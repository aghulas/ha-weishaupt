// The Weishaupt panel: read only, for administrators. Device tree and menus on the left; on the right the table of
// the selected menu, the week grid of the programs, or the definitions in use. Data from the WebSocket commands of
// the integration (panel.py); a change is made in the entity a row links to (Home Assistant's own dialog).
// Uses only the custom-panel contract (hass, narrow) and Home Assistant's theme variables, no internal element.

import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import {
  bars,
  formatAge,
  formatRange,
  formatValue,
  label,
  languageOf,
  menuTree,
  missingReason,
  notUsable,
  readingOf,
  redundant,
  t,
  WEEKDAYS,
} from "./format.ts";
import type { Days, Device, Hass, Installation, LiveEvent, Reading, Row, Tree } from "./types.ts";

const DEFINITIONS = "__definitions__";

/** Whether `menu` is under `ancestor` in the menus of a device. */
function descends(menus: { id: string; parent: string }[], menu: string, ancestor: string): boolean {
  let parent = menus.find((m) => m.id === menu)?.parent ?? "";
  while (parent) {
    if (parent === ancestor) return true;
    parent = menus.find((m) => m.id === parent)?.parent ?? "";
  }
  return false;
}
const PROGRAMS = "programs";

export class WeishauptPanel extends LitElement {
  static properties = {
    hass: { attribute: false },
    narrow: { type: Boolean },
    _installations: { state: true },
    _entryId: { state: true },
    _tree: { state: true },
    _readings: { state: true },
    _programs: { state: true },
    _available: { state: true },
    _device: { state: true },
    _menu: { state: true },
    _error: { state: true },
    _tick: { state: true },
    _queued: { state: true },
    _reloading: { state: true },
  };

  declare hass: Hass;
  declare narrow: boolean;
  declare _installations: Installation[] | undefined;
  declare _entryId: string | undefined;
  declare _tree: Tree | undefined;
  declare _readings: Record<string, Reading | null>;
  declare _programs: Record<string, Days>;
  declare _available: boolean;
  declare _device: string | undefined;
  declare _menu: string | undefined;
  declare _error: string | undefined;
  declare _tick: number;
  declare _queued: Record<string, number>;
  declare _reloading: boolean;

  private _unsubscribe?: () => void;
  private _offset = 0; // browser clock minus Home Assistant's clock, in seconds
  private _timer?: number;
  private _loading?: string;

  constructor() {
    super();
    this._readings = {};
    this._programs = {};
    this._available = true;
    this._tick = 0;
    this._queued = {};
    this._reloading = false;
  }

  private get _lang(): string {
    return languageOf(this.hass?.language);
  }

  connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => (this._tick += 1), 30000); // ages move on
    if (this._entryId) void this._subscribe(this._entryId);
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    window.clearInterval(this._timer);
    this._unsubscribe?.();
    this._unsubscribe = undefined;
  }

  protected willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass && this._installations === undefined && !this._loading) {
      this._loading = "installations";
      this.hass
        .callWS<Installation[]>({ type: "weishaupt/panel/installations" })
        .then((found) => {
          this._installations = found;
          if (found.length) void this._select(found[0].entry_id);
        })
        .catch((err: Error) => (this._error = err.message));
    }
  }

  private async _select(entryId: string, again = false): Promise<void> {
    this._entryId = entryId;
    if (!again) {
      this._tree = undefined;
      this._device = undefined;
      this._menu = undefined;
    }
    this._readings = {};
    this._programs = {};
    this._queued = {};
    try {
      const tree = await this.hass.callWS<Tree>({ type: "weishaupt/panel/tree", entry_id: entryId });
      this._tree = tree;
      // after a reload, stay on the device and menu shown
      if (!tree.devices.some((d) => d.id === this._device)) {
        this._device = tree.devices[0]?.id;
        this._menu = tree.devices[0]?.menus[0]?.id;
      }
      await this._subscribe(entryId);
    } catch (err) {
      if (again) throw err;
      this._error = (err as Error).message;
    }
  }

  private async _readProgram(key: string): Promise<void> {
    if (!this._entryId) return;
    const answer = await this.hass.callWS<{ queued: number; seconds: number }>({
      type: "weishaupt/panel/read_program",
      entry_id: this._entryId,
      program: key,
    });
    this._queued = { ...this._queued, [key]: answer.queued };
  }

  private async _subscribe(entryId: string): Promise<void> {
    this._unsubscribe?.();
    this._unsubscribe = await this.hass.connection.subscribeMessage<LiveEvent>((event) => this._live(event), {
      type: "weishaupt/panel/subscribe",
      entry_id: entryId,
    });
  }

  private _live(event: LiveEvent): void {
    this._offset = Date.now() / 1000 - event.now;
    if (event.reloaded) {
      // the entry unloaded (a reload): ask the new one for its tree and readings, once it is loaded again
      this._unsubscribe = undefined;
      this._reloading = true;
      const retry = (left: number): void => {
        window.setTimeout(() => {
          if (!this._entryId || !this.isConnected) return;
          this._select(this._entryId, true).then(
            () => (this._reloading = false),
            () => (left > 0 ? retry(left - 1) : (this._error = t(this._lang, "reloading"))),
          );
        }, 2000);
      };
      retry(15);
      return;
    }
    if (event.available !== undefined) this._available = event.available;
    if (event.readings) this._readings = { ...this._readings, ...event.readings };
    if (event.programs) this._programs = { ...this._programs, ...event.programs };
  }

  private _open(entityId: string): void {
    // Home Assistant's own more-info dialog of the entity: where a change is made
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }

  private _age(reading: Reading): string {
    return formatAge(Date.now() / 1000 - this._offset - reading.when, this._lang);
  }

  // ---- rendering --------------------------------------------------------------------------------------------

  render(): TemplateResult {
    const lang = this._lang;
    if (this._error) return html`<div class="message error" role="alert">${this._error}</div>`;
    if (this._installations === undefined) return html`<div class="message">${t(lang, "loading")}</div>`;
    if (!this._installations.length) return html`<div class="message">${t(lang, "no_installation")}</div>`;
    return html`
      <header>
        <h1>${t(lang, "title")}</h1>
        ${this._installations.length > 1
          ? html`<label
              >${t(lang, "installation")}
              <select @change=${(e: Event) => this._select((e.target as HTMLSelectElement).value)}>
                ${this._installations.map(
                  (i) => html`<option value=${i.entry_id} ?selected=${i.entry_id === this._entryId}>${i.title}</option>`,
                )}
              </select></label
            >`
          : nothing}
        ${this._clock()}
      </header>
      ${this._available ? nothing : html`<div class="message warning" role="status">${t(lang, "unavailable")}</div>`}
      ${this._reloading ? html`<div class="message" role="status">${t(lang, "reloading")}</div>` : nothing}
      ${this._tree ? this._body(this._tree) : html`<div class="message">${t(lang, "loading")}</div>`}
    `;
  }

  private _clock(): TemplateResult | typeof nothing {
    const id = this._tree?.clock.entity_id;
    const state = id ? this.hass.states[id] : undefined;
    if (!id || !state || Number.isNaN(Number(state.state))) return nothing;
    const lang = this._lang;
    const offset = Math.round(Number(state.state));
    const text =
      offset === 0
        ? t(lang, "clock_on_time")
        : t(lang, offset > 0 ? "clock_ahead" : "clock_behind", { n: Math.abs(offset) });
    return html`<button class="clock link" @click=${() => this._open(id)}>
      ${t(lang, "clock_line", { label: t(lang, "clock_offset"), text })}
    </button>`;
  }

  private _body(tree: Tree): TemplateResult {
    const device = tree.devices.find((d) => d.id === this._device);
    return html`<div class=${this.narrow ? "layout narrow" : "layout"}>
      <nav aria-label=${t(this._lang, "devices")}>${this._nav(tree)}</nav>
      <main>${this._menu === DEFINITIONS ? this._definitions(tree) : device ? this._device_view(device) : nothing}</main>
    </div>`;
  }

  private _nav(tree: Tree): TemplateResult {
    const lang = this._lang;
    if (this.narrow) {
      // a phone: one list to choose from, so that the table is not pushed below the whole tree
      const current = `${this._device ?? ""}|${this._menu ?? ""}`;
      return html`<label class="choose"
        >${t(lang, "devices")}
        <select
          @change=${(e: Event) => {
            const [device, menu] = (e.target as HTMLSelectElement).value.split("|");
            this._device = device;
            this._menu = menu;
          }}
        >
          ${tree.devices.map(
            (device) => html`<optgroup label=${label(device.label, lang)}>
              ${menuTree(device.menus).map(
                ([menu, depth]) =>
                  html`<option value=${`${device.id}|${menu.id}`} ?selected=${current === `${device.id}|${menu.id}`}>
                    ${"\u00a0\u00a0".repeat(depth)}${label(menu.label, lang)}
                  </option>`,
              )}
            </optgroup>`,
          )}
          <option value=${`${this._device ?? ""}|${DEFINITIONS}`} ?selected=${this._menu === DEFINITIONS}>
            ${t(lang, "definitions")}
          </option>
        </select></label
      >`;
    }
    const item = (device: string, menu: string, text: string, depth: number): TemplateResult => {
      const current = this._device === device && this._menu === menu;
      return html`<li>
        <button
          class="menu depth${depth}"
          aria-current=${current ? "page" : "false"}
          @click=${() => {
            this._device = device;
            this._menu = menu;
          }}
        >
          ${text}
        </button>
      </li>`;
    };
    return html`<ul>
      ${tree.devices.map(
        (device) => html`<li>
          <span class="device">${label(device.label, lang)}</span>
          <ul>
            ${menuTree(device.menus).map(([menu, depth]) => item(device.id, menu.id, label(menu.label, lang), depth))}
          </ul>
        </li>`,
      )}
      ${item(this._device ?? "", DEFINITIONS, t(lang, "definitions"), 0)}
    </ul>`;
  }

  private _device_view(device: Device): TemplateResult {
    const lang = this._lang;
    const menu = device.menus.find((m) => m.id === this._menu);
    const info = [
      device.addresses.length ? `${t(lang, "address")} ${device.addresses.join(", ")}` : "",
      device.software ? `${t(lang, "software")} ${device.software}` : "",
      device.hardware ? `${t(lang, "hardware")} ${device.hardware}` : "",
    ].filter(Boolean);
    // a menu shows its own rows, then those of its sub-menus under their names
    const sections = menuTree(device.menus)
      .filter(([m]) => m.id === this._menu || descends(device.menus, m.id, this._menu ?? ""))
      .map(([m]) => [m, device.rows.filter((row) => row.menu === m.id)] as const)
      .filter(([, rows]) => rows.length);
    return html`<h2>${label(device.label, lang)}${menu ? html` — ${label(menu.label, lang)}` : nothing}</h2>
      ${info.length ? html`<p class="secondary">${info.join(" · ")}</p>` : nothing}
      ${this._menu === PROGRAMS ? this._programs_view(device) : nothing}
      ${sections.length ? html`<p class="secondary">${t(lang, "write_hint")}</p>` : nothing}
      ${sections.map(
        ([m, rows]) => html`${m.id !== this._menu ? html`<h3>${label(m.label, lang)}</h3>` : nothing}${this._table(rows)}`,
      )}`;
  }

  private _table(rows: Row[]): TemplateResult {
    const lang = this._lang;
    void this._tick;
    return html`<div class="scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">${t(lang, "name")}</th>
              <th scope="col">${t(lang, "value")}</th>
              <th scope="col">${t(lang, "age")}</th>
              <th scope="col">${t(lang, "range")}</th>
              <th scope="col">${t(lang, "write")}</th>
              <th scope="col">${t(lang, "entity")}</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map((row) => {
              const reading = readingOf(row, this._readings);
              const value = formatValue(row, reading, lang);
              const description = redundant(label(row.description, lang), label(row.label, lang))
                ? ""
                : label(row.description, lang);
              return html`<tr>
                <th scope="row">
                  ${label(row.label, lang)}
                  ${description ? html`<div class="description">${description}</div>` : nothing}
                </th>
                <td class="nowrap">${value ?? html`<span class="secondary">${t(lang, missingReason(row))}</span>`}</td>
                <td class="secondary nowrap">
                  ${reading ? this._age(reading) : ""}${reading?.kept
                    ? html`<div class="kept">${t(lang, "kept")}</div>`
                    : nothing}${row.passive ? html`<div>${t(lang, "passive")}</div>` : nothing}
                </td>
                <td class="nowrap">${formatRange(row)}</td>
                <td>
                  ${row.writable
                    ? html`<span class="badge ${row.writable.risk}">${t(lang, row.writable.risk)}</span>${row.writable
                          .through
                        ? html`<div class="secondary">${t(lang, "through", { circuit: row.writable.through })}</div>`
                        : nothing}`
                    : html`<span class="secondary">${t(lang, "read_only")}</span>`}
                </td>
                <td>
                  ${row.entity_id
                    ? html`<button class="link" @click=${() => this._open(row.entity_id!)}>${t(lang, "open")}</button>`
                    : nothing}
                </td>
              </tr>`;
            })}
          </tbody>
        </table>
      </div>`;
  }

  private _programs_view(device: Device): TemplateResult {
    const lang = this._lang;
    const days = WEEKDAYS[lang] ?? WEEKDAYS.en;
    return html`${device.programs.map((program) => {
      const week = this._programs[program.key];
      const note = !program.read
        ? t(lang, "not_read_program")
        : !program.listened
          ? t(lang, "program_not_listened")
          : program.writable
          ? t(lang, "editable")
          : t(lang, "not_editable");
      return html`<section class="program">
        <h3>
          ${label(program.label, lang)}
          ${program.entity_id
            ? html`<button class="link" @click=${() => this._open(program.entity_id!)}>${t(lang, "open")}</button>`
            : nothing}
        </h3>
        <p class="secondary">${note}</p>
        ${program.read && !program.listened
          ? this._queued[program.key] !== undefined
            ? html`<p class="secondary" role="status">${t(lang, "read_queued", { n: this._queued[program.key] })}</p>`
            : html`<p>
                <button class="link" @click=${() => this._readProgram(program.key)}>${t(lang, "read_now")}</button>
                <span class="secondary"
                  >${t(lang, "read_cost", { n: program.slots, s: Math.round(program.slots * 2.2) })}</span
                >
              </p>`
          : nothing}
        <table class="week">
          <caption class="visually-hidden">${label(program.label, lang)}</caption>
          <thead>
            <tr>
              <th scope="col"><span class="visually-hidden">${t(lang, "programs")}</span></th>
              <td class="scale" aria-hidden="true">
                ${[0, 6, 12, 18, 24].map((h) => html`<span style="left:${(h / 24) * 100}%">${h}</span>`)}
              </td>
            </tr>
          </thead>
          <tbody>
            ${days.map((name, i) => {
              const ranges = week?.[String(i + 1)];
              const text =
                ranges === undefined || ranges === null
                  ? t(lang, program.listened ? "day_unread" : "not_listened")
                  : ranges.length
                    ? ranges.map(([from, to]) => `${from}-${to}`).join(", ")
                    : t(lang, "day_none");
              return html`<tr>
                <th scope="row">${name}</th>
                <td>
                  <div class="day" aria-hidden="true">
                    ${(ranges ?? []).length
                      ? bars(ranges!).map(
                          (bar) => html`<span class="bar" style="left:${bar.left}%;width:${bar.width}%"></span>`,
                        )
                      : nothing}
                  </div>
                  <div class="day-text">${text}</div>
                </td>
              </tr>`;
            })}
          </tbody>
        </table>
      </section>`;
    })}`;
  }

  private _definitions(tree: Tree): TemplateResult {
    const lang = this._lang;
    const d = tree.definitions;
    const list = (items: string[]): TemplateResult =>
      items.length ? html`<ul>${items.map((i) => html`<li><code>${i}</code></li>`)}</ul>` : html`${t(lang, "none")}`;
    const writes = tree.writes;
    return html`<h2>${t(lang, "definitions")}</h2>
      <dl>
        <dt>${t(lang, "in_use")}</dt>
        <dd>
          ${d.version}${d.commit ? html` <code>${d.commit.slice(0, 7)}</code>` : nothing} —
          ${d.source === "bundled" ? t(lang, "source_bundled") : t(lang, "source_file", { file: d.source })}
        </dd>
        <dt>${t(lang, "messages")}</dt>
        <dd>
          ${t(lang, "readable", {
            usable: d.usable,
            readable: d.usable + d.not_usable.filter((m) => m.reason === "mismatch" || m.reason === "other").length,
          })}
        </dd>
        <dt>${t(lang, "not_usable")}</dt>
        <dd>${list(notUsable(d.not_usable, lang))}</dd>
        <dt>${t(lang, "refused")}</dt>
        <dd>${list(Object.entries(d.refused).map(([file, why]) => `${file}: ${why}`))}</dd>
        <dt>${t(lang, "mismatches")}</dt>
        <dd>${list(d.mismatches.map((m) => `${m.key}: ${m.reason}${m.detail ? ` (${m.detail})` : ""}`))}</dd>
        <dt>${t(lang, "named_from_metadata")}</dt>
        <dd>
          ${list(d.named_from_metadata.map((e) => (e.disabled ? `${e.entity_id} (${t(lang, "disabled")})` : e.entity_id)))}
        </dd>
        <dt>${t(lang, "not_named")}</dt>
        <dd>${list(d.not_named)}</dd>
        <dt>${t(lang, "ebusd")}</dt>
        <dd>${tree.ebusd.version ?? "?"}${tree.ebusd.own_address ? ` (${tree.ebusd.own_address})` : ""}</dd>
        <dt>${t(lang, "unknown_addresses")}</dt>
        <dd>${list(tree.unknown_addresses)}</dd>
        <dt>${t(lang, "writes")}</dt>
        <dd>
          ${writes
            ? html`${t(lang, writes.switch ? "switch_on" : "switch_off")} ·
              ${t(lang, "capability", { value: writes.capability })} ·
              ${t(lang, "per_hour", { n: writes.writes_last_hour, max: writes.max_per_hour })}`
            : t(lang, "writes_off")}
        </dd>
      </dl>`;
  }

  static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
    header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 24px;
      padding: 12px 16px;
      background: var(--app-header-background-color, var(--card-background-color));
      color: var(--app-header-text-color, var(--primary-text-color));
      border-bottom: 1px solid var(--divider-color);
    }
    h1 {
      font-size: 20px;
      font-weight: 400;
      margin: 0;
    }
    h2 {
      font-size: 18px;
      font-weight: 500;
      margin: 0 0 8px;
    }
    h3 {
      font-size: 16px;
      font-weight: 500;
      margin: 16px 0 4px;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(200px, 260px) 1fr;
      gap: 16px;
      padding: 16px;
    }
    .layout.narrow {
      grid-template-columns: 1fr;
    }
    nav,
    main {
      background: var(--card-background-color);
      border-radius: var(--ha-card-border-radius, 12px);
      border: 1px solid var(--divider-color);
      padding: 12px;
      min-width: 0;
    }
    nav ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    label.choose {
      display: flex;
      flex-direction: column;
      gap: 4px;
      color: var(--secondary-text-color);
    }
    select {
      font: inherit;
      padding: 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    .device {
      display: block;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    button {
      font: inherit;
      color: inherit;
    }
    button.menu {
      display: block;
      width: 100%;
      text-align: start;
      border: 0;
      background: none;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
    }
    button.menu.depth1 {
      padding-inline-start: 24px;
    }
    button.menu.depth2 {
      padding-inline-start: 40px;
    }
    button.menu[aria-current="page"] {
      background: var(--secondary-background-color);
      color: var(--primary-color);
      font-weight: 500;
    }
    button:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    button.link {
      border: 1px solid var(--divider-color);
      background: none;
      border-radius: 6px;
      padding: 2px 8px;
      cursor: pointer;
      color: var(--primary-color);
    }
    .nowrap {
      white-space: nowrap;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      text-align: start;
      vertical-align: top;
      padding: 6px 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    thead th {
      font-weight: 500;
      color: var(--secondary-text-color);
    }
    tbody th {
      font-weight: 400;
      min-width: 12em;
    }
    .description,
    .secondary {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .kept {
      font-style: italic;
    }
    .badge {
      white-space: nowrap;
      border-radius: 10px;
      padding: 1px 8px;
      border: 1px solid currentColor;
    }
    .badge.comfort {
      color: var(--success-color, var(--primary-color));
    }
    .badge.regulation {
      color: var(--warning-color, var(--primary-color));
    }
    .message {
      padding: 16px;
    }
    .message.error {
      color: var(--error-color);
    }
    .message.warning {
      color: var(--warning-color);
    }
    table.week th {
      width: 8em;
    }
    .scale {
      position: relative;
      height: 1.4em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .day {
      position: relative;
      height: 14px;
      background: var(--secondary-background-color);
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    dl {
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 6px 16px;
    }
    dt {
      color: var(--secondary-text-color);
    }
    dd {
      margin: 0;
    }
    dd ul {
      margin: 0;
      padding-inline-start: 16px;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
    @media (max-width: 600px) {
      dl {
        grid-template-columns: 1fr;
      }
    }
  `;
}

if (!customElements.get("weishaupt-panel")) customElements.define("weishaupt-panel", WeishauptPanel);
