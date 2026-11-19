// The Weishaupt program card: the week grid of one weekly program on a dashboard, read from the program's sensor
// (an entity, so every user who sees the dashboard can read it; the panel's commands are for administrators).
// Administrators can edit the days of a program proven writable (owner's choice C2), through the program-day text
// entities and their `text.set_value` action: the same writer, guard, hourly limit and read-back as everywhere else.
// Uses only Home Assistant's card contract (setConfig, hass, getCardSize, getStubConfig, getConfigElement) and its
// theme variables, no internal element.

import { LitElement, css, html, type TemplateResult } from "lit";
import "./week-grid.ts";
import {
  dayTextEntities, formatDay, isoWeekday, isProgramSensor, languageOf, parseDay, t, weekFromAttributes, WEEKDAYS,
  writeSwitch,
} from "./format.ts";
import type { Days } from "./types.ts";
import type { Hass } from "./types.ts";

export interface CardConfig {
  type: string;
  entity?: string;
  title?: string;
  today?: boolean;
}

const CARD = "weishaupt-program-card";
const EDITOR = "weishaupt-program-card-editor";

/** The program sensors in the states, those with days read first. */
function programSensors(hass: Hass): string[] {
  const read = (id: string): number => (hass.states[id].state === "unavailable" ? 1 : 0);
  return Object.keys(hass.states)
    .filter((id) => isProgramSensor(id, hass.states[id].attributes))
    .sort((a, b) => read(a) - read(b) || a.localeCompare(b));
}

export class WeishauptProgramCard extends LitElement {
  static properties = {
    hass: { attribute: false }, _config: { state: true }, _draft: { state: true }, _results: { state: true },
    _busy: { state: true },
  };

  declare hass: Hass;
  declare _config: CardConfig;
  declare _draft: Record<string, string> | undefined; // day "1" … "7" -> text being edited
  declare _results: Record<string, { text: string; error: boolean }>;
  declare _busy: boolean;

  constructor() {
    super();
    this._results = {};
    this._busy = false;
  }

  setConfig(config: CardConfig): void {
    if (!config || typeof config !== "object") throw new Error("Invalid configuration");
    this._config = { today: true, ...config };
  }

  getCardSize(): number {
    return 5;
  }

  static getStubConfig(hass: Hass): CardConfig {
    return { type: `custom:${CARD}`, entity: programSensors(hass)[0] ?? "", today: true };
  }

  static getConfigElement(): HTMLElement {
    return document.createElement(EDITOR);
  }

  render(): TemplateResult {
    const lang = languageOf(this.hass?.language);
    const config = this._config ?? { type: CARD };
    const entity = config.entity;
    const state = entity ? this.hass?.states[entity] : undefined;
    const title = config.title || (state?.attributes.friendly_name as string | undefined) || t(lang, "card_name");
    let body: TemplateResult;
    if (!entity) body = html`<p class="message">${t(lang, "card_no_entity")}</p>`;
    else if (!state) body = html`<p class="message">${t(lang, "card_missing", { entity })}</p>`;
    else if (state.state === "unavailable") body = html`<p class="message">${t(lang, "card_unavailable", { entity })}</p>`;
    else {
      const week = weekFromAttributes(state.attributes);
      const texts = this.hass.user?.is_admin ? dayTextEntities(this.hass.entities, entity) : null;
      body = this._draft && texts
        ? this._editor(week, texts, lang)
        : html`<weishaupt-week-grid
              .days=${week}
              language=${lang}
              unread=${t(lang, "card_unread")}
              caption=${title}
              today=${config.today === false ? 0 : isoWeekday(new Date())}
            ></weishaupt-week-grid>
            ${texts
              ? html`<div class="actions">
                  <button class="link" @click=${() => this._start(week)}>${t(lang, "card_edit")}</button>
                </div>`
              : null}
            ${this._resultLines()}`;
    }
    return html`<div class="card"><h2>${title}</h2>${body}</div>`;
  }

  // ---- editing (administrators; the program-day text entities do the writing) -----------------------------------

  private _current(week: Days, day: string): string | null {
    const ranges = week[day];
    return ranges ? formatDay(ranges.map(([a, b]) => [minutes(a), minutes(b)])) : null;
  }

  private _start(week: Days): void {
    const draft: Record<string, string> = {};
    for (let day = 1; day <= 7; day++) draft[String(day)] = this._current(week, String(day)) ?? "";
    this._draft = draft;
    this._results = {};
  }

  private _changed(week: Days): string[] {
    const draft = this._draft ?? {};
    return Object.keys(draft).filter((day) => {
      const current = this._current(week, day);
      if (current === null && draft[day].trim() === "") return false;
      const parsed = parseDay(draft[day]);
      return ("ranges" in parsed ? formatDay(parsed.ranges) : draft[day]) !== current;
    });
  }

  private _copy(from: string, target: string): void {
    const text = this._draft![from];
    const days = target === "all" ? ["1", "2", "3", "4", "5", "6", "7"]
      : target === "weekdays" ? ["1", "2", "3", "4", "5"] : ["6", "7"];
    const next = { ...this._draft! };
    for (const day of days) next[day] = text;
    this._draft = next;
  }

  private async _write(week: Days, texts: Record<string, string>): Promise<void> {
    const lang = languageOf(this.hass.language);
    const names = WEEKDAYS[lang] ?? WEEKDAYS.en;
    this._busy = true;
    const results: Record<string, { text: string; error: boolean }> = {};
    for (const day of this._changed(week)) {
      const name = names[Number(day) - 1];
      this._results = { ...results, [day]: { text: t(lang, "card_writing_day", { day: name }), error: false } };
      try {
        await this.hass.callService!("text", "set_value", { value: this._draft![day] }, { entity_id: texts[day] });
        results[day] = { text: t(lang, "card_written_day", { day: name }), error: false };
      } catch (err) {
        results[day] = { text: t(lang, "card_failed_day", { day: name, message: (err as Error).message ?? "" }),
          error: true };
      }
    }
    this._results = results;
    this._busy = false;
    if (!Object.values(results).some((r) => r.error)) this._draft = undefined;
  }

  private _resultLines(): TemplateResult | null {
    const lines = Object.values(this._results);
    return lines.length
      ? html`<div class="results" role="status">
          ${lines.map((r) => html`<div class=${r.error ? "error" : "secondary"}>${r.text}</div>`)}
        </div>`
      : null;
  }

  private _editor(week: Days, texts: Record<string, string>, lang: string): TemplateResult {
    const names = WEEKDAYS[lang] ?? WEEKDAYS.en;
    const draft = this._draft!;
    const changed = this._changed(week);
    const errors = Object.fromEntries(Object.entries(draft).map(([day, text]) => {
      const parsed = parseDay(text);
      return [day, "error" in parsed ? parsed.error : null];
    }));
    const invalid = Object.values(errors).some(Boolean);
    const writes = writeSwitch(this.hass.entities, this.hass.states);
    return html`<p class="secondary">${t(lang, "card_type_hint")}</p>
      ${names.map((name, i) => {
        const day = String(i + 1);
        return html`<div class=${changed.includes(day) ? "day changed" : "day"}>
          <label for="d${day}">${name}</label>
          <input id="d${day}" type="text" .value=${draft[day]} aria-invalid=${errors[day] ? "true" : "false"}
            placeholder=${week[day] == null ? t(lang, "card_unread") : ""}
            @input=${(e: Event) => (this._draft = { ...draft, [day]: (e.target as HTMLInputElement).value })} />
          <select aria-label=${t(lang, "copy_to")} @change=${(e: Event) => {
            const select = e.target as HTMLSelectElement;
            if (select.value) this._copy(day, select.value);
            select.value = "";
          }}>
            <option value="">${t(lang, "copy_to")}…</option>
            <option value="all">${lang === "fr" ? "tous les jours" : "every day"}</option>
            <option value="weekdays">${lang === "fr" ? "lundi – vendredi" : "Monday – Friday"}</option>
            <option value="weekend">${lang === "fr" ? "samedi, dimanche" : "Saturday, Sunday"}</option>
          </select>
          ${errors[day] ? html`<div class="error" role="alert">${t(lang, errors[day]!)}</div>` : null}
          ${this._results[day]
            ? html`<div class=${this._results[day].error ? "error" : "secondary"}>${this._results[day].text}</div>`
            : null}
        </div>`;
      })}
      ${writes
        ? html`<p class="secondary">
              ${t(lang, changed.length === 1 ? "cost_one" : "cost", {
                days: changed.length, writes: changed.length * 3, used: writes.used ?? "?", max: writes.max ?? "?",
              })}
            </p>
            ${writes.on ? null : html`<p class="error">${t(lang, "switch_off_hint")}</p>`}`
        : html`<p class="error">${t(lang, "card_no_switch")}</p>`}
      <div class="actions">
        <button class="link" ?disabled=${this._busy} @click=${() => { this._draft = undefined; this._results = {}; }}>
          ${t(lang, "discard")}
        </button>
        <button class="primary" ?disabled=${this._busy || invalid || !changed.length}
          @click=${() => this._write(week, texts)}>${t(lang, "write_days")}</button>
      </div>`;
  }

  static styles = css`
    .card {
      background: var(--ha-card-background, var(--card-background-color));
      color: var(--primary-text-color);
      border-radius: var(--ha-card-border-radius, 12px);
      border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color));
      box-shadow: var(--ha-card-box-shadow, none);
      padding: 12px 16px 16px;
    }
    h2 {
      font-size: var(--ha-card-header-font-size, 20px);
      font-weight: 400;
      margin: 0 0 8px;
    }
    .message,
    .secondary {
      color: var(--secondary-text-color);
      margin: 0;
    }
    .secondary {
      font-size: 0.9em;
    }
    .error {
      color: var(--error-color);
      font-size: 0.9em;
    }
    .day {
      display: grid;
      grid-template-columns: 6.5em minmax(0, 1fr) auto;
      gap: 4px 8px;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    .day .error,
    .day .secondary {
      grid-column: 2 / -1;
    }
    .day.changed label {
      color: var(--primary-color);
      font-weight: 500;
    }
    input,
    select {
      font: inherit;
      padding: 4px 6px;
      min-width: 0;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    input[aria-invalid="true"] {
      border-color: var(--error-color);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
    .results {
      margin-top: 8px;
    }
    button {
      font: inherit;
      cursor: pointer;
    }
    button.link {
      border: 1px solid var(--divider-color);
      background: none;
      border-radius: 6px;
      padding: 2px 10px;
      color: var(--primary-color);
    }
    button.primary {
      border: 0;
      border-radius: 6px;
      padding: 4px 12px;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    button:disabled {
      opacity: 0.5;
      cursor: default;
    }
  `;
}

/** "06:30" -> minutes since midnight. */
function minutes(time: string): number {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + (m || 0);
}

/** The card's visual editor: native elements only (no internal element of Home Assistant). */
export class WeishauptProgramCardEditor extends LitElement {
  static properties = { hass: { attribute: false }, _config: { state: true } };

  declare hass: Hass;
  declare _config: CardConfig;

  setConfig(config: CardConfig): void {
    this._config = config;
  }

  private _change(changes: Partial<CardConfig>): void {
    this._config = { ...this._config, ...changes };
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
  }

  render(): TemplateResult {
    const lang = languageOf(this.hass?.language);
    const sensors = this.hass ? programSensors(this.hass) : [];
    const config = this._config ?? { type: `custom:${CARD}` };
    return html`<div class="editor">
      <label
        >${t(lang, "card_editor_entity")}
        <select @change=${(e: Event) => this._change({ entity: (e.target as HTMLSelectElement).value })}>
          <option value="" ?selected=${!config.entity}>…</option>
          ${sensors.map((id) => html`<option value=${id} ?selected=${id === config.entity}>
            ${(this.hass.states[id].attributes.friendly_name as string | undefined) ?? id}
          </option>`)}
        </select>
      </label>
      <p class="hint">${t(lang, "card_editor_hint")}</p>
      <label
        >${t(lang, "card_editor_title")}
        <input type="text" .value=${config.title ?? ""}
          @input=${(e: Event) => this._change({ title: (e.target as HTMLInputElement).value || undefined })} />
      </label>
      <label class="check"
        ><input type="checkbox" .checked=${config.today !== false}
          @change=${(e: Event) => this._change({ today: (e.target as HTMLInputElement).checked })} />
        ${t(lang, "card_editor_today")}</label
      >
    </div>`;
  }

  static styles = css`
    .editor {
      display: grid;
      gap: 12px;
    }
    label {
      display: grid;
      gap: 4px;
      color: var(--secondary-text-color);
    }
    .hint {
      margin: -6px 0 0;
      font-size: 0.85em;
      color: var(--secondary-text-color);
    }
    label.check {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    select,
    input[type="text"] {
      font: inherit;
      padding: 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
  `;
}

if (!customElements.get(CARD)) customElements.define(CARD, WeishauptProgramCard);
if (!customElements.get(EDITOR)) customElements.define(EDITOR, WeishauptProgramCardEditor);

// listed in the dashboard's card picker
const known = window as unknown as { customCards?: { type: string; name: string; description: string }[] };
known.customCards = known.customCards ?? [];
if (!known.customCards.some((c) => c.type === CARD)) {
  const lang = languageOf(navigator.language);
  known.customCards.push({ type: CARD, name: t(lang, "card_name"), description: t(lang, "card_description") });
}
