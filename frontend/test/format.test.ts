// The pure functions of the panel, run by `node --test` on the TypeScript sources (type stripping).
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  addDragged, bars, formatAge, formatDay, parseDay, formatRange, formatValue, languageOf, menuTree, missingReason, notUsable, readingOf, redundant,
  STRINGS, t,
} from "../src/format.ts";
import type { Row } from "../src/types.ts";

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
  assert.equal(formatRange(row()), "16 – 35 °C (0.5)");
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
