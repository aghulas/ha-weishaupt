// The Weishaupt program card: the week grid of one weekly program on a dashboard, read from the program's sensor
// (an entity, so every user who sees the dashboard can read it; the panel's commands are for administrators).
// Read only in this version; editing waits on the owner's choices (section 11 of the design).
// Uses only Home Assistant's card contract (setConfig, hass, getCardSize, getStubConfig, getConfigElement) and its
// theme variables, no internal element.

import { LitElement, css, html, type TemplateResult } from "lit";
import "./week-grid.ts";
import { isoWeekday, isProgramSensor, languageOf, t, weekFromAttributes } from "./format.ts";
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
  static properties = { hass: { attribute: false }, _config: { state: true } };

  declare hass: Hass;
  declare _config: CardConfig;

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
      body = html`<weishaupt-week-grid
        .days=${weekFromAttributes(state.attributes)}
        language=${lang}
        unread=${t(lang, "card_unread")}
        caption=${title}
        today=${config.today === false ? 0 : isoWeekday(new Date())}
      ></weishaupt-week-grid>`;
    }
    return html`<div class="card"><h2>${title}</h2>${body}</div>`;
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
    .message {
      color: var(--secondary-text-color);
      margin: 0;
    }
  `;
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
