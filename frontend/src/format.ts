// Pure functions of the panel: the words of the interface, values, ages, ranges, the week grid.
// No Lit and no DOM here, so that `node --test` runs them as they are.

import type { Labels, Reading, Row } from "./types.ts";

export const NOT_AVAILABLE = "-"; // what ebusd answers for the replacement value of a type

export const STRINGS: Record<string, Record<string, string>> = {
  en: {
    title: "Weishaupt",
    installation: "Installation",
    devices: "Devices",
    definitions: "Definitions",
    programs: "Weekly programs",
    loading: "Loading…",
    no_installation: "No Weishaupt installation is loaded.",
    unavailable: "ebusd does not answer: the values shown are the last ones read.",
    value: "Value",
    name: "Name",
    age: "Read",
    range: "Range",
    write: "Write",
    entity: "Entity",
    open: "Open",
    comfort: "comfort",
    regulation: "regulation",
    read_only: "read only",
    not_loaded: "not loaded by ebusd",
    not_listened: "not read: no enabled entity",
    waiting: "waiting for the first reading",
    not_available: "not available",
    seconds_ago: "{n} s ago",
    minutes_ago: "{n} min ago",
    hours_ago: "{n} h ago",
    days_ago: "{n} d ago",
    passive: "sent by the device",
    clock_offset: "Clock master",
    clock_line: "{label}: {text}",
    clock_ahead: "{n} s ahead",
    clock_behind: "{n} s behind",
    clock_on_time: "on time",
    software: "Software",
    hardware: "Hardware",
    address: "Bus address",
    in_use: "In use",
    source_bundled: "shipped with the integration",
    source_file: "file beside the configuration: {file}",
    refused: "Files not used",
    mismatches: "Differences with ebusd",
    named_from_metadata: "Entities named from the definitions",
    not_named: "Entities waiting for a name",
    messages: "Messages",
    usable: "{usable} of {messages} loaded by ebusd as described",
    writes: "Writes",
    writes_off: "disabled in the options",
    switch_on: "switch on",
    switch_off: "switch off",
    capability: "run-time checksum: {value}",
    per_hour: "{n} of {max} this hour",
    ebusd: "ebusd",
    unknown_addresses: "Addresses answering that no definition knows",
    none: "none",
    day_unread: "not read yet",
    day_none: "no range",
    editable: "editable through its program-day entities",
    not_editable: "read only: not proven writable on this device",
    not_read_program: "not loaded by ebusd",
    program_not_listened: "not read by any enabled entity: read it once now, or enable the program sensor to keep it up to date",
    write_hint: "Changes are made in the entity (button Open); the panel only shows. Comfort: written at once; regulation: after a confirmation in Repairs.",
    description: "Description",
    no_sensor: "no sensor",
    kept: "kept from before the reload, read again soon",
    through: "through {circuit}",
    read_now: "Read now",
    read_cost: "{n} requests to the bus, about {s} s, once",
    read_queued: "{n} requests queued; the grid fills in as they are answered",
    readable: "{usable} of {readable} readable messages loaded by ebusd as described",
    not_usable: "Messages not read",
    reason_write_only: "write only",
    reason_device_absent: "device not on the bus",
    absent_circuit: "{circuit}: {n} messages, device not on the bus",
    reason_mismatch: "not loaded as described",
    reason_other: "not read",
    disabled: "disabled",
    reloading: "The integration was reloaded: loading again…",
    read_only_settings: "Settings left read-only",
  },
  fr: {
    title: "Weishaupt",
    installation: "Installation",
    devices: "Appareils",
    definitions: "Définitions",
    programs: "Programmes hebdomadaires",
    loading: "Chargement…",
    no_installation: "Aucune installation Weishaupt n'est chargée.",
    unavailable: "ebusd ne répond pas : les valeurs affichées sont les dernières lues.",
    value: "Valeur",
    name: "Nom",
    age: "Lu",
    range: "Plage",
    write: "Écriture",
    entity: "Entité",
    open: "Ouvrir",
    comfort: "confort",
    regulation: "régulation",
    read_only: "lecture seule",
    not_loaded: "non chargé par ebusd",
    not_listened: "non lu : aucune entité activée",
    waiting: "en attente de la première lecture",
    not_available: "non disponible",
    seconds_ago: "il y a {n} s",
    minutes_ago: "il y a {n} min",
    hours_ago: "il y a {n} h",
    days_ago: "il y a {n} j",
    passive: "envoyé par l'appareil",
    clock_offset: "Horloge maîtresse",
    clock_line: "{label} : {text}",
    clock_ahead: "{n} s d'avance",
    clock_behind: "{n} s de retard",
    clock_on_time: "à l'heure",
    software: "Logiciel",
    hardware: "Matériel",
    address: "Adresse de bus",
    in_use: "Utilisées",
    source_bundled: "livrées avec l'intégration",
    source_file: "fichier à côté de la configuration : {file}",
    refused: "Fichiers non utilisés",
    mismatches: "Écarts avec ebusd",
    named_from_metadata: "Entités nommées par les définitions",
    not_named: "Entités en attente d'un nom",
    messages: "Messages",
    usable: "{usable} sur {messages} chargés par ebusd comme décrits",
    writes: "Écritures",
    writes_off: "désactivées dans les options",
    switch_on: "interrupteur allumé",
    switch_off: "interrupteur éteint",
    capability: "checksum à l'exécution : {value}",
    per_hour: "{n} sur {max} cette heure",
    ebusd: "ebusd",
    unknown_addresses: "Adresses qui répondent sans définition",
    none: "aucun",
    day_unread: "pas encore lu",
    day_none: "aucune plage",
    editable: "modifiable par ses entités de jour de programme",
    not_editable: "lecture seule : écriture non prouvée sur cet appareil",
    not_read_program: "non chargé par ebusd",
    program_not_listened: "lu par aucune entité activée : lisez-le une fois maintenant, ou activez le capteur du programme pour le tenir à jour",
    write_hint: "Les modifications se font dans l'entité (bouton Ouvrir) ; le panneau ne fait qu'afficher. Confort : écrit aussitôt ; régulation : après une confirmation dans Réparations.",
    description: "Description",
    no_sensor: "pas de sonde",
    kept: "conservée d'avant le rechargement, relue bientôt",
    through: "par {circuit}",
    read_now: "Lire maintenant",
    read_cost: "{n} requêtes sur le bus, environ {s} s, une seule fois",
    read_queued: "{n} requêtes en file ; la grille se remplit au fil des réponses",
    readable: "{usable} sur {readable} messages lisibles chargés par ebusd comme décrits",
    not_usable: "Messages non lus",
    reason_write_only: "écriture seule",
    reason_device_absent: "appareil absent du bus",
    absent_circuit: "{circuit} : {n} messages, appareil absent du bus",
    reason_mismatch: "non chargé comme décrit",
    reason_other: "non lu",
    disabled: "désactivée",
    reloading: "L'intégration a été rechargée : nouveau chargement…",
    read_only_settings: "Réglages laissés en lecture seule",
  },
};

export const WEEKDAYS: Record<string, string[]> = {
  en: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
  fr: ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
};

/** "fr-CA" -> "fr"; any language the panel has no words for -> "en". */
export function languageOf(language: string | undefined): string {
  const base = (language ?? "en").split("-")[0];
  return base in STRINGS ? base : "en";
}

export function t(language: string, key: string, values: Record<string, string | number> = {}): string {
  const text = STRINGS[language]?.[key] ?? STRINGS.en[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, name: string) => String(values[name] ?? `{${name}}`));
}

export function label(labels: Labels | null | undefined, language: string): string {
  if (!labels) return "";
  return labels[language] ?? labels.en ?? Object.values(labels)[0] ?? "";
}

/** The value of a row as the device holds it: a value-list entry by its label, a number with its unit. */
export function formatValue(row: Row, reading: Reading | null | undefined, language: string): string | null {
  if (!reading) return null;
  const raw = reading.values[row.index];
  if (raw === undefined) return null;
  if (raw === NOT_AVAILABLE) return t(language, "not_available");
  if (row.absent !== null && row.absent !== undefined && Number(raw) === row.absent) return t(language, "no_sensor");
  if (row.values) {
    const entry = row.values[raw];
    return entry ? label(entry, language) : raw;
  }
  return row.unit ? `${raw} ${row.unit}` : raw;
}

/** A description that only repeats the name ("température de départ (valeur d'information i35)" under
 * "Température de départ (i35)") is not shown. */
export function redundant(description: string, name: string): boolean {
  const stem = (text: string): string => text.split(" (")[0].trim().toLowerCase();
  return !description || stem(description) === stem(name);
}

/** The reading of a row: of the first of its messages that has one (a register read by two messages). */
export function readingOf(row: Row, readings: Record<string, Reading | null>): Reading | null {
  for (const key of row.messages ?? [row.message]) {
    const found = readings[key];
    if (found) return found;
  }
  return null;
}

/** The messages not read, one line each, except those of a device not on the bus: one line per circuit. */
export function notUsable(items: { key: string; reason: string }[], language: string): string[] {
  const absent = new Map<string, number>();
  const lines: string[] = [];
  for (const item of items) {
    if (item.reason === "device_absent") {
      const circuit = item.key.split("/")[0];
      absent.set(circuit, (absent.get(circuit) ?? 0) + 1);
    } else lines.push(`${item.key}: ${t(language, `reason_${item.reason}`)}`);
  }
  for (const [circuit, n] of absent) lines.push(t(language, "absent_circuit", { circuit, n }));
  return lines;
}

/** Why a row has no value, when it has none. */
export function missingReason(row: Row): string {
  if (!row.read) return "not_loaded";
  if (!row.entity_id && !row.passive) return "not_listened";
  return "waiting";
}

export function formatAge(seconds: number, language: string): string {
  const s = Math.max(0, Math.round(seconds));
  if (s < 90) return t(language, "seconds_ago", { n: s });
  if (s < 90 * 60) return t(language, "minutes_ago", { n: Math.round(s / 60) });
  if (s < 36 * 3600) return t(language, "hours_ago", { n: Math.round(s / 3600) });
  return t(language, "days_ago", { n: Math.round(s / 86400) });
}

export function formatRange(row: Row): string {
  const range = row.range;
  if (!range) return "";
  const unit = row.unit ? ` ${row.unit}` : "";
  const bounds = `${range.min ?? "…"} – ${range.max ?? "…"}${unit}`;
  return range.step ? `${bounds} (${range.step})` : bounds;
}

/** "06:30" -> minutes since midnight; "24:00" -> 1440. */
export function minutes(time: string): number {
  const [h, m] = time.split(":").map((part) => Number(part));
  return h * 60 + (m || 0);
}

/** The bars of a day in the week grid: left and width in percent of the day. */
export function bars(ranges: string[][]): { left: number; width: number; text: string }[] {
  return ranges.map(([from, to]) => {
    const start = minutes(from);
    const end = minutes(to);
    return {
      left: (start / 1440) * 100,
      width: (Math.max(0, end - start) / 1440) * 100,
      text: `${from}-${to}`,
    };
  });
}

/** The menus of a device as a tree in their order: [menu, depth]. */
export function menuTree<M extends { id: string; parent: string }>(menus: M[]): [M, number][] {
  const out: [M, number][] = [];
  const visit = (parent: string, depth: number): void => {
    for (const menu of menus.filter((m) => m.parent === parent)) {
      out.push([menu, depth]);
      visit(menu.id, depth + 1);
    }
  };
  visit("", 0);
  // a menu whose parent is not shown still appears, at the top
  for (const menu of menus) if (!out.some(([m]) => m.id === menu.id)) out.push([menu, 0]);
  return out;
}
