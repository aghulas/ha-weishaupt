// The Weishaupt panel: read only, for administrators. Device tree and menus on the left; on the right the table of
// the selected menu, the week grid of the programs, or the definitions in use. Data from the WebSocket commands of
// the integration (panel.py); a change is made in the entity a row links to (Home Assistant's own dialog).
// Uses only the custom-panel contract (hass, narrow) and Home Assistant's theme variables, no internal element.

import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import "./week-grid.ts";
import {
  bars,
  choose,
  clockText,
  dragRange,
  followPlan,
  jobText,
  priceText,
  formatAge,
  formatRange,
  formatValue,
  isoWeekday,
  label,
  languageOf,
  addDragged,
  matchesRow,
  queuedText,
  reportHtml,
  reportRows,
  toCsv,
  formatDay,
  initialDraft,
  menuTree,
  missingReason,
  parseDay,
  notUsable,
  readingOf,
  redundant,
  t,
  WEEKDAYS,
  type RowFilter,
} from "./format.ts";
import type {
  Days, Device, Estimate, FaultTable, Follow, FollowAnswer, Hass, Installation, JobProgress, LiveEvent, Program, Reading,
  Row, Tree, WriteAnswer,
} from "./types.ts";

/** A read on demand of a menu, a device or the installation: its cost first, then its job. */
interface ReadState {
  device?: string;
  menu?: string;
  price?: Estimate;
  job?: JobProgress;
  error?: string;
  reloaded?: boolean; // the entry reloaded while it ran: what was not asked was dropped
}

const ALL = "__all__";

const DEFINITIONS = "__definitions__";
const FAULTS = "__faults__";

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
    _editing: { state: true },
    _draft: { state: true },
    _rowResult: { state: true },
    _busy: { state: true },
    _dialog: { state: true },
    _weekDraft: { state: true },
    _weekResult: { state: true },
    _faults: { state: true },
    _reads: { state: true },
    _pending: { state: true },
    _followNote: { state: true },
    _hideZeroFaults: { state: true },
    _query: { state: true },
    _filter: { state: true },
    _dragPreview: { state: true },
    _dragError: { state: true },
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
  declare _queued: Record<string, Estimate>;
  declare _reloading: boolean;
  declare _editing: string | undefined; // key of the row being changed
  declare _draft: string;
  declare _rowResult: Record<string, { text: string; error: boolean }>;
  declare _busy: boolean;
  declare _dialog: { answer: WriteAnswer; target: string } | undefined; // a confirmation asked by the writer
  declare _weekDraft: Record<string, Record<string, string>>; // program -> day -> text being edited
  declare _weekResult: Record<string, { text: string; error: boolean }>;
  declare _faults: FaultTable[] | undefined;
  declare _reads: Record<string, ReadState>; // scope (ALL, device, device|menu) -> its read on demand
  declare _pending: Record<string, boolean>; // entity id -> followed or not, chosen and not applied yet
  declare _followNote: { text: string; error: boolean } | undefined;
  declare _hideZeroFaults: boolean;
  declare _query: string;
  declare _filter: RowFilter;
  declare _dragPreview: { program: string; day: string; start: number; end: number } | undefined;
  declare _dragError: Record<string, string>; // `${program}|${day}` -> i18n error key
  private _faultTimer?: number;
  private _drag?: { program: string; day: string; from: number; element: HTMLElement };

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
    this._draft = "";
    this._rowResult = {};
    this._busy = false;
    this._weekDraft = {};
    this._weekResult = {};
    this._reads = {};
    this._pending = {};
    this._hideZeroFaults = true;
    this._query = "";
    this._filter = "all";
    this._dragError = {};
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

  protected updated(changed: PropertyValues): void {
    if (changed.has("_dialog") && this._dialog) {
      this.renderRoot.querySelector<HTMLButtonElement>(".dialog button.cancel")?.focus();
    } else if (changed.has("_editing") && this._editing) {
      this.renderRoot.querySelector<HTMLElement>("form.edit input, form.edit select")?.focus();
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
      this._loadFaults(0);
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

  /** The fault tables, again shortly after one of their messages was read (several arrive together). */
  private _loadFaults(delay: number): void {
    window.clearTimeout(this._faultTimer);
    this._faultTimer = window.setTimeout(async () => {
      if (!this._entryId) return;
      try {
        this._faults = await this.hass.callWS<FaultTable[]>({ type: "weishaupt/panel/faults", entry_id: this._entryId });
      } catch {
        // the tables stay as they were; the next reading asks again
      }
    }, delay);
  }

  private async _readFaults(device: string): Promise<void> {
    const answer = await this.hass.callWS<Estimate>({
      type: "weishaupt/panel/read_faults",
      entry_id: this._entryId,
      device,
    });
    this._queued = { ...this._queued, [`faults:${device}`]: answer };
  }

  private _report(): void {
    const tree = this._tree!;
    const lang = this._lang;
    const rows = reportRows(tree, this._readings, lang);
    const date = new Date().toLocaleString(lang === "fr" ? "fr-FR" : "en-GB");
    const page = reportHtml(rows, lang, {
      title: t(lang, "report_title"),
      subtitle: t(lang, "report_subtitle", { date, version: tree.definitions.version }),
    });
    const view = window.open("", "_blank");
    if (!view) {
      this._rowResult = { ...this._rowResult, __report__: { text: t(lang, "report_blocked"), error: true } };
      return;
    }
    view.document.open();
    view.document.write(page);
    view.document.close();
    view.focus();
    view.print();
  }

  private _csv(): void {
    const tree = this._tree!;
    const lang = this._lang;
    const blob = new Blob([toCsv(reportRows(tree, this._readings, lang), lang)], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `weishaupt-settings-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  private _faultsView(table: FaultTable): TemplateResult {
    const lang = this._lang;
    const queued = this._queued[`faults:${table.device}`];
    const value = (v: unknown): string => (v === null || v === undefined ? "-" : String(v));
    return html`<h2>${label(table.label, lang)} — ${t(lang, "faults")}</h2>
      ${table.not_listened
        ? html`<p class="secondary">${t(lang, "faults_unread", { n: table.not_listened })}</p>
            ${queued !== undefined
              ? html`<p class="secondary" role="status">${queuedText(queued, lang)}</p>`
              : table.to_read === 0 || table.unread === 0
                ? html`<p class="secondary">${t(lang, "faults_read_once")}</p>`
                : html`<p>
                    <button class="link" @click=${() => this._readFaults(table.device)}>${t(lang, "read_now")}</button>
                    <span class="secondary"
                      >${t(lang, "read_cost", { n: table.to_read, s: Math.round(table.to_read * 2.2) })}</span
                    >
                  </p>`}`
        : nothing}
      ${table.history
        ? html`<h3>${t(lang, "fault_history")}</h3>
            ${table.history.entries === null
              ? html`<p class="secondary">${t(lang, "day_unread")}</p>`
              : table.history.entries.length === 0
                ? html`<p class="secondary">${t(lang, "fault_none")}</p>`
                : html`${table.history.ordered ? nothing : html`<p class="secondary">${t(lang, "fault_unordered")}</p>`}
                    <div class="scroll">
                      <table>
                        <thead>
                          <tr>
                            <th scope="col">${t(lang, "fault_code")}</th>
                            <th scope="col">${t(lang, "fault_text")}</th>
                            <th scope="col">${t(lang, "fault_values")}</th>
                            <th scope="col">${t(lang, "fault_slot")}</th>
                          </tr>
                        </thead>
                        <tbody>
                          ${table.history.entries.map(
                            (e) => html`<tr>
                              <th scope="row" class="nowrap">${e.code}</th>
                              <td>${label(e.text, lang) || "-"}</td>
                              <td class="secondary">
                                ${e.values
                                  .map((v) => `${label(v.label, lang)} ${v.value_labels ? label(v.value_labels, lang)
                                    : v.value === null ? "-" : `${v.value}${v.unit ? ` ${v.unit}` : ""}`}`)
                                  .join(" · ")}
                              </td>
                              <td>${e.slot}</td>
                            </tr>`,
                          )}
                        </tbody>
                      </table>
                    </div>
                    <p class="secondary">${t(lang, "fault_no_time")}</p>`}`
        : nothing}
      ${table.counters
        ? (() => {
            const zeroCount = table.counters.filter((c) => c.count === 0).length;
            const visible = this._hideZeroFaults ? table.counters.filter((c) => c.count !== 0) : table.counters;
            return html`<h3>${t(lang, "fault_counters")}</h3>
              ${zeroCount > 0
                ? html`<label class="inline-check secondary">
                    <input
                      type="checkbox"
                      .checked=${this._hideZeroFaults}
                      @change=${(e: Event) => (this._hideZeroFaults = (e.target as HTMLInputElement).checked)}
                    />
                    ${t(lang, "fault_hide_zero", { n: zeroCount })}
                  </label>`
                : nothing}
              ${visible.length === 0
                ? html`<p class="secondary">${t(lang, "fault_all_zero")}</p>`
                : html`<div class="scroll">
                    <table>
                      <thead>
                        <tr>
                          <th scope="col">${t(lang, "fault_number")}</th>
                          <th scope="col">${t(lang, "fault_count")}</th>
                          <th scope="col">${t(lang, "fault_text")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${visible.map(
                          (c) => html`<tr>
                            <th scope="row">${c.number}</th>
                            <td class=${c.count ? "num" : "secondary num"}>
                              ${c.count === null ? t(lang, "day_unread") : c.count}
                            </td>
                            <td>${label(c.text, lang) || "-"}</td>
                          </tr>`,
                        )}
                      </tbody>
                    </table>
                  </div>`}`;
          })()
        : nothing}
      ${table.log
        ? html`<h3>${t(lang, "fault_log")}</h3>
            <p>
              ${table.log.entry
                ? t(lang, "fault_log_fields", {
                    id: value(table.log.entry.id),
                    code: value(table.log.entry.code),
                    type: value(table.log.entry.type),
                    device: value(table.log.entry.device),
                    time: value(table.log.entry.time),
                  })
                : t(lang, "day_unread")}
            </p>
            <p class="secondary">${t(lang, "fault_log_hint")}</p>`
        : nothing}`;
  }

  private async _readProgram(key: string): Promise<void> {
    if (!this._entryId) return;
    const answer = await this.hass.callWS<Estimate>({
      type: "weishaupt/panel/read_program",
      entry_id: this._entryId,
      program: key,
    });
    this._queued = { ...this._queued, [key]: answer };
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
      // reads on demand live in the hub that unloaded: what they had not asked is gone
      this._reads = Object.fromEntries(Object.entries(this._reads).map(([scope, read]) => [
        scope, read.job && !read.job.ended ? { ...read, reloaded: true } : read,
      ]));
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
    if (event.readings) {
      this._readings = { ...this._readings, ...event.readings };
      const keys = new Set((this._faults ?? []).flatMap((f) => f.keys));
      if (Object.keys(event.readings).some((k) => keys.has(k))) this._loadFaults(1000);
    }
    if (event.programs) this._programs = { ...this._programs, ...event.programs };
    if (event.jobs) {
      const jobs = event.jobs;
      this._reads = Object.fromEntries(Object.entries(this._reads).map(([scope, read]) => [
        scope, read.job && jobs[read.job.id] ? { ...read, job: jobs[read.job.id] } : read,
      ]));
    }
  }

  // ---- reads on demand: a menu, a device, the installation (reads only, at the reader's pace) -----------------

  private _scope(device?: string, menu?: string): string {
    return device ? (menu ? `${device}|${menu}` : device) : ALL;
  }

  private async _readCall(scope: string, start: boolean): Promise<void> {
    const read = this._reads[scope] ?? {};
    const message: Record<string, unknown> = { type: "weishaupt/panel/read_rows", entry_id: this._entryId, start };
    if (read.device) message.device = read.device;
    if (read.menu) message.menu = read.menu;
    try {
      const answer = await this.hass.callWS<Estimate>(message);
      this._reads = { ...this._reads, [scope]: start ? { ...read, price: undefined, job: answer.job } : { ...read, price: answer } };
    } catch (err) {
      this._reads = { ...this._reads, [scope]: { ...read, error: (err as Error).message } };
    }
  }

  private _price(device?: string, menu?: string): void {
    const scope = this._scope(device, menu);
    this._reads = { ...this._reads, [scope]: { device, menu } };
    void this._readCall(scope, false);
  }

  private async _stopRead(scope: string): Promise<void> {
    const read = this._reads[scope];
    if (!read?.job) return;
    try {
      const job = await this.hass.callWS<JobProgress>({
        type: "weishaupt/panel/stop_read", entry_id: this._entryId, job: read.job.id,
      });
      this._reads = { ...this._reads, [scope]: { ...read, job } };
    } catch (err) {
      this._reads = { ...this._reads, [scope]: { ...read, error: (err as Error).message } };
    }
  }

  private _dismissRead(scope: string): void {
    const rest = { ...this._reads };
    delete rest[scope];
    this._reads = rest;
  }

  private _readBar(device?: string, menu?: string): TemplateResult {
    const lang = this._lang;
    const scope = this._scope(device, menu);
    const read = this._reads[scope];
    const what = t(lang, device ? (menu ? "read_scope_menu" : "read_scope_device") : "read_scope_all");
    if (!read) {
      return html`<p class="read-bar"><button class="link" @click=${() => this._price(device, menu)}>${what}</button></p>`;
    }
    const close = html`<button class="link" @click=${() => this._dismissRead(scope)}>${t(lang, "dismiss")}</button>`;
    if (read.error) return html`<p class="read-bar error" role="alert">${read.error} ${close}</p>`;
    if (read.job) {
      const running = !read.job.ended && !read.reloaded;
      return html`<p class="read-bar" role="status">
        ${read.reloaded ? t(lang, "job_reload") : jobText(read.job, lang)}
        ${running && read.job.total ? html`<progress max=${read.job.total} value=${read.job.done}></progress>` : nothing}
        ${running
          ? html`<button class="link" @click=${() => this._stopRead(scope)}>${t(lang, "read_stop")}</button>`
          : close}
      </p>`;
    }
    if (!read.price) return html`<p class="read-bar secondary">${t(lang, "loading")}</p>`;
    return html`<p class="read-bar">
      <strong>${what}</strong> ${priceText(read.price, lang)}
      <span class="secondary">${t(lang, "read_scope_hint")}</span>
      ${read.price.queued
        ? html`<button class="primary" @click=${() => this._readCall(scope, true)}>${t(lang, "read_start")}</button>`
        : nothing}
      ${close}
    </p>`;
  }

  // ---- following: enable or disable the sensor behind a row, chosen here and applied in one go ------------------

  private _follows(): Follow[] {
    return (this._tree?.devices ?? []).flatMap((d) => [
      ...d.rows.map((r) => r.follow), ...d.programs.map((p) => p.follow),
    ]).filter((f): f is Follow => !!f);
  }

  private _followed(follow: Follow): boolean {
    return this._pending[follow.entity_id] ?? follow.enabled;
  }

  private _toggle(follow: Follow, wanted: boolean): void {
    this._pending = choose(this._pending, [follow], wanted);
    this._followNote = undefined;
  }

  private _followCell(follow: Follow | null, showLabel = true, rowLabel = ""): TemplateResult | typeof nothing {
    const lang = this._lang;
    if (!follow) return nothing;
    if (follow.blocked) return html`<span class="secondary">${t(lang, "follow_blocked")}</span>`;
    const changed = this._pending[follow.entity_id] !== undefined;
    const aria = rowLabel ? `${t(lang, "follow")} — ${rowLabel}` : t(lang, "follow");
    return html`<label class=${changed ? "follow changed" : "follow"}>
      <input type="checkbox" aria-label=${aria} .checked=${this._followed(follow)}
        @change=${(e: Event) => this._toggle(follow, (e.target as HTMLInputElement).checked)} />
      ${showLabel ? t(lang, "follow") : nothing}
    </label>`;
  }

  private _followBar(): TemplateResult | typeof nothing {
    const lang = this._lang;
    const plan = followPlan(this._pending, this._follows());
    const n = plan.enable.length + plan.disable.length;
    if (!n) {
      return this._followNote
        ? html`<div class=${this._followNote.error ? "message error" : "message"} role="status">
            ${this._followNote.text}
            <button class="ghost" type="button" aria-label=${t(lang, "dismiss")} @click=${() => (this._followNote = undefined)}>
              ×
            </button>
          </div>`
        : nothing;
    }
    return html`<div class="message follow-bar" role="status">
      <p>${t(lang, "follow_pending", { n, enable: plan.enable.length, disable: plan.disable.length })}</p>
      ${plan.enable.length ? html`<p class="secondary">${t(lang, "follow_reload", { s: 30 })}</p>` : nothing}
      ${plan.defaultsOff ? html`<p class="warning">${t(lang, "follow_defaults_off", { n: plan.defaultsOff })}</p>` : nothing}
      <details class="follow-details">
        <summary>${t(lang, "follow_details", { n })}</summary>
        <ul>
          ${plan.enable.map((id) => html`<li><code>+ ${id}</code></li>`)}
          ${plan.disable.map((id) => html`<li><code>− ${id}</code></li>`)}
        </ul>
      </details>
      <button class="primary" ?disabled=${this._busy} @click=${() => this._applyFollow()}>${t(lang, "follow_apply")}</button>
      <button class="link" @click=${() => (this._pending = {})}>${t(lang, "follow_discard")}</button>
    </div>`;
  }

  private async _applyFollow(): Promise<void> {
    const lang = this._lang;
    const plan = followPlan(this._pending, this._follows());
    this._busy = true;
    try {
      const answer = await this.hass.callWS<FollowAnswer>({
        type: "weishaupt/panel/follow", entry_id: this._entryId, enable: plan.enable, disable: plan.disable,
      });
      this._pending = {};
      const parts = [t(lang, "follow_done", { enabled: answer.enabled.length, disabled: answer.disabled.length })];
      if (answer.refused.length) parts.push(t(lang, "follow_refused", { n: answer.refused.length }));
      if (answer.reload) parts.push(t(lang, "follow_reload_soon", { s: answer.reload_after }));
      this._followNote = { text: parts.join(" "), error: answer.refused.length > 0 };
      // the registry as it is now (no reload needed for a disabled entity); a reload follows an enabled one
      if (this._entryId) await this._select(this._entryId, true);
    } catch (err) {
      this._followNote = { text: (err as Error).message, error: true };
    } finally {
      this._busy = false;
    }
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
        ${this._writesPill()}
        ${this._tree
          ? html`<button class="link" @click=${() => this._report()}>${t(lang, "report")}</button>
              <button class="link" @click=${() => this._csv()}>${t(lang, "export_csv")}</button>`
          : nothing}
        ${this._rowResult.__report__
          ? html`<span class="error" role="alert">
              ${this._rowResult.__report__.text}
              <button class="ghost" type="button" aria-label=${t(lang, "dismiss")} @click=${() => this._dismissRowResult("__report__")}>×</button>
            </span>`
          : nothing}
        ${this._tree?.writes?.clock_writable
          ? html`<button class="link" ?disabled=${this._busy} @click=${() => this._setClock()}>
              ${t(lang, "set_clock")}
            </button>`
          : nothing}
        ${this._rowResult.__clock__
          ? html`<span class=${this._rowResult.__clock__.error ? "error" : "secondary"} role="status">
              ${this._rowResult.__clock__.text}
              <button class="ghost" type="button" aria-label=${t(lang, "dismiss")} @click=${() => this._dismissRowResult("__clock__")}>×</button>
            </span>`
          : nothing}
      </header>
      ${this._available ? nothing : html`<div class="message warning" role="status">${t(lang, "unavailable")}</div>`}
      ${this._reloading ? html`<div class="message" role="status">${t(lang, "reloading")}</div>` : nothing}
      ${this._tree ? html`<div class="top-tools">${this._searchBar()}${this._readBar()}</div>` : nothing}
      ${this._followBar()}
      ${this._tree ? this._body(this._tree) : html`<div class="message">${t(lang, "loading")}</div>`}
      ${this._dialog ? this._confirmDialog(this._dialog.answer) : nothing}
    `;
  }

  // ---- writes: through the integration's writer and its guard (panel.py); nothing is written here --------------

  private async _call(message: Record<string, unknown>): Promise<WriteAnswer> {
    this._busy = true;
    try {
      const answer = await this.hass.callWS<WriteAnswer>({ ...message, entry_id: this._entryId, language: this._lang });
      if (answer.guard && this._tree?.writes) {
        this._tree = { ...this._tree, writes: { ...this._tree.writes, ...answer.guard } };
      }
      return answer;
    } catch (err) {
      // the connection to Home Assistant dropped, or it answered with an error: say what is known
      const error = err as { code?: string; message?: string };
      const lost = !error?.code || error.code === "connection_lost" || /connection/i.test(error.message ?? "");
      return {
        status: "refused",
        code: lost ? "interrupted" : error.code,
        message: lost ? t(this._lang, "interrupted") : error.message || error.code,
      };
    } finally {
      this._busy = false;
    }
  }

  /** The writes switch as Home Assistant shows it now (it follows a change made anywhere, without a reload). */
  private _switchOn(): boolean {
    const writes = this._tree?.writes;
    if (!writes) return false;
    const state = writes.switch_entity_id ? this.hass.states[writes.switch_entity_id] : undefined;
    return state ? state.state === "on" : writes.switch;
  }

  private _writesPill(): TemplateResult | typeof nothing {
    const writes = this._tree?.writes;
    if (!writes) return nothing;
    const lang = this._lang;
    const on = this._switchOn();
    const state = writes.switch_entity_id ? this.hass.states[writes.switch_entity_id] : undefined;
    const used = typeof state?.attributes.writes_last_hour === "number"
      ? state.attributes.writes_last_hour
      : writes.writes_last_hour;
    const max = typeof state?.attributes.max_writes_per_hour === "number"
      ? state.attributes.max_writes_per_hour
      : writes.max_per_hour;
    const text = on ? t(lang, "writes_pill_on", { n: used, max }) : t(lang, "writes_pill_off");
    if (writes.switch_entity_id) {
      return html`<button class="writes-pill ${on ? "on" : "off"}" @click=${() => this._open(writes.switch_entity_id!)}>
        ${text}
      </button>`;
    }
    return html`<span class="writes-pill ${on ? "on" : "off"}">${text}</span>`;
  }

  private _switchOffHint(): TemplateResult {
    const lang = this._lang;
    const id = this._tree?.writes?.switch_entity_id;
    return html`<div class="error">
      ${t(lang, "switch_off_hint")}
      ${id
        ? html` <button class="link" type="button" @click=${() => this._open(id)}>${t(lang, "open_switch")}</button>`
        : nothing}
    </div>`;
  }

  private _resultText(answer: WriteAnswer): { text: string; error: boolean } {
    const lang = this._lang;
    if (answer.status === "refused") return { text: t(lang, "not_written", { message: answer.message ?? "" }), error: true };
    if (answer.kind === "clock" || answer.requested !== undefined) {
      return {
        text: t(lang, "clock_sent", {
          requested: answer.requested ?? "",
          frame: answer.frame ?? "",
          result: answer.result_text ?? answer.result ?? "",
        }),
        error: answer.result !== "sent",
      };
    }
    return {
      text: t(lang, "written_line", {
        before: answer.before ?? "-",
        after: answer.after ?? "",
        frame: answer.frame ? ` (${answer.frame})` : "",
        result: answer.result_text ?? answer.result ?? "",
      }),
      error: answer.result !== "ok" && answer.result !== "unchanged",
    };
  }

  private _writing(target: string): void {
    this._rowResult = { ...this._rowResult, [target]: { text: t(this._lang, "writing"), error: false } };
  }

  private async _writeRow(row: Row): Promise<void> {
    const writable = row.writable!;
    const value = Number(this._draft);
    this._writing(row.key);
    const answer = await this._call({ type: "weishaupt/panel/write", key: writable.key, value });
    this._handle(answer, row.key);
    if (answer.status !== "refused") this._editing = undefined;
  }

  private _handle(answer: WriteAnswer, target: string): void {
    if (answer.status === "confirm") {
      this._dialog = { answer, target };
      return;
    }
    this._rowResult = { ...this._rowResult, [target]: this._resultText(answer) };
  }

  private async _setClock(): Promise<void> {
    this._writing("__clock__");
    this._handle(await this._call({ type: "weishaupt/panel/clock" }), "__clock__");
  }

  private async _confirmed(): Promise<void> {
    const dialog = this._dialog!;
    this._dialog = undefined;
    this._writing(dialog.target);
    const answer = await this._call({ type: "weishaupt/panel/confirm", pending_id: dialog.answer.pending_id });
    this._rowResult = { ...this._rowResult, [dialog.target]: this._resultText(answer) };
  }

  private async _withdrawn(): Promise<void> {
    const dialog = this._dialog!;
    this._dialog = undefined;
    const rest = { ...this._rowResult };
    delete rest[dialog.target]; // the "writing…" of the request: nothing was written
    this._rowResult = rest;
    await this._call({ type: "weishaupt/panel/cancel", pending_id: dialog.answer.pending_id });
  }

  private _dialogKeydown(e: KeyboardEvent): void {
    if (e.key === "Escape") {
      void this._withdrawn();
      return;
    }
    if (e.key !== "Tab") return;
    const dialog = e.currentTarget as HTMLElement;
    const focusable = Array.from(dialog.querySelectorAll<HTMLElement>("button:not([disabled]), [href], input, select, [tabindex]:not([tabindex='-1'])"));
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = this.renderRoot instanceof ShadowRoot ? this.renderRoot.activeElement : document.activeElement;
    if (e.shiftKey && active === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && active === last) {
      e.preventDefault();
      first.focus();
    }
  }

  private _confirmDialog(answer: WriteAnswer): TemplateResult {
    const lang = this._lang;
    const p = answer.placeholders ?? {};
    const clock = answer.kind === "clock";
    return html`<div
      class="backdrop"
      @click=${(e: MouseEvent) => e.target === e.currentTarget && void this._withdrawn()}
    >
      <div
        class="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        @keydown=${(e: KeyboardEvent) => this._dialogKeydown(e)}
      >
        <h2 id="confirm-title">${t(lang, "confirm_title", { setting: p.setting ?? "", device: p.device ?? "" })}</h2>
        ${clock
          ? html`<p>${t(lang, "clock_current", { current: p.current ?? "-" })}</p>
              <p>${t(lang, "clock_confirm", { send_at: p.send_at ?? "", late: p.late ?? "" })}</p>`
          : html`<dl>
                <dt>${t(lang, "current")}</dt>
                <dd>${p.current}</dd>
                <dt>${t(lang, "new_value")}</dt>
                <dd><strong>${p.requested}</strong></dd>
                <dt>${t(lang, "allowed")}</dt>
                <dd>${p.allowed}</dd>
              </dl>
              <p>${t(lang, "path", p)}</p>
              <p class="secondary">${t(lang, "regulation_note")}</p>`}
        <div class="actions">
          <button class="link cancel" @click=${() => this._withdrawn()}>${t(lang, "cancel")}</button>
          <button class="primary" @click=${() => this._confirmed()}>
            ${t(lang, clock ? "confirm_clock" : "confirm")}
          </button>
        </div>
      </div>
    </div>`;
  }

  private _dismissRowResult(key: string): void {
    const rest = { ...this._rowResult };
    delete rest[key];
    this._rowResult = rest;
  }

  private _dismissWeekResult(key: string): void {
    const rest = { ...this._weekResult };
    delete rest[key];
    this._weekResult = rest;
  }

  private _writeCell(row: Row): TemplateResult {
    const lang = this._lang;
    const writable = row.writable;
    if (row.edited_on) {
      return html`<span class="secondary">${t(lang, "edited_on_setting", { device: label(row.edited_on.device, lang) })}</span>`;
    }
    if (!writable) return html`<span class="secondary">${t(lang, "read_only")}</span>`;
    const result = this._rowResult[row.key];
    const badge = html`<span class="badge ${writable.risk}">${t(lang, writable.risk)}</span>${writable.through
        ? html`<div class="secondary">${t(lang, "through", { circuit: writable.through })}</div>`
        : nothing}`;
    let action: TemplateResult | typeof nothing = nothing;
    if (!writable.offered) {
      action = html`<div class="secondary">
        ${writable.why_not === "writes_disabled"
          ? t(lang, "not_offered_writes_disabled")
          : t(lang, "not_offered", { reason: writable.why_not ?? "" })}
      </div>`;
    } else if (this._editing === row.key) {
      action = nothing; // the form is on its own line below the row
    } else {
      action = html`<button class="link" @click=${() => this._startEdit(row)}>${t(lang, "edit")}</button>`;
    }
    return html`${badge}${action}${result
      ? html`<div class=${result.error ? "error" : "secondary"} role="status">
          ${result.text}
          <button class="ghost" type="button" aria-label=${t(lang, "dismiss")} @click=${() => this._dismissRowResult(row.key)}>×</button>
        </div>`
      : nothing}`;
  }

  private _editForm(row: Row): TemplateResult {
    const lang = this._lang;
    const writable = row.writable!;
    const reading = readingOf(row, this._readings);
    const currentDraft = initialDraft(row, reading);
    const unchanged = currentDraft !== "" && this._draft === currentDraft;
    const switchOn = this._switchOn();
    const range = formatRange(row, lang);
    return html`<form
        class="edit"
        @keydown=${(e: KeyboardEvent) => e.key === "Escape" && (this._editing = undefined)}
        @submit=${(e: Event) => {
          e.preventDefault();
          void this._writeRow(row);
        }}
      >
        ${writable.options
          ? html`<select aria-label=${t(lang, "new_value")}
              @change=${(e: Event) => (this._draft = (e.target as HTMLSelectElement).value)}>
              <option value="" ?selected=${this._draft === ""} disabled>…</option>
              ${writable.options.map(
                (o) => html`<option value=${o.raw} ?selected=${String(o.raw) === this._draft}>${label(o.label, lang)}</option>`,
              )}
            </select>`
          : html`<input type="number" aria-label=${t(lang, "new_value")} .value=${this._draft}
              min=${writable.minimum ?? ""} max=${writable.maximum ?? ""} step=${writable.step ?? "any"}
              @input=${(e: Event) => (this._draft = (e.target as HTMLInputElement).value)} />${row.unit
              ? html` ${row.unit}`
              : nothing}${range ? html` <span class="secondary">(${range})</span>` : nothing}`}
        <button class="primary" type="submit" ?disabled=${this._busy || this._draft === "" || unchanged || !switchOn}>
          ${t(lang, "write_now")}
        </button>
        <button class="link" type="button" @click=${() => (this._editing = undefined)}>${t(lang, "cancel")}</button>
        <div class="secondary">
          ${formatValue(row, reading, lang) ?? "-"} ·
          ${t(lang, "path_short", { address: writable.address ?? "", register: writable.register ?? "", source: writable.source })}
        </div>
        <div class="secondary">${t(lang, writable.risk === "comfort" ? "comfort_note" : "regulation_note")}</div>
        ${this._tree?.writes && !switchOn ? this._switchOffHint() : nothing}
      </form>`;
  }

  private _startEdit(row: Row): void {
    this._draft = initialDraft(row, readingOf(row, this._readings));
    this._editing = row.key;
  }

  // ---- week grid editing --------------------------------------------------------------------------------------

  private _dayText(week: Days | undefined, day: string): string | null {
    const ranges = week?.[day];
    if (ranges === undefined || ranges === null) return null;
    return formatDay(ranges.map(([a, b]) => [minutesOf(a), minutesOf(b)]));
  }

  private _startWeek(program: Program): void {
    const week = this._programs[program.key];
    const draft: Record<string, string> = {};
    // a day not read yet starts empty and is written only if something is typed or drawn in it
    for (let day = 1; day <= 7; day++) draft[String(day)] = this._dayText(week, String(day)) ?? "";
    this._weekDraft = { ...this._weekDraft, [program.key]: draft };
    this._weekResult = { ...this._weekResult, [program.key]: undefined as never };
  }

  private _setDay(program: string, day: string, text: string): void {
    this._weekDraft = { ...this._weekDraft, [program]: { ...this._weekDraft[program], [day]: text } };
    const key = `${program}|${day}`;
    if (this._dragError[key]) {
      const rest = { ...this._dragError };
      delete rest[key];
      this._dragError = rest;
    }
  }

  private _changed(program: Program): string[] {
    const draft = this._weekDraft[program.key] ?? {};
    const week = this._programs[program.key];
    return Object.keys(draft).filter((day) => {
      const current = this._dayText(week, day);
      if (current === null && draft[day].trim() === "") return false;
      const parsed = parseDay(draft[day]);
      const text = "ranges" in parsed ? formatDay(parsed.ranges) : draft[day];
      return text !== current;
    });
  }

  private async _writeWeek(program: Program): Promise<void> {
    const draft = this._weekDraft[program.key];
    const days: Record<string, string> = {};
    for (const day of this._changed(program)) days[day] = draft[day];
    this._weekResult = { ...this._weekResult, [program.key]: { text: t(this._lang, "writing"), error: false } };
    const answer = await this._call({ type: "weishaupt/panel/write_days", program: program.key, days });
    const lang = this._lang;
    if (answer.status === "refused") {
      this._weekResult = { ...this._weekResult, [program.key]: this._resultText(answer) };
      return;
    }
    const names = WEEKDAYS[lang] ?? WEEKDAYS.en;
    const lines = Object.entries(answer.days ?? {}).map(([day, d]) =>
      t(lang, "written_line", {
        before: `${names[Number(day) - 1]} ${d.before ?? "-"}`,
        after: d.after ?? "",
        frame: d.frames?.length ? ` (${d.frames.join(", ")})` : "",
        result: d.result_text ?? d.result ?? "",
      }),
    );
    this._weekResult = { ...this._weekResult, [program.key]: { text: lines.join(" · "), error: false } };
    const rest = { ...this._weekDraft };
    delete rest[program.key];
    this._weekDraft = rest;
  }

  private _copy(program: string, from: string, target: string): void {
    const text = this._weekDraft[program][from];
    const targets = target === "all" ? ["1", "2", "3", "4", "5", "6", "7"]
      : target === "weekdays" ? ["1", "2", "3", "4", "5"]
      : target === "weekend" ? ["6", "7"] : [target];
    const next = { ...this._weekDraft[program] };
    for (const day of targets) if (day !== from) next[day] = text;
    this._weekDraft = { ...this._weekDraft, [program]: next };
  }

  private _dragStart(e: PointerEvent, program: string, day: string): void {
    const element = e.currentTarget as HTMLElement;
    if ((e.target as HTMLElement).classList.contains("bar")) return; // a click on a range removes it
    const box = element.getBoundingClientRect();
    const from = (e.clientX - box.left) / box.width;
    this._drag = { program, day, from, element };
    const [start, end] = dragRange(from, from);
    this._dragPreview = { program, day, start, end };
    element.setPointerCapture(e.pointerId);
  }

  private _dragMove(e: PointerEvent): void {
    const drag = this._drag;
    if (!drag) return;
    const box = drag.element.getBoundingClientRect();
    const [start, end] = dragRange(drag.from, (e.clientX - box.left) / box.width);
    this._dragPreview = { program: drag.program, day: drag.day, start, end };
  }

  private _dragCancel(): void {
    this._drag = undefined;
    this._dragPreview = undefined;
  }

  private _dragEnd(e: PointerEvent): void {
    const drag = this._drag;
    this._drag = undefined;
    this._dragPreview = undefined;
    if (!drag) return;
    const box = drag.element.getBoundingClientRect();
    const parsed = parseDay(this._weekDraft[drag.program][drag.day]);
    if (!("ranges" in parsed)) return;
    const next = addDragged(parsed.ranges, drag.from, (e.clientX - box.left) / box.width);
    if (next) this._setDay(drag.program, drag.day, formatDay(next));
    else this._dragError = { ...this._dragError, [`${drag.program}|${drag.day}`]: "day_too_many" };
  }

  private _removeRange(program: string, day: string, index: number): void {
    const parsed = parseDay(this._weekDraft[program][day]);
    if (!("ranges" in parsed)) return;
    this._setDay(program, day, formatDay(parsed.ranges.filter((_, i) => i !== index)));
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

  private _searchActive(): boolean {
    return this._query.trim() !== "" || this._filter !== "all";
  }

  private _clearSearch(): void {
    this._query = "";
    this._filter = "all";
  }

  private _searchBar(): TemplateResult {
    const lang = this._lang;
    const filters: [RowFilter, string][] = [
      ["all", t(lang, "filter_all")],
      ["writable", t(lang, "filter_writable")],
      ["followed", t(lang, "filter_followed")],
      ["unread", t(lang, "filter_unread")],
    ];
    return html`<div class="search-bar" role="search">
      <input
        type="search"
        .value=${this._query}
        placeholder=${t(lang, "search_placeholder")}
        aria-label=${t(lang, "search_placeholder")}
        @input=${(e: Event) => (this._query = (e.target as HTMLInputElement).value)}
        @keydown=${(e: KeyboardEvent) => e.key === "Escape" && this._clearSearch()}
      />
      <div class="filters" role="group">
        ${filters.map(
          ([id, text]) => html`<button
            type="button"
            class="filter-pill ${this._filter === id ? "active" : ""}"
            aria-pressed=${this._filter === id ? "true" : "false"}
            @click=${() => (this._filter = id)}
          >
            ${text}
          </button>`,
        )}
      </div>
      ${this._searchActive()
        ? html`<button type="button" class="link" @click=${() => this._clearSearch()}>${t(lang, "search_clear")}</button>`
        : nothing}
    </div>`;
  }

  private _searchView(tree: Tree): TemplateResult {
    const lang = this._lang;
    const groups = tree.devices
      .map((device) => ({
        device,
        rows: device.rows.filter((row) => matchesRow(row, this._query, this._filter, this._readings, lang)),
      }))
      .filter((g) => g.rows.length > 0);
    const total = groups.reduce((acc, g) => acc + g.rows.length, 0);
    return html`<h2>${t(lang, total === 1 ? "search_results_one" : "search_results", { n: total })}</h2>
      ${total === 0
        ? html`<p class="secondary">${t(lang, "search_empty")}</p>`
        : groups.map(
            ({ device, rows }) => html`<h3>${label(device.label, lang)} (${rows.length})</h3>
              ${this._table(rows)}`,
          )}`;
  }

  private _body(tree: Tree): TemplateResult {
    const device = tree.devices.find((d) => d.id === this._device);
    return html`<div class=${this.narrow ? "layout narrow" : "layout"}>
      <nav aria-label=${t(this._lang, "devices")}>${this._nav(tree)}</nav>
      <main>
        ${this._searchActive()
          ? this._searchView(tree)
          : this._menu === DEFINITIONS
          ? this._definitions(tree)
          : this._menu === FAULTS
            ? (() => {
                const table = this._faults?.find((f) => f.device === this._device);
                return table ? this._faultsView(table) : html`<p class="secondary">${t(this._lang, "loading")}</p>`;
              })()
            : device
              ? this._device_view(device)
              : nothing}
      </main>
    </div>`;
  }

  private _faultBadge(deviceId: string): number {
    const table = this._faults?.find((f) => f.device === deviceId);
    if (!table) return 0;
    const hist = table.history?.entries?.length ?? 0;
    if (hist > 0) return hist;
    return (table.counters ?? []).filter((c) => (c.count ?? 0) > 0).length;
  }

  private _menuPendingCount(device: Device, menuId: string): number {
    const rowPending = device.rows.filter(
      (r) =>
        (r.menu === menuId || descends(device.menus, r.menu, menuId)) &&
        r.follow &&
        this._pending[r.follow.entity_id] !== undefined,
    ).length;
    const progPending = menuId === PROGRAMS
      ? device.programs.filter((p) => p.follow && this._pending[p.follow.entity_id] !== undefined).length
      : 0;
    return rowPending + progPending;
  }

  private _nav(tree: Tree): TemplateResult {
    const lang = this._lang;
    const selectMenu = (device: string, menu: string): void => {
      this._device = device;
      this._menu = menu;
      if (this._searchActive()) this._clearSearch();
    };
    if (this.narrow) {
      // a phone: one list to choose from, so that the table is not pushed below the whole tree
      const current = `${this._device ?? ""}|${this._menu ?? ""}`;
      return html`<label class="choose"
        >${t(lang, "devices")}
        <select
          @change=${(e: Event) => {
            const [device, menu] = (e.target as HTMLSelectElement).value.split("|");
            selectMenu(device, menu);
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
              ${this._faults?.some((f) => f.device === device.id)
                ? html`<option value=${`${device.id}|${FAULTS}`} ?selected=${current === `${device.id}|${FAULTS}`}>
                    ${t(lang, "faults")}
                  </option>`
                : nothing}
            </optgroup>`,
          )}
          <option value=${`${this._device ?? ""}|${DEFINITIONS}`} ?selected=${this._menu === DEFINITIONS}>
            ${t(lang, "definitions")}
          </option>
        </select></label
      >`;
    }
    const item = (device: string, menu: string, text: string, depth: number, badge = ""): TemplateResult => {
      const current = !this._searchActive() && this._device === device && this._menu === menu;
      return html`<li>
        <button
          class="menu depth${depth}"
          aria-current=${current ? "page" : "false"}
          @click=${() => selectMenu(device, menu)}
        >
          <span>${text}</span>
          ${badge ? html`<span class="nav-badge">${badge}</span>` : nothing}
        </button>
      </li>`;
    };
    return html`<ul>
      ${tree.devices.map((device) => {
        const faultCount = this._faultBadge(device.id);
        const hasWeekDraft = device.programs.some((p) => this._weekDraft[p.key] !== undefined);
        return html`<li>
          <span class="device">${label(device.label, lang)}</span>
          <ul>
            ${menuTree(device.menus).map(([menu, depth]) => {
              const pending = this._menuPendingCount(device, menu.id);
              const badge = menu.id === PROGRAMS && hasWeekDraft ? "•" : pending > 0 ? String(pending) : "";
              return item(device.id, menu.id, label(menu.label, lang), depth, badge);
            })}
            ${this._faults?.some((f) => f.device === device.id)
              ? item(device.id, FAULTS, t(lang, "faults"), 0, faultCount > 0 ? String(faultCount) : "")
              : nothing}
          </ul>
        </li>`;
      })}
      <li class="nav-sep" role="separator"></li>
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
      ${device.rows.some((r) => !r.listened && r.read && !r.passive) ? this._readBar(device.id) : nothing}
      ${this._menu === PROGRAMS ? this._programs_view(device) : nothing}
      ${sections.length ? html`<p class="secondary">${t(lang, "write_hint")}</p>` : nothing}
      ${sections.map(
        ([m, rows]) => html`${m.id !== this._menu ? html`<h3>${label(m.label, lang)}</h3>` : nothing}
          <div class="table-tools">
            ${rows.some((r) => !r.listened && r.read && !r.passive) ? this._readBar(device.id, m.id) : nothing}
            ${rows.some((r) => r.follow && !r.follow.blocked)
              ? html`<span>
                  <button class="ghost" @click=${() => (this._pending = choose(this._pending, rows.map((r) => r.follow), true))}>
                    ${t(lang, "follow_all")}</button>
                  <button class="ghost" @click=${() => (this._pending = choose(this._pending, rows.map((r) => r.follow), false))}>
                    ${t(lang, "follow_none")}</button>
                </span>`
              : nothing}
          </div>
          ${this._table(rows)}`,
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
              <th scope="col">${t(lang, "follow")}</th>
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
                <td class="nowrap num">${value ?? html`<span class="secondary">${t(lang, missingReason(row))}</span>`}</td>
                <td class="secondary nowrap">
                  ${reading ? this._age(reading) : ""}${reading?.kept
                    ? html`<div class="kept">${t(lang, "kept")}</div>`
                    : nothing}${row.passive ? html`<div>${t(lang, "passive")}</div>` : nothing}${reading?.once && !row.passive
                    ? html`<div class="kept">${t(lang, "read_once")}</div>`
                    : nothing}
                </td>
                <td class="nowrap num">${formatRange(row, lang)}</td>
                <td>${this._writeCell(row)}</td>
                <td>
                  ${row.entity_id
                    ? html`<button class="ghost" @click=${() => this._open(row.entity_id!)}>${t(lang, "open")}</button>`
                    : nothing}
                </td>
                <td class="follow-cell">${this._followCell(row.follow, false, label(row.label, lang))}</td>
              </tr>${this._editing === row.key
                ? html`<tr class="edit-row"><td colspan="7">${this._editForm(row)}</td></tr>`
                : nothing}`;
            })}
          </tbody>
        </table>
      </div>`;
  }

  private _programs_view(device: Device): TemplateResult {
    const lang = this._lang;
    const days = WEEKDAYS[lang] ?? WEEKDAYS.en;
    const writes = this._tree?.writes;
    return html`${device.programs.map((program) => {
      const week = this._programs[program.key];
      const draft = this._weekDraft[program.key];
      const editing = draft !== undefined;
      const changed = editing ? this._changed(program) : [];
      const errors = editing
        ? Object.fromEntries(Object.entries(draft).map(([day, text]) => {
            const parsed = parseDay(text);
            return [day, "error" in parsed ? parsed.error : null];
          }))
        : {};
      const invalid = Object.values(errors).some(Boolean);
      const note = program.edited_on
        ? t(lang, "edited_on_program", {
            program: label(program.edited_on.label, lang), device: label(program.edited_on.device, lang),
          })
        : !program.read
        ? t(lang, "not_read_program")
        : !program.listened
          ? t(lang, "program_not_listened")
          : program.writable
            ? t(lang, "editable")
            : t(lang, "not_editable");
      const result = this._weekResult[program.key];
      return html`<section class="program">
        <h3>
          ${label(program.label, lang)}
          ${program.stored_only ? html`<span class="badge">${t(lang, "stored_only_badge")}</span>` : nothing}
          ${program.entity_id
            ? html`<button class="link" @click=${() => this._open(program.entity_id!)}>${t(lang, "open")}</button>`
            : nothing}
          ${program.writable && writes && !editing
            ? html`<button class="link" @click=${() => this._startWeek(program)}>${t(lang, "edit_days")}</button>`
            : nothing}
          ${this._followCell(program.follow)}
        </h3>
        <p class="secondary">${note}</p>
        ${program.stored_only ? html`<p class="secondary">${t(lang, "stored_only_note")}</p>` : nothing}
        ${program.read && !program.listened
          ? this._queued[program.key] !== undefined
            ? html`<p class="secondary" role="status">${queuedText(this._queued[program.key], lang)}</p>`
            : html`<p>
                <button class="link" @click=${() => this._readProgram(program.key)}>${t(lang, "read_now")}</button>
                <span class="secondary"
                  >${t(lang, "read_cost", { n: program.to_read, s: Math.round(program.to_read * 2.2) })}</span
                >
              </p>`
          : nothing}
        ${editing ? html`<p class="secondary">${t(lang, "drag_hint")}</p>` : nothing}
        ${!editing
          ? html`<weishaupt-week-grid
              .days=${week}
              language=${lang}
              unread=${t(lang, program.listened ? "day_unread" : "not_listened")}
              caption=${label(program.label, lang)}
              today=${isoWeekday(new Date())}
            ></weishaupt-week-grid>`
          : html`<table class="week">
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
              const day = String(i + 1);
              if (editing) {
                const parsed = parseDay(draft[day]);
                const ranges = "ranges" in parsed ? parsed.ranges : [];
                const error = errors[day] ?? this._dragError[`${program.key}|${day}`] ?? null;
                const preview =
                  this._dragPreview?.program === program.key && this._dragPreview.day === day
                    ? this._dragPreview
                    : undefined;
                return html`<tr class=${changed.includes(day) ? "changed" : ""}>
                  <th scope="row">${name}</th>
                  <td>
                    <div
                      class="day editable"
                      aria-hidden="true"
                      @pointerdown=${(e: PointerEvent) => this._dragStart(e, program.key, day)}
                      @pointermove=${(e: PointerEvent) => this._dragMove(e)}
                      @pointerup=${(e: PointerEvent) => this._dragEnd(e)}
                      @pointercancel=${() => this._dragCancel()}
                    >
                      ${ranges.map(
                        ([a, b], index) => html`<span
                          class="bar"
                          title=${t(lang, "bar_remove_hint", { range: `${clockText(a)}-${clockText(b)}` })}
                          style="left:${(a / 1440) * 100}%;width:${((b - a) / 1440) * 100}%"
                          @click=${() => this._removeRange(program.key, day, index)}
                        ></span>`,
                      )}
                      ${preview
                        ? html`<span
                              class="bar preview"
                              style="left:${(preview.start / 1440) * 100}%;width:${((preview.end - preview.start) / 1440) * 100}%"
                            ></span>
                            <span
                              class="drag-label"
                              style="left:${((preview.start + preview.end) / 2880) * 100}%"
                            >${clockText(preview.start)}–${clockText(preview.end)}</span>`
                        : nothing}
                    </div>
                    <div class="day-edit">
                      <input
                        type="text"
                        aria-label=${name}
                        aria-invalid=${error ? "true" : "false"}
                        placeholder=${week?.[day] == null ? t(lang, "day_unread") : ""}
                        .value=${draft[day]}
                        @input=${(e: Event) => this._setDay(program.key, day, (e.target as HTMLInputElement).value)}
                      />
                      <button
                        class="ghost"
                        type="button"
                        ?disabled=${draft[day].trim() === "" || draft[day].trim() === "-"}
                        @click=${() => this._setDay(program.key, day, "-")}
                      >
                        ${t(lang, "clear_day")}
                      </button>
                      <label class="secondary"
                        >${t(lang, "copy_to")}
                        <select
                          @change=${(e: Event) => {
                            const select = e.target as HTMLSelectElement;
                            if (select.value) this._copy(program.key, day, select.value);
                            select.value = "";
                          }}
                        >
                          <option value="">…</option>
                          <option value="all">${t(lang, "copy_all")}</option>
                          <option value="weekdays">${t(lang, "copy_weekdays")}</option>
                          <option value="weekend">${t(lang, "copy_weekend")}</option>
                          ${days.map((other, k) => (k === i ? nothing : html`<option value=${String(k + 1)}>${other}</option>`))}
                        </select></label
                      >
                    </div>
                    ${error ? html`<div class="error" role="alert">${t(lang, error)}</div>` : nothing}
                  </td>
                </tr>`;
              }
              return nothing; // the read-only grid is <weishaupt-week-grid>
            })}
          </tbody>
        </table>`}
        ${editing && writes
          ? html`<p class="secondary">
                ${t(lang, changed.length === 1 ? "cost_one" : "cost", {
                  days: changed.length,
                  writes: changed.length * 3,
                  used: writes.writes_last_hour,
                  max: writes.max_per_hour,
                })}
              </p>
              ${this._switchOn() ? nothing : this._switchOffHint()}
              <div class="actions">
                <button class="link" @click=${() => {
                  const rest = { ...this._weekDraft };
                  delete rest[program.key];
                  this._weekDraft = rest;
                }}>${t(lang, "discard")}</button>
                <button class="primary" ?disabled=${this._busy || invalid || !changed.length || !this._switchOn()}
                  @click=${() => this._writeWeek(program)}>${t(lang, "write_days")}</button>
              </div>`
          : nothing}
        ${result
          ? html`<p class=${result.error ? "error" : "secondary"} role="status">
              ${result.text}
              <button class="ghost" type="button" aria-label=${t(lang, "dismiss")} @click=${() => this._dismissWeekResult(program.key)}>×</button>
            </p>`
          : nothing}
      </section>`;
    })}`;
  }

  private _definitions(tree: Tree): TemplateResult {
    const lang = this._lang;
    const d = tree.definitions;
    const list = (items: string[]): TemplateResult => {
      if (!items.length) return html`${t(lang, "none")}`;
      const ul = html`<ul>${items.map((i) => html`<li><code>${i}</code></li>`)}</ul>`;
      if (items.length <= 5) return ul;
      const summary = t(lang, items.length === 1 ? "items_count_one" : "items_count", { n: items.length });
      return html`<details><summary>${summary}</summary>${ul}</details>`;
    };
    const writes = tree.writes;
    return html`<h2>${t(lang, "definitions")}</h2>
      <dl>
        <dt>${t(lang, "in_use")}</dt>
        <dd>
          ${d.version}${d.commit ? html` <code>${d.commit.slice(0, 7)}</code>` : nothing} —
          ${d.source === "bundled" ? t(lang, "source_bundled") : t(lang, "source_file", { file: d.source })}
        </dd>
        <dt>${t(lang, "ebusd")}</dt>
        <dd>
          ${tree.ebusd.endpoint ?? "?"} · ${tree.ebusd.version ?? "?"}${tree.ebusd.own_address ? ` (${tree.ebusd.own_address})` : ""} ·
          ${t(lang, "capability", { value: tree.ebusd.capability })} ·
          ${t(lang, tree.ebusd.mode === "follow" ? "mode_follow" : "mode_pinned", { n: tree.ebusd.endpoints.length })}
        </dd>
        <dt>${t(lang, "writes")}</dt>
        <dd>
          ${writes
            ? html`${t(lang, this._switchOn() ? "switch_on" : "switch_off")} ·
              ${t(lang, "capability", { value: writes.capability })} ·
              ${t(lang, "per_hour", { n: writes.writes_last_hour, max: writes.max_per_hour })}`
            : t(lang, "writes_off")}
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
        <dt>${t(lang, "unknown_addresses")}</dt>
        <dd>${list(tree.unknown_addresses)}</dd>
        <dt>${t(lang, "named_from_metadata")}</dt>
        <dd>
          ${list(d.named_from_metadata.map((e) => (e.disabled ? `${e.entity_id} (${t(lang, "disabled")})` : e.entity_id)))}
        </dd>
        <dt>${t(lang, "not_named")}</dt>
        <dd>${list(d.not_named)}</dd>
        ${writes
          ? html`<dt>${t(lang, "read_only_settings")}</dt>
              <dd>${list(writes.read_only.map((r) => `${r.key}: ${r.reason}`))}</dd>`
          : nothing}
      </dl>`;
  }

  static styles = css`
    .read-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      margin: 4px 0;
    }
    .top-tools {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px 16px;
      padding: 8px 16px 0;
    }
    .search-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px 8px;
      flex: 1 1 320px;
    }
    .search-bar input[type="search"] {
      flex: 1 1 200px;
      max-width: 340px;
      min-width: 0;
    }
    .filters {
      display: inline-flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    .filter-pill {
      border: 1px solid var(--divider-color);
      background: var(--card-background-color);
      color: var(--secondary-text-color);
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 0.85em;
      cursor: pointer;
    }
    .filter-pill.active {
      border-color: var(--primary-color);
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    .read-bar progress {
      width: 160px;
    }
    .table-tools {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    .follow {
      white-space: nowrap;
      font-weight: normal;
      font-size: 0.9em;
    }
    .follow.changed {
      font-style: italic;
    }
    .follow-bar {
      position: sticky;
      top: 0;
      z-index: 2;
      background: var(--card-background-color, var(--primary-background-color));
      border-bottom: 1px solid var(--divider-color);
      border-inline-start: 4px solid var(--primary-color);
    }
    .follow-bar p {
      margin: 0 0 6px;
    }
    .follow-details {
      margin: 0 0 8px;
      font-size: 0.9em;
    }
    .follow-details ul {
      margin: 4px 0 0;
      padding-inline-start: 18px;
      max-height: 160px;
      overflow-y: auto;
    }
    .writes-pill {
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 0.9em;
      border: 1px solid currentColor;
      background: none;
      cursor: pointer;
    }
    .writes-pill.on {
      color: var(--success-color, var(--primary-color));
    }
    .writes-pill.off {
      color: var(--secondary-text-color);
    }
    .nav-sep {
      border-top: 1px solid var(--divider-color);
      margin: 10px 0;
    }
    .num {
      font-variant-numeric: tabular-nums;
    }
    .follow-cell {
      text-align: center;
    }
    .inline-check {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin: 0 0 8px;
      cursor: pointer;
    }
    details summary {
      cursor: pointer;
      color: var(--primary-color);
    }
    details[open] summary {
      margin-bottom: 4px;
    }
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
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      width: 100%;
      text-align: start;
      border: 0;
      background: none;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
    }
    .nav-badge {
      font-size: 0.78em;
      padding: 0 6px;
      border-radius: 10px;
      background: var(--secondary-background-color);
      color: var(--primary-color);
      font-weight: 500;
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
    button.ghost {
      border: 0;
      background: none;
      border-radius: 6px;
      padding: 2px 6px;
      cursor: pointer;
      color: var(--primary-color);
    }
    button.ghost:hover:not(:disabled) {
      background: var(--secondary-background-color);
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
    tbody tr:hover {
      background: var(--secondary-background-color);
    }
    tr.edit-row,
    tr.edit-row:hover {
      background: var(--secondary-background-color);
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
    .message.warning,
    .follow-bar .warning {
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
    .scale span:first-child {
      transform: none;
    }
    .scale span:last-child {
      transform: translateX(-100%);
    }
    .day {
      position: relative;
      height: 14px;
      background-color: var(--secondary-background-color);
      background-image: linear-gradient(
        to right,
        transparent calc(25% - 0.5px),
        var(--divider-color) 25%,
        transparent calc(25% + 0.5px),
        transparent calc(50% - 0.5px),
        var(--divider-color) 50%,
        transparent calc(50% + 0.5px),
        transparent calc(75% - 0.5px),
        var(--divider-color) 75%,
        transparent calc(75% + 0.5px)
      );
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
      grid-template-columns: minmax(0, max-content) minmax(0, 1fr);
      gap: 6px 16px;
    }
    dt {
      color: var(--secondary-text-color);
    }
    dd {
      margin: 0;
      min-width: 0; /* a long entity id wraps inside its column instead of widening the page */
      overflow-wrap: anywhere;
    }
    code {
      overflow-wrap: anywhere;
    }
    dd ul {
      margin: 0;
      padding-inline-start: 16px;
    }
    .error {
      color: var(--error-color);
    }
    button.primary {
      border: 0;
      border-radius: 6px;
      padding: 4px 12px;
      cursor: pointer;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    button:disabled {
      opacity: 0.5;
      cursor: default;
    }
    form.edit {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px 8px;
      margin-top: 6px;
    }
    form.edit div {
      flex-basis: 100%;
    }
    input {
      font: inherit;
      padding: 4px 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    input[type="number"] {
      width: 6em;
    }
    input[aria-invalid="true"] {
      border-color: var(--error-color);
    }
    .day.editable {
      cursor: crosshair;
      height: 22px;
      touch-action: none;
    }
    .day.editable .bar {
      cursor: pointer;
    }
    .day.editable .bar:hover {
      background: var(--error-color);
    }
    .bar.preview {
      opacity: 0.45;
      pointer-events: none;
    }
    .drag-label {
      position: absolute;
      top: -22px;
      transform: translateX(-50%);
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 0.78em;
      white-space: nowrap;
      background: var(--primary-text-color);
      color: var(--card-background-color);
      pointer-events: none;
      z-index: 3;
    }
    .day-edit {
      display: flex;
      flex-wrap: wrap;
      gap: 4px 12px;
      margin-top: 4px;
      align-items: center;
    }
    .day-edit input {
      flex: 1 1 14em;
      min-width: 0;
    }
    tr.changed th {
      font-weight: 500;
      color: var(--primary-color);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 10;
    }
    .dialog {
      background: var(--card-background-color);
      color: var(--primary-text-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 16px 20px;
      max-width: 560px;
      width: 100%;
      max-height: 90vh;
      overflow: auto;
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

/** "06:30" -> minutes since midnight. */
function minutesOf(time: string): number {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + (m || 0);
}
