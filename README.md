# Weishaupt WCM (ebusd)

Intégration Home Assistant qui lit et règle les régulateurs Weishaupt WCM (cascade KA, commandes FS) à travers ebusd,
avec les commandes `5022` (lecture) et `5023` (écriture) protégées par le CRC Weishaupt. Les lectures et l'état des
chaudières publiés par ebusd en MQTT restent tels quels ; cette intégration ajoute les réglages.

## Prérequis

- ebusd lancé avec `--enablehex`, joignable en TCP (port 8888 par défaut).
- Le journal des trames de l'add-on ebusd (`sqlite_db`) lisible par Home Assistant, par exemple
  `/share/ebusd/telegrams.db` : il sert à savoir si WCM-Diagnose est connecté.

## Entités

Par régulateur (KA, FS1, FS2, FS3) : les réglages en entités `number`, les dates de congés des FS en entités `date` et leur niveau de température (hors-gel ou réduit) en entité `select`,
les programmes horaires (chauffage 1 à 3, eau chaude, circulation) en capteurs (état = créneaux du jour, un attribut
par jour, relus toutes les heures). Le service `weishaupt.set_time_program` réécrit les créneaux d'un jour
(ex. `06:30-18:00, 19:00-21:00`, au quart d'heure, 3 au plus), créneau par créneau, sans réécrire ceux qui ne changent
pas.
Seuls les registres dont l'écriture a été essayée sur le bus de l'école Sainte-Marie (30/10/2026) sont exposés
(`registers.py`).

## Écritures

Désactivées par défaut (options de l'intégration). Chaque écriture passe par `guard.py` :

- bornes par registre, tirées des notices WCM-FS 2.0 (83277701) et WCM-KA 3.0 (83258401), resserrées par les réglages liés (réduite ≤ normale, départ mini ≤ maxi, modulation mini ≤ maxi) ;
- au plus une écriture par registre toutes les 10 s et 30 écritures par heure ;
- un registre par trame `5023`, relu après l'écriture ; une valeur non retenue est signalée comme une erreur ;
- la plupart des réglages ne sont acceptés que depuis l'adresse de l'outil de service `ff` (les autres adresses sont
  acquittées puis ignorées). Une écriture depuis `ff` est refusée si une trame de `ff` figure dans le journal des
  10 dernières minutes (WCM-Diagnose connecté : deux maîtres à la même adresse se perturberaient) ou si le journal
  est illisible.

Chaque écriture est journalisée (`ÉCRITURE …` dans le journal HA) et émet l'événement `weishaupt_write` (valeur avant,
valeur relue, adresse source).

## Tests

```bash
python3 -m pytest tests
```

Les tests couvrent le protocole (trames comparées à celles du bus réel) et la garde, sans Home Assistant.
