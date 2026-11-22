// The week grid of one program, read only: seven rows, the enabled ranges as bars over 24 h and as text. Shared by
// the panel and the dashboard card. Uses only Home Assistant's theme variables.

import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { bars, t, WEEKDAYS } from "./format.ts";
import type { Days } from "./types.ts";

export class WeishauptWeekGrid extends LitElement {
  static properties = {
    days: { attribute: false },
    language: { type: String },
    unread: { type: String }, // text of a day not read yet
    today: { type: Number }, // 1 (Monday) … 7, 0 for none
    now: { type: Number }, // minutes since midnight; negative/omitted uses the current clock
    caption: { type: String },
  };

  declare days: Days | undefined;
  declare language: string;
  declare unread: string;
  declare today: number;
  declare now: number;
  declare caption: string;

  constructor() {
    super();
    this.language = "en";
    this.unread = "";
    this.today = 0;
    this.now = -1;
    this.caption = "";
  }

  render(): TemplateResult {
    const lang = this.language;
    const names = WEEKDAYS[lang] ?? WEEKDAYS.en;
    const currentMinutes = this.now >= 0 ? this.now : (() => {
      const d = new Date();
      return d.getHours() * 60 + d.getMinutes();
    })();
    const nowPercent = Math.min(100, Math.max(0, (currentMinutes / 1440) * 100));
    return html`<table>
      ${this.caption ? html`<caption class="visually-hidden">${this.caption}</caption>` : nothing}
      <thead>
        <tr>
          <th scope="col"><span class="visually-hidden">${t(lang, "programs")}</span></th>
          <td class="scale" aria-hidden="true">
            ${[0, 6, 12, 18, 24].map((h) => html`<span style="left:${(h / 24) * 100}%">${h}</span>`)}
          </td>
        </tr>
      </thead>
      <tbody>
        ${names.map((name, i) => {
          const ranges = this.days?.[String(i + 1)];
          const text =
            ranges === undefined || ranges === null
              ? this.unread || t(lang, "day_unread")
              : ranges.length
                ? ranges.map(([from, to]) => `${from}-${to}`).join(", ")
                : t(lang, "day_none");
          return html`<tr class=${this.today === i + 1 ? "today" : ""}>
            <th scope="row">${name}</th>
            <td>
              <div class="day" aria-hidden="true">
                ${(ranges ?? []).length
                  ? bars(ranges!).map(
                      (bar) => html`<span class="bar" style="left:${bar.left}%;width:${bar.width}%"></span>`,
                    )
                  : nothing}
                ${this.today === i + 1
                  ? html`<span class="now-line" style="left:${nowPercent}%"></span>`
                  : nothing}
              </div>
              <div class="day-text">${text}</div>
            </td>
          </tr>`;
        })}
      </tbody>
    </table>`;
  }

  static styles = css`
    :host {
      display: block;
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
    tbody th {
      font-weight: 400;
      width: 8em;
    }
    tr.today th {
      font-weight: 500;
      color: var(--primary-color);
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
    .now-line {
      position: absolute;
      top: -2px;
      bottom: -2px;
      width: 2px;
      margin-left: -1px;
      background: var(--error-color);
      border-radius: 1px;
      pointer-events: none;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
  `;
}

if (!customElements.get("weishaupt-week-grid")) customElements.define("weishaupt-week-grid", WeishauptWeekGrid);
