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
  writable: { risk: string; source: string; proof: string } | null;
  read: boolean;
  passive: boolean;
  entity_id: string | null;
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
    named_from_metadata: string[];
    not_named: string[];
    mismatches: { key: string; reason: string; detail: string }[];
    messages: number;
    usable: number;
  };
  writes: {
    switch: boolean;
    capability: string;
    writes_last_hour: number;
    max_per_hour: number;
    switch_entity_id: string | null;
  } | null;
  clock: { entity_id: string | null; set_entity_id: string | null };
  unknown_addresses: string[];
  devices: Device[];
}

export interface Reading {
  values: string[];
  when: number; // seconds since the epoch, on Home Assistant's clock
}

export type Days = Record<string, string[][] | null>; // "1" (Monday) … "7" -> [[from, to], …], null while unread

export interface LiveEvent {
  now: number;
  available?: boolean;
  readings?: Record<string, Reading | null>;
  programs?: Record<string, Days>;
}
