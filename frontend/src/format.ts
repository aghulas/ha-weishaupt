// Pure functions of the panel: the words of the interface, values, ages, ranges, the week grid.
// No Lit and no DOM here, so that `node --test` runs them as they are.

import type { Days, Estimate, Follow, JobProgress, Labels, Reading, RegistryEntry, Row, Tree, VendorCode } from "./types.ts";

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
    mode_follow: "follows the running ebusd ({n} known)",
    mode_pinned: "pinned ({n} known)",
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
    col_code: "Vendor code",
    col_scheme: "Code scheme",
    code: "Code",
    code_title: "{scheme}, document {document}",
    sort_by_code: "Sort by vendor code",
    report_codes: "Vendor codes: {schemes}.",
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
    card_name: "Weishaupt weekly program",
    card_description: "The week grid of one weekly program of a Weishaupt controller.",
    card_no_entity: "Choose a program sensor of the Weishaupt integration in the card's settings.",
    card_missing: "{entity} does not exist, or is disabled: enable it in Settings → Entities (program sensors are created disabled).",
    card_unavailable: "{entity} is unavailable: ebusd or the controller does not answer.",
    card_unread: "not read yet",
    card_editor_entity: "Program sensor",
    card_editor_title: "Title (optional)",
    card_editor_today: "Mark today",
    card_editor_hint: "Program sensors are created disabled: a program not listed here is enabled in Settings → Entities.",
    card_edit: "Edit",
    card_edited_on: "Read from the store of {device}: change this program there.",
    edited_on_program: "Read from the store of {device}: change {program} of {device}; a change sent here would be acknowledged and lost.",
    edited_on_setting: "kept by {device}: changed there",
    stored_only_badge: "stored only",
    stored_only_note: "Stored in this device only: not followed by the installation (hot water follows the system manager).",
    card_type_hint: "Type up to three ranges a day, HH:MM-HH:MM, or - for none; only changed days are written.",
    card_edit_admin: "Days are changed by administrators, here or in the Weishaupt panel.",
    card_not_writable: "This program is not proven writable on its device: read only.",
    card_writing_day: "{day}: writing…",
    card_written_day: "{day}: written and read back",
    card_failed_day: "{day}: not written: {message}",
    card_no_switch: "Writes are not enabled in the options of the integration.",
    read_queued_one: "1 request queued (about {s} s).",
    read_queued_n: "{n} requests queued (about {s} s).",
    read_after_first_pass: "They come after the first pass that follows a start: {n} reads still due, {wait}.",
    read_after_queue: "They come after {n} reads already due, {wait}.",
    about_s: "about {n} s",
    about_min: "about {n} min",
    read_scope_menu: "Read this menu once",
    read_scope_device: "Read this device once",
    read_scope_all: "Read everything once",
    read_scope_hint: "Rows no enabled entity follows are read once, at the pace of the bus, after what the entities wait for.",
    read_price_one: "1 request, {time}.",
    read_price_n: "{n} requests, {time}.",
    read_start: "Start",
    read_stop: "Stop",
    dismiss: "Close",
    job_running: "Reading: {done} of {total} asked, {read} with a value.",
    job_done: "Read once: {read} of {total} with a value. Not kept up to date: follow a row to keep it.",
    job_stopped: "Stopped: {done} of {total} asked, {stopped} withdrawn.",
    job_reload: "The integration reloaded: the reads not yet asked were dropped.",
    read_once: "read once",
    follow: "Follow",
    follow_all: "Follow all",
    follow_none: "Follow none",
    follow_blocked: "disabled by its device",
    follow_pending: "{n} changes to apply: {enable} to follow, {disable} to stop following.",
    follow_reload: "Home Assistant reloads the integration about {s} s after an entity is enabled: the panel reloads with it, and reads under way stop.",
    follow_defaults_off: "{n} of them are followed by default (live values, states, counters): disabled, they are no longer read, their history stops, and dashboards or automations that use them no longer find them.",
    follow_apply: "Apply",
    follow_discard: "Discard",
    follow_done: "{enabled} enabled, {disabled} disabled.",
    follow_reload_soon: "Home Assistant reloads the integration in about {s} s.",
    follow_refused: "{n} not changed: disabled by their device or config entry, or not this integration's.",
    writes_pill_on: "Writes: on ({n}/{max})",
    writes_pill_off: "Writes: locked",
    open_switch: "Open writes switch",
    items_count: "{n} items",
    items_count_one: "1 item",
    fault_hide_zero: "Hide zero counters ({n})",
    fault_all_zero: "All read counters are at 0.",
    copy_all: "every day",
    copy_weekdays: "Monday – Friday",
    copy_weekend: "Saturday, Sunday",
    search_placeholder: "Search settings, sensors, codes, keys…",
    search_clear: "Clear",
    filter_all: "All",
    filter_writable: "Writable",
    filter_followed: "Followed",
    filter_unread: "Unread",
    search_results: "{n} matching rows",
    search_results_one: "1 matching row",
    search_empty: "No row matches this search.",
    bar_remove_hint: "{range} — click to remove",
    clear_day: "Clear",
    follow_details: "Show details ({n})",
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
    mode_follow: "suit l'ebusd en marche ({n} connus)",
    mode_pinned: "fixé ({n} connus)",
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
    col_code: "Code constructeur",
    col_scheme: "Numérotation du code",
    code: "Code",
    code_title: "{scheme}, document {document}",
    sort_by_code: "Trier par code constructeur",
    report_codes: "Codes constructeur : {schemes}.",
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
    card_name: "Programme hebdomadaire Weishaupt",
    card_description: "La grille de la semaine d'un programme hebdomadaire d'un régulateur Weishaupt.",
    card_no_entity: "Choisissez un capteur de programme de l'intégration Weishaupt dans les réglages de la carte.",
    card_missing: "{entity} n'existe pas ou est désactivé : activez-le dans Paramètres → Entités (les capteurs de programme sont créés désactivés).",
    card_unavailable: "{entity} est indisponible : ebusd ou le régulateur ne répond pas.",
    card_unread: "pas encore lu",
    card_editor_entity: "Capteur de programme",
    card_editor_title: "Titre (facultatif)",
    card_editor_today: "Marquer aujourd'hui",
    card_editor_hint: "Les capteurs de programme sont créés désactivés : un programme absent de la liste s'active dans Paramètres → Entités.",
    card_edit: "Modifier",
    card_edited_on: "Lu dans la mémoire de {device} : modifiez ce programme là-bas.",
    edited_on_program: "Lu dans la mémoire de {device} : modifiez {program} de {device} ; une modification envoyée ici serait acquittée puis perdue.",
    edited_on_setting: "tenu par {device} : à modifier là-bas",
    stored_only_badge: "mémorisé uniquement",
    stored_only_note: "Mémorisé dans cet appareil uniquement : non suivi par l'installation (l'ECS suit le manager de cascade).",
    card_type_hint: "Saisissez jusqu'à trois plages par jour, HH:MM-HH:MM, ou - pour aucune ; seuls les jours modifiés sont écrits.",
    card_edit_admin: "Les jours sont modifiés par les administrateurs, ici ou dans le panneau Weishaupt.",
    card_not_writable: "Ce programme n'est pas prouvé inscriptible sur son appareil : lecture seule.",
    card_writing_day: "{day} : écriture…",
    card_written_day: "{day} : écrit et relu",
    card_failed_day: "{day} : non écrit : {message}",
    card_no_switch: "L'écriture n'est pas activée dans les options de l'intégration.",
    read_queued_one: "1 requête en file (environ {s} s).",
    read_queued_n: "{n} requêtes en file (environ {s} s).",
    read_after_first_pass: "Elles passent après la première lecture qui suit un démarrage : {n} lectures encore dues, {wait}.",
    read_after_queue: "Elles passent après {n} lectures déjà dues, {wait}.",
    about_s: "environ {n} s",
    about_min: "environ {n} min",
    read_scope_menu: "Lire ce menu une fois",
    read_scope_device: "Lire cet appareil une fois",
    read_scope_all: "Tout lire une fois",
    read_scope_hint: "Les lignes qu'aucune entité activée ne suit sont lues une fois, au rythme du bus, après ce qu'attendent les entités.",
    read_price_one: "1 requête, {time}.",
    read_price_n: "{n} requêtes, {time}.",
    read_start: "Démarrer",
    read_stop: "Arrêter",
    dismiss: "Fermer",
    job_running: "Lecture : {done} sur {total} demandées, {read} avec une valeur.",
    job_done: "Lu une fois : {read} sur {total} avec une valeur. Pas tenu à jour : suivez une ligne pour la garder à jour.",
    job_stopped: "Arrêté : {done} sur {total} demandées, {stopped} retirées.",
    job_reload: "L'intégration a été rechargée : les lectures pas encore demandées ont été abandonnées.",
    read_once: "lu une fois",
    follow: "Suivre",
    follow_all: "Tout suivre",
    follow_none: "Ne rien suivre",
    follow_blocked: "désactivée par son appareil",
    follow_pending: "{n} changements à appliquer : {enable} à suivre, {disable} à ne plus suivre.",
    follow_reload: "Home Assistant recharge l'intégration environ {s} s après l'activation d'une entité : le panneau se recharge avec elle, et les lectures en cours s'arrêtent.",
    follow_defaults_off: "{n} d'entre elles sont suivies par défaut (valeurs instantanées, états, compteurs) : désactivées, elles ne sont plus lues, leur historique s'arrête, et les tableaux de bord ou automatisations qui les utilisent ne les trouvent plus.",
    follow_apply: "Appliquer",
    follow_discard: "Annuler",
    follow_done: "{enabled} activées, {disabled} désactivées.",
    follow_reload_soon: "Home Assistant recharge l'intégration dans environ {s} s.",
    follow_refused: "{n} non modifiées : désactivées par leur appareil ou leur entrée, ou pas de cette intégration.",
    writes_pill_on: "Écritures : actives ({n}/{max})",
    writes_pill_off: "Écritures : verrouillées",
    open_switch: "Ouvrir l'interrupteur",
    items_count: "{n} éléments",
    items_count_one: "1 élément",
    fault_hide_zero: "Masquer les compteurs à 0 ({n})",
    fault_all_zero: "Tous les compteurs lus sont à 0.",
    copy_all: "tous les jours",
    copy_weekdays: "lundi – vendredi",
    copy_weekend: "samedi, dimanche",
    search_placeholder: "Rechercher un réglage, une sonde, un code, une clé…",
    search_clear: "Effacer",
    filter_all: "Tout",
    filter_writable: "Modifiables",
    filter_followed: "Suivis",
    filter_unread: "Non lus",
    search_results: "{n} lignes correspondantes",
    search_results_one: "1 ligne correspondante",
    search_empty: "Aucune ligne ne correspond à cette recherche.",
    bar_remove_hint: "{range} — cliquer pour retirer",
    clear_day: "Vider",
    follow_details: "Voir le détail ({n})",
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

/** A range dragged on the bar of a day (from and to as fractions of the day, either order), in quarters of an hour. */
export function dragRange(from: number, to: number): [number, number] {
  const q = (f: number): number => Math.round((Math.min(1, Math.max(0, f)) * 1440) / QUARTER) * QUARTER;
  const start = Math.min(q(from), q(to));
  let end = Math.max(q(from), q(to));
  if (end === start) end = Math.min(1440, start + 60); // a click: one hour
  return [start, end];
}

/** A range dragged on the bar of a day (from and to as fractions of the day, either order), in quarters of an
 * hour, added to the day: ranges it overlaps are merged into it. Null when the day would hold more than three. */
export function addDragged(ranges: [number, number][], from: number, to: number): [number, number][] | null {
  let [start, end] = dragRange(from, to);
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
  code: string; // the vendor codes, ", " between them
  scheme: string; // the labels of their schemes, in the same order, each once
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
        code: codeText(row),
        scheme: [...new Set((row.vendor_codes ?? []).map((c) => schemeText(c, language)))].join(", "),
      });
    }
  }
  return out;
}

// the CSV keeps its first seven columns as before the codes; the code and its scheme come last
const COLUMNS: (keyof ReportRow)[] = ["device", "menu", "label", "value", "unit", "range", "writable", "code", "scheme"];
// the printed report: the code beside the setting, its scheme in a note under each device
const PRINTED: (keyof ReportRow)[] = ["menu", "label", "code", "value", "unit", "range", "writable"];

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
  const headers = PRINTED.map((c) => t(language, `col_${c}`));
  const tables = devices.map((device) => {
    const own = rows.filter((r) => r.device === device);
    const schemes = [...new Set(own.flatMap((r) => (r.scheme ? r.scheme.split(", ") : [])))];
    const note = schemes.length
      ? `<p>${escapeHtml(t(language, "report_codes", { schemes: schemes.join(", ") }))}</p>`
      : "";
    return `<section><h2>${escapeHtml(device)}</h2><table><thead><tr>${headers
      .map((h) => `<th>${escapeHtml(h)}</th>`).join("")}</tr></thead><tbody>${own
      .map((r) => `<tr>${PRINTED.map((c) => `<td>${escapeHtml(r[c])}</td>`).join("")}</tr>`).join("")}</tbody></table>${note}</section>`;
  });
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

// ---- the dashboard card -------------------------------------------------------------------------------------------

/** The attribute keys of a program sensor: one per day, Monday first. */
export const DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

/** A program sensor's attributes (`06:30-18:00, 19:00-21:00` or `-` per day) as the days of the week grid; a day not
 * read yet (no attribute) or not readable is null. */
export function weekFromAttributes(attributes: Record<string, unknown>): Days {
  const days: Days = {};
  DAY_KEYS.forEach((key, i) => {
    const text = attributes[key];
    const parsed = typeof text === "string" ? parseDay(text) : null;
    days[String(i + 1)] = parsed && "ranges" in parsed
      ? parsed.ranges.map(([a, b]) => [clockText(a), clockText(b)])
      : null;
  });
  return days;
}

/** Whether a state is a program sensor of this integration: a sensor whose attributes are days, or (not read yet)
 * whose entity id names a program. */
export function isProgramSensor(entityId: string, attributes: Record<string, unknown>): boolean {
  if (!entityId.startsWith("sensor.")) return false;
  const days = DAY_KEYS.filter((k) => typeof attributes[k] === "string").length;
  const others = Object.keys(attributes).filter((k) => !DAY_KEYS.includes(k) && !["friendly_name", "icon", "edited_on"].includes(k));
  return (days > 0 && others.length === 0) || (days === 0 && /program/.test(entityId));
}

/** Monday 1 … Sunday 7, for the today mark. */
export function isoWeekday(date: Date): number {
  return ((date.getDay() + 6) % 7) + 1;
}

/** The program-day text entities of the program a sensor shows (same device, translation key `<sensor's>_<day>`):
 * day "1" … "7" -> entity id, or null when the program is not writable on its device (no such entities). */
export function dayTextEntities(entities: Record<string, RegistryEntry> | undefined, sensor: string):
  Record<string, string> | null {
  const own = entities?.[sensor];
  if (!entities || !own?.device_id || !own.translation_key) return null;
  const found: Record<string, string> = {};
  for (const entry of Object.values(entities)) {
    if (entry.platform !== "weishaupt" || entry.device_id !== own.device_id || !entry.entity_id.startsWith("text.")) {
      continue;
    }
    const day = DAY_KEYS.findIndex((key) => entry.translation_key === `${own.translation_key}_${key}`);
    if (day >= 0) found[String(day + 1)] = entry.entity_id;
  }
  return Object.keys(found).length === DAY_KEYS.length ? found : null;
}

/** The write switch of the integration and its counters, from its entity (translation key `writes`). */
export function writeSwitch(entities: Record<string, RegistryEntry> | undefined,
  states: Record<string, { state: string; attributes: Record<string, unknown> }>):
  { entity_id: string; on: boolean; used: number | null; max: number | null } | null {
  const entry = Object.values(entities ?? {}).find((e) => e.platform === "weishaupt" && e.translation_key === "writes");
  const state = entry ? states[entry.entity_id] : undefined;
  if (!entry || !state) return null;
  const n = (v: unknown): number | null => (typeof v === "number" ? v : null);
  return { entity_id: entry.entity_id, on: state.state === "on", used: n(state.attributes.writes_last_hour),
    max: n(state.attributes.max_writes_per_hour) };
}

// ---- reads on demand and following entities ---------------------------------------------------------------------

function duration(seconds: number, language: string): string {
  return seconds >= 90 ? t(language, "about_min", { n: Math.round(seconds / 60) }) : t(language, "about_s", { n: seconds });
}

/** What a read on demand would cost, before it is started: requests, their time at the reader's pace, and what they
 * would wait behind. */
export function priceText(estimate: Estimate, language: string): string {
  if (estimate.queued === 0) return t(language, "read_nothing");
  const own = t(language, estimate.queued === 1 ? "read_price_one" : "read_price_n", {
    n: estimate.queued, time: duration(estimate.seconds, language),
  });
  if (estimate.ahead === 0) return own;
  return `${own} ${t(language, estimate.first_pass ? "read_after_first_pass" : "read_after_queue", {
    n: estimate.ahead, wait: duration(estimate.wait, language),
  })}`;
}

/** Where a read on demand stands. */
export function jobText(job: JobProgress, language: string): string {
  if (job.stopped) return t(language, "job_stopped", { done: job.done, total: job.total, stopped: job.stopped });
  if (job.ended) return t(language, "job_done", { read: job.read, total: job.total });
  return t(language, "job_running", { done: job.done, total: job.total, read: job.read });
}

/** The changes chosen in the panel (entity id -> followed or not), against the registry as the tree gave it: what to
 * enable, what to disable, and how many of those disabled are followed by default. */
export function followPlan(
  pending: Record<string, boolean>,
  follows: (Follow | null | undefined)[],
): { enable: string[]; disable: string[]; defaultsOff: number } {
  const known = new Map(follows.filter((f): f is Follow => !!f && !f.blocked).map((f) => [f.entity_id, f]));
  const enable: string[] = [];
  const disable: string[] = [];
  let defaultsOff = 0;
  for (const [entityId, wanted] of Object.entries(pending)) {
    const follow = known.get(entityId);
    if (!follow || follow.enabled === wanted) continue;
    if (wanted) enable.push(entityId);
    else {
      disable.push(entityId);
      if (follow.default) defaultsOff += 1;
    }
  }
  return { enable: enable.sort(), disable: disable.sort(), defaultsOff };
}

/** A choice of follow for a set of rows (follow all, follow none) on top of the pending ones: a row already as
 * wanted drops out of the pending changes. */
export function choose(
  pending: Record<string, boolean>,
  follows: (Follow | null | undefined)[],
  wanted: boolean,
): Record<string, boolean> {
  const next = { ...pending };
  for (const follow of follows) {
    if (!follow || follow.blocked) continue;
    if (follow.enabled === wanted) delete next[follow.entity_id];
    else next[follow.entity_id] = wanted;
  }
  return next;
}

// ---- search and quick filters -----------------------------------------------------------------------------------

export type RowFilter = "all" | "writable" | "followed" | "unread";

function fold(text: string): string {
  return text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
}

/** A vendor code as compared: without case and spaces ("P 31", "p31" and "P31" are one code). */
export function codeKey(text: string): string {
  return text.replace(/\s+/g, "").toLowerCase();
}

/** The vendor codes of a row as shown: "P112", or "P141, 593" for several; empty without. */
export function codeText(row: Row): string {
  return (row.vendor_codes ?? []).map((c) => c.code).join(", ");
}

/** A scheme in words: its label, and the vendor document it numbers. */
export function schemeText(code: VendorCode, language: string): string {
  const name = label(code.scheme_label, language) || code.scheme;
  return code.document ? t(language, "code_title", { scheme: name, document: code.document }) : name;
}

/** The tooltip of a code cell: the scheme of each code (a code means something only in its scheme). */
export function codeTitle(row: Row, language: string): string {
  const codes = row.vendor_codes ?? [];
  const schemes = [...new Set(codes.map((c) => schemeText(c, language)))];
  return schemes.length === 1 ? schemes[0] : codes.map((c) => `${c.code}: ${schemeText(c, language)}`).join("\n");
}

export type CodeSort = "" | "asc" | "desc";

/** Rows ordered by their first vendor code (case- and space-insensitive, numbers in order: P9 before P31), rows
 * without a code last in both directions; "" keeps the order of the menus. The sort is stable. */
export function sortByCode(rows: Row[], direction: CodeSort): Row[] {
  if (!direction) return rows;
  const key = (row: Row): string => codeKey(row.vendor_codes?.[0]?.code ?? "");
  const sign = direction === "asc" ? 1 : -1;
  return rows
    .map((row, i) => ({ row, i, k: key(row) }))
    .sort((a, b) => {
      if (!a.k || !b.k) return (a.k ? 0 : 1) - (b.k ? 0 : 1) || a.i - b.i;
      return sign * a.k.localeCompare(b.k, "en", { numeric: true }) || a.i - b.i;
    })
    .map((x) => x.row);
}

// a query written as a lettered vendor code: one or two letters then digits, a space between or not (P31, p 31, i35)
const CODE_QUERY = /^[a-z]{1,2}\s*\d+$/;

/** Whether a row matches a free-text query (accent- and case-insensitive) and a quick filter. A query written as a
 * lettered code ("P 31", "p31") finds only the rows of that code (P31: not P315, not i31, not a name with "p" and
 * "31" in it); any other query is matched word by word against the name, the description, the keys, the register
 * and the codes, and also finds the rows whose code contains it without spaces ("535"). */
export function matchesRow(
  row: Row,
  query: string,
  filter: RowFilter,
  readings: Record<string, Reading | null>,
  language: string,
): boolean {
  if (filter === "writable" && (!row.writable || row.edited_on)) return false;
  if (filter === "followed" && !row.listened && !row.follow?.enabled) return false;
  if (filter === "unread" && readingOf(row, readings) !== null) return false;
  const terms = fold(query).trim().split(/\s+/).filter(Boolean);
  if (!terms.length) return true;
  const codes = (row.vendor_codes ?? []).map((c) => codeKey(fold(c.code)));
  const wanted = codeKey(fold(query));
  if (CODE_QUERY.test(fold(query).trim())) return codes.includes(wanted);
  if (codes.some((code) => code.includes(wanted))) return true;
  const haystack = fold([
    label(row.label, language),
    label(row.description, language),
    row.key,
    row.message,
    row.writable?.register ?? "",
    ...(row.vendor_codes ?? []).map((c) => c.code),
  ].join(" "));
  return terms.every((term) => haystack.includes(term));
}
