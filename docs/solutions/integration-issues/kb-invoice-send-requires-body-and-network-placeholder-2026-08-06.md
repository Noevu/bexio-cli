# `kb_invoice/{id}/send` verschickt echte E-Mails — braucht Body und `[Network Link]`

**Datum:** 2026-08-06 · **Kategorie:** integration-issues · **Betrifft:** `bexio invoices send`

## Frage

Verschickt `POST /2.0/kb_invoice/{id}/send` tatsächlich E-Mails an Kunden — oder markiert es
die Rechnung nur intern?

## Test

Testkontakt mit `noel@noevu.ch` angelegt (id 354), Rechnungsentwurf über 1.00 CHF (id 404),
Versand an die eigene Adresse. Danach beides gelöscht.

| Aufruf | Ergebnis |
|---|---|
| `POST …/send` ohne Body (bisheriger CLI-Stand) | `422 missing data` — **es passiert nichts** |
| Body ohne Platzhalter im `message` | `422 … missing_network_placeholder` |
| `message` mit `[Network]`, `[Netzwerk]`, `[network]`, `[Dokument]` | dieselbe 422 |
| `message` mit **`[Network Link]`** | `{"success": true}` → **Mail zugestellt** |

Zustellung verifiziert: Mail um 16:46 im Posteingang, Absender `billing@noevu.ch`,
Betreff wie übergeben.

## Ergebnis

1. **Der Endpunkt verschickt echte E-Mails.** Wer die Empfängeradresse setzt, bestimmt, wer
   die Rechnung bekommt — deshalb ist `--to` Pflichtargument und steht sichtbar im Kommando,
   das der Freigabe-Guard anzeigt.
2. **Der bisherige CLI-Befehl war funktionslos** — er sendete keinen Body und lief immer in
   `422 missing data`. Ein „versehentlicher Versand" war damit gar nicht möglich; ab jetzt
   schon, deshalb der explizite Empfänger.
3. **`message` muss den Platzhalter `[Network Link]` enthalten** (bexio Netzwerk-Plugin). Er
   wird beim Versand durch den Link auf das Dokument ersetzt. Ohne ihn: 422, kein Versand.
   Der CLI hängt ihn nicht automatisch an — der Text gehört dem Absender, nicht dem Werkzeug;
   die Fehlermeldung der API ist eindeutig genug.

## Verwandt

- `bexio invoices send --to … --subject … --message "… [Network Link]"`
- Guard: `bexio invoices send` fällt in den Freigabe-Zweig von `external-action-guard.sh`;
  seit 2026-08-06 auch `mcp__bexio__send_invoice`.
