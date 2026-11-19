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
    caption: { type: String },
  };

  declare days: Days | undefined;
  declare language: string;
  declare unread: string;
  declare today: number;
  declare caption: string;

  constructor() {
    super();
    this.language = "en";
    this.unread = "";
    this.today = 0;
    this.caption = "";
  }

  render(): TemplateResult {
    const lang = this.language;
    const names = WEEKDAYS[lang] ?? WEEKDAYS.en;
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
