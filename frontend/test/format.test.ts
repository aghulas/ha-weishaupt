// The pure functions of the panel, run by `node --test` on the TypeScript sources (type stripping).
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  addDragged, initialDraft, queuedText, isoWeekday, isProgramSensor, weekFromAttributes, reportHtml, reportRows, toCsv, bars, formatAge, formatDay, parseDay, formatRange, formatValue, languageOf, menuTree, missingReason, notUsable, readingOf, redundant,
  STRINGS, t,
} from "../src/format.ts";
import type { Row, Tree } from "../src/types.ts";

const row = (extra: Partial<Row> = {}): Row => ({
  key: "em2/RoomNormalTemp/value", message: "em2/RoomNormalTemp", index: 0, menu: "settings", kind: "setting",
  label: { en: "Normal room temperature", fr: "Température ambiante normale" }, description: null, unit: "°C",
  type: "UIN", values: null, range: { min: 16, max: 35, step: 0.5 }, writable: null, read: true, passive: false,
  entity_id: "number.x", messages: ["em2/RoomNormalTemp"], absent: null, ...extra,
});

test("both languages have the same words", () => {
  assert.deepEqual(Object.keys(STRINGS.fr).sort(), Object.keys(STRINGS.en).sort());
});

test("language: base of a regional code, English for any other", () => {
  assert.equal(languageOf("fr-CA"), "fr");
  assert.equal(languageOf("de"), "en");
  assert.equal(languageOf(undefined), "en");
  assert.equal(t("fr", "seconds_ago", { n: 5 }), "il y a 5 s");
});

test("values: unit, value-list label, not available, unread", () => {
  assert.equal(formatValue(row(), { values: ["21.5"], when: 0 }, "en"), "21.5 °C");
  const list = row({ unit: null, values: { Monday: { en: "Monday", fr: "Lundi" } } });
  assert.equal(formatValue(list, { values: ["Monday"], when: 0 }, "fr"), "Lundi");
  assert.equal(formatValue(row(), { values: ["-"], when: 0 }, "fr"), "non disponible");
  assert.equal(formatValue(row(), undefined, "en"), null);
});

test("a description that repeats the name is not shown", () => {
  assert.ok(redundant("température de départ (valeur d'information i35)", "Température de départ (i35)"));
  assert.ok(!redundant("consigne de température ambiante normale", "Température ambiante normale"));
  assert.ok(redundant("", "x"));
});

test("absent sensor, register read by two messages, messages not read", () => {
  const boiler = row({ absent: -40, messages: ["bc1/DHWTemp"], message: "bc1/DHWTemp" });
  assert.equal(formatValue(boiler, { values: ["-40.0"], when: 0 }, "fr"), "pas de sonde");
  assert.equal(formatValue(boiler, { values: ["-39.5"], when: 0 }, "en"), "-39.5 °C");
  const twin = row({ messages: ["ka/RoomNormalTemp", "em1/RoomNormalTemp"] });
  assert.deepEqual(readingOf(twin, { "em1/RoomNormalTemp": { values: ["20.0"], when: 1 } }), { values: ["20.0"], when: 1 });
  assert.deepEqual(notUsable([
    { key: "broadcast/Datetime", reason: "write_only" }, { key: "em3/A", reason: "device_absent" },
    { key: "em3/B", reason: "device_absent" },
  ], "en"), ["broadcast/Datetime: write only", "em3: 2 messages, device not on the bus"]);
});

test("why a row has no value", () => {
  assert.equal(missingReason(row({ read: false })), "not_loaded");
  assert.equal(missingReason(row({ entity_id: null })), "not_listened");
  assert.equal(missingReason(row({ entity_id: null, passive: true })), "waiting");
  assert.equal(missingReason(row()), "waiting");
});

test("ages and ranges", () => {
  assert.equal(formatAge(42, "en"), "42 s ago");
  assert.equal(formatAge(600, "fr"), "il y a 10 min");
  assert.equal(formatAge(7200, "en"), "2 h ago");
  assert.equal(formatRange(row()), "16 … 35 °C (0.5)");
  assert.equal(formatRange(row({ range: { min: -10, max: -1, step: 0.5 } }), "fr"), "\u221210 … \u22121 °C (0,5)");
  assert.equal(formatRange(row({ values: { Off: { en: "Off" } }, range: { min: 0, max: 7, step: 1 } })), "");
  assert.equal(formatRange(row({ range: null })), "");
});

test("week grid bars in percent of the day", () => {
  assert.deepEqual(bars([["06:00", "18:00"]]), [{ left: 25, width: 50, text: "06:00-18:00" }]);
  assert.equal(bars([["00:00", "24:00"]])[0].width, 100);
});

test("menus as a tree, children after their parent", () => {
  const menus = [
    { id: "info", parent: "" }, { id: "process", parent: "" }, { id: "info_sensors", parent: "info" },
    { id: "orphan", parent: "gone" },
  ];
  assert.deepEqual(menuTree(menus).map(([m, d]) => `${m.id}:${d}`), ["info:0", "info_sensors:1", "process:0", "orphan:0"]);
});

test("a typed day: ranges in minutes, or what is wrong", () => {
  assert.deepEqual(parseDay("06:30-18:00, 19:00-21:00"), { ranges: [[390, 1080], [1140, 1260]] });
  assert.deepEqual(parseDay(" - "), { ranges: [] });
  assert.deepEqual(parseDay("2h-3h"), { error: "day_format" });
  assert.deepEqual(parseDay("06:10-07:00"), { error: "day_quarter" });
  assert.deepEqual(parseDay("08:00-07:00"), { error: "day_order" });
  assert.deepEqual(parseDay("01:00-02:00, 03:00-04:00, 05:00-06:00, 07:00-08:00"), { error: "day_too_many" });
  assert.deepEqual(parseDay("01:00-03:00, 02:00-04:00"), { error: "day_overlap" });
  assert.equal(formatDay([[390, 1080], [1140, 1440]]), "06:30-18:00, 19:00-24:00");
  assert.equal(formatDay([]), "-");
});

test("a dragged range: quarters of an hour, merged with what it overlaps, three at most", () => {
  assert.deepEqual(addDragged([], 0.25, 0.5), [[360, 720]]);
  assert.deepEqual(addDragged([], 0.5, 0.25), [[360, 720]]); // dragged leftwards
  assert.deepEqual(addDragged([[360, 720]], 0.45, 0.6), [[360, 870]]); // merged
  assert.deepEqual(addDragged([], 0.2501, 0.2501), [[360, 420]]); // a click: one hour
  assert.equal(addDragged([[0, 60], [120, 180], [240, 300]], 0.8, 0.9), null);
});

test("the edit field starts with the value read, never with the minimum", () => {
  const writable = {
    risk: "comfort", source: "ff", proof: "", through: null, key: "em2/RoomSetbackTemp", offered: true, why_not: null,
    register: "05 65", address: "51", minimum: 10, maximum: 21.5, step: 0.5, options: null,
  };
  const setback = row({ writable });
  assert.equal(initialDraft(setback, { values: ["16.5"], when: 0 }), "16.5");
  assert.equal(initialDraft(setback, undefined), ""); // not read yet: empty, not "10"
  assert.equal(initialDraft(setback, null), "");
  assert.equal(initialDraft(setback, { values: ["-"], when: 0 }), "");
  const choice = row({ writable: { ...writable, options: [{ raw: 0, name: "Off", label: { en: "Off" } },
    { raw: 1, name: "Monday", label: { en: "Monday" } }] } });
  assert.equal(initialDraft(choice, { values: ["Monday"], when: 0 }), "1");
  assert.equal(initialDraft(choice, undefined), ""); // not the first entry of the list
});

test("the report: settings only, in the order of the menus, values as read, CSV by language", () => {
  const setting = (extra: Partial<Row>): Row => row({ kind: "setting", ...extra });
  const tree = {
    devices: [{
      id: "module2", type: "module", label: { en: "Heating module 2", fr: "Module de chauffage 2" }, addresses: ["51"],
      software: null, hardware: null, programs: [],
      menus: [{ id: "info", parent: "", label: { en: "Info", fr: "Info" } },
        { id: "settings", parent: "", label: { en: "Settings", fr: "Réglage" } },
        { id: "holiday", parent: "settings", label: { en: "Holiday", fr: "Congés" } }],
      rows: [
        setting({ key: "a", message: "em2/HolidayLevel", messages: ["em2/HolidayLevel"], menu: "holiday", unit: null, range: null,
          label: { en: "Holiday level", fr: "Niveau, vacances" },
          values: { Setback: { en: "Setback", fr: "Réduit" } } }),
        setting({ key: "b", message: "em2/RoomNormalTemp", menu: "settings" }),
        row({ key: "c", message: "em2/FlowTemp", menu: "info", kind: "live" }),
      ],
    }],
  } as unknown as Tree;
  const readings = { "em2/RoomNormalTemp": { values: ["21.5"], when: 0 }, "em2/HolidayLevel": { values: ["Setback"], when: 0 } };
  const rows = reportRows(tree, readings, "fr");
  assert.deepEqual(rows.map((r) => [r.menu, r.label, r.value, r.unit]), [
    ["Réglage", "Température ambiante normale", "21.5", "°C"],
    ["Réglage › Congés", "Niveau, vacances", "Réduit", ""],
  ]);
  assert.equal(rows[0].range, "16 … 35 (0,5)");
  assert.equal(rows[1].range, "Réduit"); // a choice: its entries, not "0 … 7 (1)"
  const csv = toCsv(rows, "fr");
  assert.ok(csv.startsWith("\ufeffAppareil;Menu;Réglage;Valeur;Unité;Plage (pas) ou choix;Inscriptible\r\n"));
  assert.ok(csv.includes("Module de chauffage 2;Réglage;Température ambiante normale;21.5;°C;16 … 35 (0,5);lecture seule"));
  // a setting not read: its reason, never a blank
  assert.equal(reportRows(tree, {}, "fr")[0].value, "en attente de la première lecture");
  assert.ok(toCsv(reportRows(tree, readings, "en"), "en").includes("Heating module 2,Settings,Normal room temperature,21.5"));
  assert.ok(toCsv([{ ...rows[0], label: 'a "b"; c' }], "fr").includes('"a ""b""; c"'));
  const page = reportHtml(rows, "fr", { title: "Réglages <x>", subtitle: "s" });
  assert.ok(page.includes("<h2>Module de chauffage 2</h2>") && page.includes("Réglages &lt;x&gt;"));
  assert.ok(page.includes("@media print"));
});

test("the estimate of a Read now: only what is requested, and what it waits behind", () => {
  assert.equal(queuedText({ queued: 7, seconds: 15, ahead: 0, wait: 0, first_pass: false }, "en"),
    "7 requests queued (about 15 s).");
  assert.equal(queuedText({ queued: 7, seconds: 15, ahead: 95, wait: 200, first_pass: true }, "fr"),
    "7 requêtes en file (environ 15 s). Elles passent après la première lecture qui suit un démarrage : 95 lectures encore dues, environ 3 min.");
  assert.equal(queuedText({ queued: 1, seconds: 2, ahead: 4, wait: 8, first_pass: false }, "en"),
    "1 request queued (about 2 s). They come after 4 reads already due, about 8 s.");
  assert.ok(queuedText({ queued: 0, seconds: 0, ahead: 0, wait: 0, first_pass: false }, "en").startsWith("Nothing"));
});

test("the card: a program sensor's attributes as the week grid", () => {
  const week = weekFromAttributes({ monday: "06:30-18:00, 19:00-21:00", tuesday: "-", friendly_name: "x" });
  assert.deepEqual(week["1"], [["06:30", "18:00"], ["19:00", "21:00"]]);
  assert.deepEqual(week["2"], []); // no range
  assert.equal(week["3"], null); // not read yet
  assert.equal(weekFromAttributes({ monday: "garbage" })["1"], null);
});

test("the card: which states are program sensors, and today", () => {
  const all = Object.fromEntries(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    .map((d) => [d, "-"]));
  assert.ok(isProgramSensor("sensor.room_unit_1_heating_program_1", all));
  assert.ok(isProgramSensor("sensor.room_unit_1_heating_program_1", {})); // not read yet
  assert.ok(!isProgramSensor("sensor.boiler_1_flow_temperature", {}));
  assert.ok(!isProgramSensor("text.room_unit_1_heating_program_1_monday_setting", all));
  assert.ok(isProgramSensor("sensor.room_unit_1_heating_program_1", { monday: "-", friendly_name: "x" })); // partly read
  assert.ok(!isProgramSensor("sensor.boiler_1_x", { monday: "-", unit_of_measurement: "°C" }));
  assert.equal(isoWeekday(new Date(2026, 10, 16)), 1); // a Monday
  assert.equal(isoWeekday(new Date(2026, 10, 22)), 7); // a Sunday
});
