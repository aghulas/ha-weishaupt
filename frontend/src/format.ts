// Pure functions of the panel: the words of the interface, values, ages, ranges, the week grid.
// No Lit and no DOM here, so that `node --test` runs them as they are.

import type { Estimate, Labels, Reading, Row, Tree } from "./types.ts";

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
    write_hint: "Change a setting with its button Change (the writes switch must be on). Comfort: written at once and read back; regulation: after a confirmation in this panel. Open shows the entity.",
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
    edit: "Change",
    write_now: "Write",
    cancel: "Cancel",
    confirm: "Write to the controller",
    confirm_clock: "Send the time",
    confirm_title: "Confirm: {setting} — {device}",
    current: "Current value",
    new_value: "New value",
    allowed: "Allowed",
    path: "Written to bus address {address}, register {register}, from source address {source} ({source_text}). Read back right after.",
    path_short: "bus address {address}, register {register}, from {source}",
    regulation_note: "This setting changes how the heating is regulated: it is written after your confirmation.",
    comfort_note: "Comfort setting: written at once and read back.",
    writing: "Writing…",
    written_line: "{before} → {after}{frame}: {result}",
    not_written: "Not written: {message}",
    not_offered_writes_disabled: "writes are not enabled in the options",
    not_offered: "not offered on this installation: {reason}",
    switch_off_hint: "The writes switch is off: turn it on to write.",
    edit_days: "Edit",
    write_days: "Write the changed days",
    discard: "Discard changes",
    copy_to: "Copy to",
    copy: "Copy",
    cost: "{days} days changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",
    cost_one: "1 day changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",
    interrupted: "no answer from Home Assistant (connection interrupted): the write may or may not have been sent; check the value read back",
    drag_hint: "Type the ranges, or drag on the bar to add one in quarters of an hour; a click on a range removes it.",
    day_format: "use HH:MM-HH:MM, up to three ranges, or -",
    day_quarter: "times must be quarters of an hour, from 00:00 to 24:00",
    day_order: "a range must end after it starts",
    day_too_many: "at most three ranges",
    day_overlap: "ranges must not overlap",
    set_clock: "Set the clock",
    clock_confirm: "Will send Home Assistant's time at second 00 of the next minute ({send_at}), to bus address fe from source address 31. If the bus is not free within {late} s of second 00, nothing is sent.",
    clock_sent: "Sent {requested} ({frame}): {result}",
    clock_current: "Clock master now: {current}",
    col_device: "Device",
    col_menu: "Menu",
    col_label: "Setting",
    col_value: "Value",
    col_unit: "Unit",
    col_range: "Range (step) or choices",
    col_writable: "Writable",
    report: "Printable report",
    export_csv: "Export CSV",
    report_title: "Settings of the installation",
    report_subtitle: "{date} · definitions {version} · read by the Weishaupt integration of Home Assistant",
    report_no_factory: "Factory values: the definitions do not carry them yet. An empty value was not read when the report was made.",
    report_blocked: "The browser blocked the report window: allow pop-ups for Home Assistant and try again.",
    faults: "Faults",
    fault_history: "Fault history",
    fault_counters: "Fault counters",
    fault_log: "Fault log of the system manager (selected entry)",
    fault_code: "Code",
    fault_text: "Text",
    fault_slot: "Slot",
    fault_values: "Values stored with it",
    fault_number: "Fault",
    fault_count: "Count",
    fault_none: "no fault stored",
    fault_unordered: "Order unknown: the pointer to the last entry is not read.",
    fault_no_time: "The boiler stores no time with an entry.",
    fault_log_fields: "Entry {id}: code {code}, type {type}, origin {device}, {time}",
    fault_log_hint: "The operating unit of the system manager selects the entry shown; selecting another one is a write, which the panel does not do.",
    faults_unread: "{n} of these messages are read by no enabled entity.",
    faults_read_once: "Read once on demand: not kept up to date unless their entities are enabled.",
    read_nothing: "Nothing to request: these messages are already read by enabled entities or waiting.",
    read_queued_one: "1 request queued (about {s} s).",
    read_queued_n: "{n} requests queued (about {s} s).",
    read_after_first_pass: "They come after the first pass that follows a start: {n} reads still due, {wait}.",
    read_after_queue: "They come after {n} reads already due, {wait}.",
    about_s: "about {n} s",
    about_min: "about {n} min",
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
    write_hint: "Modifiez un réglage avec son bouton Modifier (l'interrupteur d'écriture doit être allumé). Confort : écrit aussitôt et relu ; régulation : après une confirmation dans ce panneau. Ouvrir affiche l'entité.",
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
    edit: "Modifier",
    write_now: "Écrire",
    cancel: "Annuler",
    confirm: "Écrire dans le régulateur",
    confirm_clock: "Envoyer l'heure",
    confirm_title: "Confirmer : {setting} — {device}",
    current: "Valeur actuelle",
    new_value: "Nouvelle valeur",
    allowed: "Valeurs autorisées",
    path: "Écrit à l'adresse de bus {address}, registre {register}, depuis l'adresse source {source} ({source_text}). Relu juste après.",
    path_short: "adresse de bus {address}, registre {register}, depuis {source}",
    regulation_note: "Ce réglage modifie la régulation du chauffage : il est écrit après votre confirmation.",
    comfort_note: "Réglage de confort : écrit aussitôt et relu.",
    writing: "Écriture…",
    written_line: "{before} → {after}{frame} : {result}",
    not_written: "Non écrit : {message}",
    not_offered_writes_disabled: "l'écriture n'est pas activée dans les options",
    not_offered: "non proposé sur cette installation : {reason}",
    switch_off_hint: "L'interrupteur d'écriture est éteint : allumez-le pour écrire.",
    edit_days: "Modifier",
    write_days: "Écrire les jours modifiés",
    discard: "Abandonner les modifications",
    copy_to: "Copier vers",
    copy: "Copier",
    cost: "{days} jours modifiés : jusqu'à {writes} écritures (seuls les créneaux changés sont écrits) ; {used} sur {max} cette heure",
    cost_one: "1 jour modifié : jusqu'à {writes} écritures (seuls les créneaux changés sont écrits) ; {used} sur {max} cette heure",
    interrupted: "pas de réponse de Home Assistant (connexion interrompue) : l'écriture a pu partir ou non ; vérifiez la valeur relue",
    drag_hint: "Saisissez les plages, ou glissez sur la barre pour en ajouter une au quart d'heure ; un clic sur une plage la retire.",
    day_format: "écrivez HH:MM-HH:MM, trois plages au plus, ou -",
    day_quarter: "les heures doivent être des quarts d'heure, de 00:00 à 24:00",
    day_order: "une plage doit finir après son début",
    day_too_many: "trois plages au plus",
    day_overlap: "les plages ne doivent pas se chevaucher",
    set_clock: "Mettre à l'heure",
    clock_confirm: "Enverra l'heure de Home Assistant à la seconde 00 de la minute suivante ({send_at}), à l'adresse de bus fe depuis l'adresse source 31. Si le bus n'est pas libre dans les {late} s après la seconde 00, rien n'est envoyé.",
    clock_sent: "Envoyé {requested} ({frame}) : {result}",
    clock_current: "Horloge maîtresse maintenant : {current}",
    col_device: "Appareil",
    col_menu: "Menu",
    col_label: "Réglage",
    col_value: "Valeur",
    col_unit: "Unité",
    col_range: "Plage (pas) ou choix",
    col_writable: "Inscriptible",
    report: "Rapport imprimable",
    export_csv: "Exporter en CSV",
    report_title: "Réglages de l'installation",
    report_subtitle: "{date} · définitions {version} · lus par l'intégration Weishaupt de Home Assistant",
    report_no_factory: "Valeurs d'usine : les définitions ne les donnent pas encore. Une valeur vide n'était pas lue au moment du rapport.",
    report_blocked: "Le navigateur a bloqué la fenêtre du rapport : autorisez les fenêtres pour Home Assistant et réessayez.",
    faults: "Défauts",
    fault_history: "Mémoire de défauts",
    fault_counters: "Compteurs de défauts",
    fault_log: "Journal de défauts du manager système (entrée sélectionnée)",
    fault_code: "Code",
    fault_text: "Texte",
    fault_slot: "Emplacement",
    fault_values: "Valeurs enregistrées avec lui",
    fault_number: "Défaut",
    fault_count: "Nombre",
    fault_none: "aucun défaut enregistré",
    fault_unordered: "Ordre inconnu : le pointeur de la dernière entrée n'est pas lu.",
    fault_no_time: "La chaudière n'enregistre pas d'heure avec une entrée.",
    fault_log_fields: "Entrée {id} : code {code}, type {type}, origine {device}, {time}",
    fault_log_hint: "Le tableau de commande du manager système choisit l'entrée affichée ; en choisir une autre est une écriture, que le panneau ne fait pas.",
    faults_unread: "{n} de ces messages ne sont lus par aucune entité activée.",
    faults_read_once: "Lus une fois à la demande : pas tenus à jour tant que leurs entités ne sont pas activées.",
    read_nothing: "Rien à demander : ces messages sont déjà lus par des entités activées ou en attente.",
    read_queued_one: "1 requête en file (environ {s} s).",
    read_queued_n: "{n} requêtes en file (environ {s} s).",
    read_after_first_pass: "Elles passent après la première lecture qui suit un démarrage : {n} lectures encore dues, {wait}.",
    read_after_queue: "Elles passent après {n} lectures déjà dues, {wait}.",
    about_s: "environ {n} s",
    about_min: "environ {n} min",
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

/** What the edit field of a setting starts with: only ever the value read from the device (a choice: its raw
 * value). Nothing read yet, or not available: an empty field, and Write stays disabled until a value is entered. */
export function initialDraft(row: Row, reading: Reading | null | undefined): string {
  const raw = reading?.values[row.index];
  if (raw === undefined || raw === "" || raw === NOT_AVAILABLE) return "";
  const options = row.writable?.options;
  if (options) {
    const found = options.find((o) => o.name === raw);
    return found ? String(found.raw) : "";
  }
  return Number.isNaN(Number(raw)) ? "" : raw;
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

/** A number in the language's way: decimal comma in French, and a real minus sign (−10, not -10). */
export function formatNumber(value: number, language: string): string {
  return new Intl.NumberFormat(language === "fr" ? "fr-FR" : "en-GB", { maximumFractionDigits: 3, useGrouping: false })
    .format(value)
    .replace("-", "\u2212");
}

/** The range of a setting: `−10 … −1 °C (0,5)`. A choice has none (its entries are its allowed values). */
export function rangeText(
  range: { min: number | null; max: number | null; step: number | null } | null | undefined,
  unit: string | null,
  language: string,
): string {
  if (!range || (range.min == null && range.max == null)) return "";
  const n = (v: number | null): string => (v == null ? "…" : formatNumber(v, language));
  const bounds = `${n(range.min)} … ${n(range.max)}${unit ? ` ${unit}` : ""}`;
  return range.step ? `${bounds} (${formatNumber(range.step, language)})` : bounds;
}

export function formatRange(row: Row, language = "en"): string {
  if (row.values || row.writable?.options) return ""; // a choice: no numeric range
  return rangeText(row.range, row.unit, language);
}

export const SLOTS = 3; // ranges a day holds
export const QUARTER = 15;

/** A day as typed (`06:30-18:00, 19:00-21:00`, `-` or nothing for none) -> its ranges in minutes, sorted, or the
 * key of what is wrong (the integration checks it again and has the last word). */
export function parseDay(text: string): { ranges: [number, number][] } | { error: string } {
  const trimmed = text.trim();
  if (trimmed === "" || trimmed === "-") return { ranges: [] };
  const ranges: [number, number][] = [];
  for (const part of trimmed.split(",")) {
    const match = /^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$/.exec(part);
    if (!match) return { error: "day_format" };
    const [h1, m1, h2, m2] = match.slice(1).map(Number);
    const start = h1 * 60 + m1;
    const end = h2 * 60 + m2;
    if ([m1, m2].some((m) => m % QUARTER) || start > 1440 || end > 1440 || m1 > 45 || m2 > 45) {
      return { error: "day_quarter" };
    }
    if (start >= end) return { error: "day_order" };
    ranges.push([start, end]);
  }
  if (ranges.length > SLOTS) return { error: "day_too_many" };
  ranges.sort((a, b) => a[0] - b[0]);
  for (let i = 1; i < ranges.length; i++) if (ranges[i][0] < ranges[i - 1][1]) return { error: "day_overlap" };
  return { ranges };
}

export function clockText(minutesOfDay: number): string {
  const h = Math.floor(minutesOfDay / 60);
  const m = minutesOfDay % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

/** Ranges in minutes -> the text of a day, as the integration writes it. */
export function formatDay(ranges: [number, number][]): string {
  return ranges.length ? ranges.map(([a, b]) => `${clockText(a)}-${clockText(b)}`).join(", ") : "-";
}

/** A range dragged on the bar of a day (from and to as fractions of the day, either order), in quarters of an
 * hour, added to the day: ranges it overlaps are merged into it. Null when the day would hold more than three. */
export function addDragged(ranges: [number, number][], from: number, to: number): [number, number][] | null {
  const q = (f: number): number => Math.round((Math.min(1, Math.max(0, f)) * 1440) / QUARTER) * QUARTER;
  let start = Math.min(q(from), q(to));
  let end = Math.max(q(from), q(to));
  if (end === start) end = Math.min(1440, start + 60); // a click: one hour
  const kept: [number, number][] = [];
  for (const [a, b] of ranges) {
    if (a <= end && b >= start) {
      start = Math.min(start, a);
      end = Math.max(end, b);
    } else kept.push([a, b]);
  }
  const out = [...kept, [start, end] as [number, number]].sort((x, y) => x[0] - y[0]);
  return out.length > SLOTS ? null : out;
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

// ---- the report of the settings and its CSV ---------------------------------------------------------------------

export interface ReportRow {
  device: string;
  menu: string;
  label: string;
  value: string;
  unit: string;
  range: string;
  writable: string;
}

/** Every setting of the installation, device by device in the order of the menus: device, menu (with its parent
 * menus), label, value as read (empty when not read), unit, range and step, writable (and its class) or not. The
 * definitions carry no factory values yet: the report says so instead of a column. */
export function reportRows(tree: Tree, readings: Record<string, Reading | null>, language: string): ReportRow[] {
  const out: ReportRow[] = [];
  for (const device of tree.devices) {
    const menus = new Map(device.menus.map((m) => [m.id, m]));
    const path = (id: string): string => {
      const names: string[] = [];
      for (let menu = menus.get(id); menu; menu = menus.get(menu.parent)) names.unshift(label(menu.label, language));
      return names.join(" › ");
    };
    const order = new Map(menuTree(device.menus).map(([m], i) => [m.id, i]));
    const rows = device.rows
      .filter((row) => row.kind === "setting")
      .sort((a, b) => (order.get(a.menu) ?? 999) - (order.get(b.menu) ?? 999));
    for (const row of rows) {
      const reading = readingOf(row, readings);
      const raw = reading?.values[row.index];
      // a blank never stands for a value: a value not read says why, as the panel does
      let value: string;
      if (raw === undefined) value = t(language, missingReason(row));
      else if (raw === NOT_AVAILABLE) value = t(language, "not_available");
      else value = row.values ? label(row.values[raw], language) || raw : raw;
      const choice = row.values || row.writable?.options;
      const range = row.writable?.minimum != null
        ? { min: row.writable.minimum, max: row.writable.maximum, step: row.writable.step }
        : row.range;
      const allowed = row.writable?.options
        ? row.writable.options.map((o) => label(o.label, language)).join(", ")
        : row.values
          ? Object.values(row.values).map((v) => label(v, language)).join(", ")
          : "";
      out.push({
        device: label(device.label, language),
        menu: path(row.menu),
        label: label(row.label, language),
        value,
        unit: row.values ? "" : (row.unit ?? ""),
        range: choice ? allowed : rangeText(range, null, language),
        writable: row.writable ? t(language, row.writable.risk) : t(language, "read_only"),
      });
    }
  }
  return out;
}

const COLUMNS: (keyof ReportRow)[] = ["device", "menu", "label", "value", "unit", "range", "writable"];

export function reportHeaders(language: string): string[] {
  return COLUMNS.map((c) => t(language, `col_${c}`));
}

/** The rows as CSV: comma-separated in English, semicolon-separated in French (as spreadsheets of that language
 * expect, the comma being the decimal separator there; values keep the device's decimal point), quoted, with a
 * byte-order mark so that spreadsheets read the accents. */
export function toCsv(rows: ReportRow[], language: string): string {
  const separator = language === "fr" ? ";" : ",";
  const quote = (text: string): string =>
    text.includes(separator) || /["\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  const lines = [reportHeaders(language), ...rows.map((row) => COLUMNS.map((c) => row[c]))];
  return "\ufeff" + lines.map((line) => line.map(quote).join(separator)).join("\r\n") + "\r\n";
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
}

/** A self-contained page of the report, printed by the browser: a table per device, headers repeated on each
 * printed page, no colour needed. */
export function reportHtml(rows: ReportRow[], language: string, heading: { title: string; subtitle: string }): string {
  const devices = [...new Set(rows.map((r) => r.device))];
  const columns = COLUMNS.filter((c) => c !== "device");
  const headers = reportHeaders(language).slice(1);
  const tables = devices.map((device) => `<section><h2>${escapeHtml(device)}</h2><table><thead><tr>${headers
    .map((h) => `<th>${escapeHtml(h)}</th>`).join("")}</tr></thead><tbody>${rows
    .filter((r) => r.device === device)
    .map((r) => `<tr>${columns.map((c) => `<td>${escapeHtml(r[c])}</td>`).join("")}</tr>`).join("")}</tbody></table></section>`);
  return `<!doctype html><html lang="${language}"><head><meta charset="utf-8"><title>${escapeHtml(heading.title)}</title>
<style>
@page{size:A4;margin:15mm 12mm}
body{font:10pt system-ui,sans-serif;margin:16px;color:#000;background:#fff}
h1{font-size:15pt;margin:0 0 4px}h2{font-size:12pt;margin:16px 0 6px}p{margin:0 0 8px;color:#333}
table{border-collapse:collapse;width:100%;table-layout:auto}
th,td{border:1px solid #999;padding:4px 7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#eee}thead{display:table-header-group}tfoot{display:table-footer-group}
tr,td,th{break-inside:avoid;page-break-inside:avoid}
@media print{body{margin:0}h2{break-after:avoid;page-break-after:avoid}th{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style></head><body><h1>${escapeHtml(heading.title)}</h1><p>${escapeHtml(heading.subtitle)}</p>${tables.join("")}
<p>${escapeHtml(t(language, "report_no_factory"))}</p></body></html>`;
}

/** What a "Read now" queued: only the requests really sent, their time, and the reads already waiting before them
 * (the first pass after a start, the reader's queue). */
export function queuedText(estimate: Estimate, language: string): string {
  if (estimate.queued === 0) return t(language, "read_nothing");
  const own = t(language, estimate.queued === 1 ? "read_queued_one" : "read_queued_n", {
    n: estimate.queued, s: estimate.seconds,
  });
  if (estimate.ahead === 0) return own;
  const minutes = estimate.wait >= 90 ? Math.round(estimate.wait / 60) : 0;
  const wait = minutes ? t(language, "about_min", { n: minutes }) : t(language, "about_s", { n: estimate.wait });
  return `${own} ${t(language, estimate.first_pass ? "read_after_first_pass" : "read_after_queue", {
    n: estimate.ahead, wait,
  })}`;
}
