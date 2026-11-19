// What the panel receives: the custom-panel contract of Home Assistant (only `hass`, `narrow`, `route`, `panel`)
// and the answers of the integration's WebSocket commands (custom_components/weishaupt/panel.py).

export type Labels = Record<string, string>; // language -> text, "en" always present

export interface HassEntityState {
  state: string;
  attributes: Record<string, unknown>;
}

export interface Hass {
  language: string;
  states: Record<string, HassEntityState>;
  user?: { is_admin: boolean };
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  connection: {
    subscribeMessage<T>(callback: (event: T) => void, message: Record<string, unknown>): Promise<() => void>;
  };
}

export interface Installation {
  entry_id: string;
  title: string;
}

export interface Row {
  key: string;
  message: string;
  index: number;
  menu: string;
  kind: string;
  label: Labels;
  description: Labels | null;
  unit: string | null;
  type: string;
  values: Record<string, Labels> | null; // ebusd name of a value-list entry -> its labels
  range: { min: number | null; max: number | null; step: number | null } | null;
  writable: Writable | null;
  messages: string[]; // messages that read this register: the first with a reading is shown
  read: boolean;
  passive: boolean;
  absent: number | null; // the value the device sends when the sensor is not fitted
  entity_id: string | null;
}

export interface Writable {
  risk: string;
  source: string;
  proof: string;
  through: string | null;
  key: string; // the message the writer knows the setting by
  offered: boolean; // this installation offers the write (writes enabled, definition loaded, a range)
  why_not: string | null;
  register: string | null;
  address: string | null;
  minimum: number | null;
  maximum: number | null;
  step: number | null;
  options: { raw: number; name: string; label: Labels }[] | null; // a choice
}

/** The answer of a write command. */
export interface WriteAnswer {
  status: "written" | "confirm" | "refused";
  // confirm
  pending_id?: string;
  kind?: "setting" | "clock";
  placeholders?: Record<string, string>;
  // refused
  code?: string;
  message?: string;
  // written
  result?: string;
  result_text?: string;
  before?: string | null;
  after?: string;
  read_back?: string | null;
  frame?: string | null;
  requested?: string;
  late?: number | null;
  written?: number;
  unchanged?: number;
  days?: Record<string, { before?: string; after?: string; frames?: string[]; result?: string; result_text?: string }>;
  guard?: { switch: boolean; writes_last_hour: number; max_per_hour: number };
}

export interface Menu {
  id: string;
  parent: string;
  label: Labels;
}

export interface Program {
  key: string;
  label: Labels;
  writable: boolean;
  read: boolean;
  listened: boolean; // an enabled entity reads its slots
  slots: number;
  entity_id: string | null;
}

export interface Device {
  id: string;
  type: string;
  label: Labels;
  addresses: string[];
  software: string | null;
  hardware: string | null;
  menus: Menu[];
  rows: Row[];
  programs: Program[];
}

export interface Tree {
  entry_id: string;
  title: string;
  ebusd: { version: string | null; available: boolean; own_address: string | null };
  definitions: {
    version: string;
    commit: string;
    source: string;
    refused: Record<string, string>;
    named_from_metadata: { entity_id: string; disabled: boolean }[];
    not_named: string[];
    mismatches: { key: string; reason: string; detail: string }[];
    messages: number;
    usable: number;
    not_usable: { key: string; reason: string }[];
  };
  writes: {
    switch: boolean;
    capability: string;
    writes_last_hour: number;
    max_per_hour: number;
    switch_entity_id: string | null;
    clock_writable: boolean;
    read_only: { key: string; reason: string }[]; // settings with write conditions left read-only, and why
  } | null;
  clock: { entity_id: string | null; set_entity_id: string | null };
  unknown_addresses: string[];
  devices: Device[];
}

export interface Reading {
  values: string[];
  when: number; // seconds since the epoch, on Home Assistant's clock
  kept?: boolean; // kept across a reload of the entry, not read again yet
}

export type Days = Record<string, string[][] | null>; // "1" (Monday) … "7" -> [[from, to], …], null while unread

export interface LiveEvent {
  now: number;
  reloaded?: boolean; // the entry unloaded: ask the new one
  available?: boolean;
  readings?: Record<string, Reading | null>;
  programs?: Record<string, Days>;
}
