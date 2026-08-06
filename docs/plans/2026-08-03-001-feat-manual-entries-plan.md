---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
title: "feat: manual-entries — Sammelbuchungen über den CLI (und MCP)"
date: 2026-08-03
depth: deep
target_repo: bexio-cli (+ ai-system guard)
---

# feat: `manual-entries` — Sammelbuchungen über den CLI

## Summary

Der CLI deckt Rechnungen, Aufträge, Kontakte, Lieferantenrechnungen und Referenzdaten ab — aber **nicht das Hauptbuch**. Jede Sammelbuchung ist damit Handarbeit in der Weboberfläche, auch dann, wenn alle Werte bereits feststehen.

Am 2026-08-03 sind so vier Nachtragsbuchungen, eine Kontokorrektur und zwei Steuercode-Korrekturen von Hand erfasst worden. Jede war eine dreizeilige Sammelbuchung mit vollständig bekannten Zahlen. Der Agent konnte sie berechnen, prüfen und die Fehler finden — nur nicht buchen.

Dieser Plan ergänzt `bexio manual-entries` (list / show / create / edit / delete) plus die gleichen Operationen im MCP-Server, und zieht die Freigabe-Absicherung im selben Schritt nach.

**Product Contract:** direkte Planung aus der Operator-Session 2026-08-03. Auslöser (Zitat): «The CLI has been built by us, so we can extend it. It is our own product. Let's fix it.»

---

## Problem Frame

**Der Befehlsumfang endet vor dem Journal.** `bexio --help` listet `bills, items, payments, orders, invoices, contacts, quotes, countries, currencies, languages, contact-groups, business-activities, accounts, account-groups, payment-types, taxes, vat-periods, timesheets, projects, milestones, work-packages, reminders`. Sammelbuchungen und Journal fehlen. Lesend geht es bereits über die rohe API (`GET /3.0/accounting/manual_entries` liefert 592 Einträge mit allen Zeilen), schreibend gibt es keinen Weg.

**Der Umweg über die rohe API ist hart blockiert.** `ai-system/config/claude/hooks/external-action-guard.sh` verweigert jede Mutation gegen `api.bexio.com` und verweist ausdrücklich auf den CLI als sanktionierten Pfad («alles via CLI», 2026-07-14). Für Sammelbuchungen existiert dieser sanktionierte Pfad aber nicht — die Absicht der Regel läuft ins Leere.

**Konten und Steuercodes werden über installationsspezifische IDs adressiert.** Die API arbeitet mit `account_id` und `tax_id`, der Mensch denkt in Kontonummern und Codes. In der Session vom 2026-08-03 hat genau das Verwirrung erzeugt: `id 243` ist Konto `4450`, `id 171` ist `4400`, `id 53` ist `Vorsteuer8.1`. Eine Fehlbuchung entstand, weil auf der Gegenzeile `4400` statt `4450` stand — mit IDs im Interface wäre der Fehler unsichtbarer geworden, nicht sichtbarer.

**Die Weboberfläche verschiebt Datumsangaben.** Zweimal beobachtet: Eintrag `790` wurde nach dem Speichern von `2026-06-26` auf `2026-06-25` verschoben; Eintrag `827` liegt gespeichert auf `2026-07-01` und wird als `30.06.2026` angezeigt. Bei einem Monats- oder Quartalsersten landet ein Beleg damit in der falschen Steuerperiode. Ein Schreibweg mit explizitem Datumsstring hat dieses Problem nicht — das ist ein eigenständiger Grund für diese Einheit, nicht nur Bequemlichkeit.

---

## Requirements

- **R1** — `manual-entries list [--limit N] [--from YYYY-MM-DD] [--to YYYY-MM-DD]` und `manual-entries show <id>`. `show` gibt alle Zeilen mit Konto**nummer**, Betrag, Währung, Kurs, Steuercode und Beschreibung aus.
- **R2** — `manual-entries create` erzeugt eine Sammelbuchung mit *n* Zeilen. Je Zeile: Soll- **oder** Habenkonto (als Kontonummer), Betrag, Währung, Kurs, optional Steuercode, Beschreibung. Die dreizeilige Form aus der Praxis (Zahlkonto / Aufwand in Fremdwährung / Kursdifferenz) muss ohne Verrenkung ausdrückbar sein.
- **R3** — `manual-entries edit <id>` ändert Zeilen. **Vor der Umsetzung zu klären:** ob der PUT auf Sammelbuchungen dieselbe Ersetzungssemantik hat wie der v4-PUT auf Lieferantenrechnungen, wo omittierte Anhänge gelöscht werden (dokumentiert in `bexio/commands/bills.py`, `--attach`). Falls ja, muss `edit` die bestehenden Zeilen lesen, zusammenführen und vollständig zurückschreiben — und das im Hilfetext sagen.
- **R4** — **Bilanzprüfung vor dem Senden.** Summe Soll muss Summe Haben entsprechen. Abweichung = Abbruch mit beiden Summen und der Differenz, kein Request. Bexio lehnt unbilanzierte Buchungen selbst ab, aber die lokale Prüfung liefert die brauchbare Meldung und verhindert einen halben Schreibversuch.
- **R5** — **Der Freigabe-Guard wird in derselben Änderung erweitert.** Ohne das läuft der neue Schreibweg **ungeprüft**: die Regex in `external-action-guard.sh` filtert nach Ressourcennamen (`contacts|invoices|items|orders|expenses|bills|payments|accounts|taxes|projects|timesheets`), und `manual-entries` steht nicht darauf. Ein neuer Befehl wäre damit der einzige unbewachte Schreibpfad ins Hauptbuch. Diese Anforderung ist blockierend — der Befehl darf nicht ohne sie ausgeliefert werden.
- **R6** — Konten werden als **Kontonummer** übergeben (`4450`), nicht als `account_id`. Auflösung über `GET /2.0/accounts`. Unbekannte Nummer = Abbruch mit der Liste der nächstliegenden Treffer.
- **R7** — Steuern werden als **Code** übergeben (`Vorsteuer8.1`, `BZM81`, `V00`), nicht als `tax_id`. Auflösung über `GET /3.0/taxes`. Ein inaktiver Code oder ein Umsatzsteuercode auf einer Aufwandszeile = Abbruch. Kein stiller Fallback auf «keine Steuer» — steuerfrei muss explizit `V00` sein.
- **R8** — Datum wird als expliziter `YYYY-MM-DD`-String gesendet und unverändert zurückgelesen. Der Hilfetext benennt, dass die Weboberfläche abweichend anzeigen kann und die API die Wahrheit hält.
- **R9** — Dieselben Operationen im MCP-Server (`bexio/mcp_server.py`), damit der Agentenpfad nicht über die Shell muss.
- **R10** — Wiederholungsschutz: `create` akzeptiert `--reference-nr` und verweigert, wenn diese Belegnummer im Zielzeitraum schon existiert. Achtung Fallstrick: `reference_nr` ist die sichtbare Belegnummer und **nicht** die API-ID (api-id `827` trägt Belegnummer `702`).

**Erfolgskriterium:** Die dreizeilige Buchung, die am 2026-08-03 als Beleg 702 von Hand erfasst wurde — Soll `1030` CHF 119.84, Haben `4450` BRL 765.35 zum Kurs 0.157222 mit `Vorsteuer8.1`, Soll `6949` CHF 0.49 — lässt sich mit einem `create`-Aufruf identisch erzeugen, und der Guard fragt vorher nach Freigabe.

---

## Key Technical Decisions

**KTD1 — Nummern und Codes im Interface, IDs nur intern.** Installationsspezifische IDs im Interface wären kürzer zu implementieren und in der Benutzung unlesbar. Die Kontokorrektur vom 2026-08-03 (`4400` statt `4450`) war nur auffindbar, weil jemand Kontonummern gelesen hat.

**KTD2 — Bilanzprüfung lokal, nicht nur serverseitig.** Doppelt geprüft ist hier richtig: die Fehlermeldung ist der eigentliche Wert.

**KTD3 — Guard-Erweiterung ist Teil der Einheit, nicht Folgearbeit.** Ein neuer Schreibweg ins Hauptbuch, der die Freigabe umgeht, ist ein grösseres Problem als der fehlende Befehl. Die Änderung liegt in einem anderen Repo (`ai-system`) — das macht sie leichter zu vergessen, nicht weniger zwingend.

**KTD4 — Der bestehende `bexio_booking.py`-Pfad bleibt für Kreditorenrechnungen zuständig.** Er trägt Toleranzprüfung, Idempotenz-Marker und Dedup-Guards, die dieser CLI-Befehl nicht nachbaut. `manual-entries` ist für Journalarbeit ausserhalb der Kreditoren-Pipeline: Umbuchungen, Korrekturen, Rückerstattungen, Bankgebühren.

---

## Verification Contract

**Testrunner ist `unittest`, nicht pytest.** `python3 -m pytest tests/` sammelt null Tests — die Suite läuft über `python3 -m unittest discover -s tests`. Basis vor dieser Arbeit: 385 Tests, grün.

Alle neuen Tests dieser Arbeit liegen in **`tests/test_manual_entries.py`**, im Muster von `tests/test_accounting.py` (`capture_with_responses` aus `tests/helpers.py`).

Eine Bedingung, die genau dann hält, wenn die agentenseitige Arbeit fertig ist:

```bash
cd ~/projects/bexio-cli \
  && python3 -m unittest tests.test_manual_entries -q \
  && python3 -m unittest discover -s tests -q \
  && rg -q 'manual-entries' /Users/noel/projects/ai-system/config/claude/hooks/external-action-guard.sh
```

Die drei Glieder prüfen: die neuen Tests existieren und laufen · nichts Bestehendes ist gebrochen · der Guard kennt die neue Ressource (U5, sonst ungeprüfter Schreibweg ins Hauptbuch).

**Die Bedingung endet bewusst vor U4.** `edit`/`delete` brauchen eine echte Testbuchung im Produktivmandanten und damit Noëls Freigabe im Einzelfall — eine Abbruchbedingung, die auf eine menschliche Handlung wartet, ist nie erfüllbar und würde endlos laufen.

## Implementation Units

### U1. Lesepfad — `list` und `show`

**Verification:** `python3 -m unittest tests.test_manual_entries.TestManualEntriesRead -q`
**Tests:** `tests/test_manual_entries.py`


Neues Modul `bexio/commands/manual_entries.py` im Muster von `bills.py` (`register(sub)` + Befehlsfunktionen), registriert in `bexio/cli.py`. Endpunkt `GET /3.0/accounting/manual_entries` über `client.get_v3`. `show` löst Konto-IDs zu Nummern und Steuer-IDs zu Codes auf (R6/R7) und gibt Soll/Haben lesbar aus.

**Test zuerst:** gemockte Antwort im Muster von `tests/test_accounting.py` (`capture_with_responses`); `show` gibt Kontonummer statt ID aus; ein unbekanntes Konto in der Antwort bricht nicht, sondern zeigt die ID mit Hinweis.

### U2. Auflösung von Konten und Steuercodes

**Verification:** `python3 -m unittest tests.test_manual_entries.TestResolveAccountsAndTaxes -q`
**Tests:** `tests/test_manual_entries.py`


Hilfsfunktionen, die Kontonummer → `account_id` und Steuercode → `tax_id` auflösen, mit Zwischenspeicherung pro Prozess (jeder Aufruf sonst zwei zusätzliche Requests). Prüfung analog zu `bexio_booking.py`: inaktiver Code und Umsatzsteuercode auf einer Aufwandszeile werden verweigert.

**Test zuerst:** bekannte Nummer löst auf; unbekannte bricht mit Vorschlagsliste; inaktiver Steuercode bricht; Umsatzsteuercode auf Aufwandszeile bricht.

### U3. `create` mit Bilanzprüfung

**Verification:** `python3 -m unittest tests.test_manual_entries.TestCreateAndBalance -q`
**Tests:** `tests/test_manual_entries.py`


Zeilen-Syntax festlegen. Empfehlung: wiederholbares `--line`, ein Argument pro Zeile, Felder durch `:` getrennt und benannt, damit die Reihenfolge nicht auswendig gelernt werden muss — z. B.
`--line "debit=1030,amount=119.84,currency=CHF,text=..."`.
Alternative in der Umsetzung prüfen: eine JSON-Datei via `--lines-file`, falls das Zeilenformat unhandlich wird. Beides zulassen ist erlaubt.

Bilanzprüfung nach R4 vor dem Request. Datum als expliziter String (R8).

**Test zuerst:** die Beleg-702-Buchung aus dem Erfolgskriterium erzeugt genau die erwartete Payload; unbilanzierte Buchung bricht ab und nennt beide Summen; fehlendes Datum bricht ab.

### U4. `edit` und `delete`

**Verification:** menschlich — Testbuchung 0.01 im Produktivmandanten, danach gelöscht. NICHT Teil der /goal-Bedingung.


Erst die Ersetzungssemantik aus R3 empirisch klären — eine Testbuchung anlegen, eine Zeile ändern, zurücklesen. **Diese Klärung läuft gegen einen echten Mandanten und braucht Noëls Freigabe**; ohne sie wird `edit` nicht ausgeliefert, `list`/`show`/`create` aber schon.

**Test zuerst:** `edit` liest bestehende Zeilen und schickt sie vollständig zurück (sofern die Klärung Ersetzungssemantik ergibt); `delete` verlangt die API-ID und weist eine Belegnummer als Eingabe ab (R10-Fallstrick).

### U5. Guard-Erweiterung — blockierend

**Verification:** `rg -q 'manual-entries' ~/projects/ai-system/config/claude/hooks/external-action-guard.sh` PLUS ein beobachtet ausgelöster Freigabedialog.


In `ai-system/config/claude/hooks/external-action-guard.sh` die Ressourcenliste um `manual-entries` erweitern, sodass `create|edit|delete` in den bestehenden Freigabe-Zweig fallen (interaktiv fragen, headless blocken). Danach `rulesync generate` beziehungsweise das Settings-Sync-Skript, Änderung committen und pushen.

**Verifikation ausgeführt, nicht gelesen:** ein `bexio manual-entries create …`-Aufruf muss die Freigabeabfrage auslösen. Ohne diesen Nachweis gilt die Einheit als offen.

### U6. MCP-Operationen

**Verification:** `python3 -c "import bexio.mcp_server as m; assert hasattr(m,'create_manual_entry')"`
**Tests:** `tests/test_manual_entries.py`


`list_manual_entries`, `show_manual_entry`, `create_manual_entry` in `bexio/mcp_server.py` im Muster der bestehenden `@mcp.tool()`-Funktionen. Der schreibende Aufruf trägt im Docstring den Hinweis, dass er ins Hauptbuch schreibt.

### U7. Dokumentation

**Verification:** `rg -q 'manual-entries' README.md README.de.md`


`README.md` und `README.de.md` um den Befehl ergänzen. In `~/projects/ai-system/.rulesync/skills/bexio/` festhalten, dass Sammelbuchungen jetzt über den CLI gehen — die Skill-Referenz `reference/ui-deep-links.md` verweist bereits auf `accounting/manualEntries/id/<id>` für die Oberfläche. Danach `rulesync generate`.

---

## Regression Checklist

- [ ] `bexio --help` listet den neuen Befehl, alle bestehenden bleiben unverändert
- [ ] Bestehende Testsuite unverändert grün
- [ ] `bexio bills`, `invoices`, `orders`, `contacts` in Funktion und Ausgabe unberührt
- [ ] Der Guard verweigert weiterhin jede rohe Mutation gegen `api.bexio.com`
- [ ] Die bestehenden freigabepflichtigen CLI-Befehle fragen weiterhin nach Freigabe
- [ ] `bexio_booking.py` im `noevu-company`-Repo bleibt unberührt — es ist der Kreditorenpfad und nicht Teil dieser Änderung
- [ ] MCP-Server startet und listet die bestehenden Werkzeuge weiter

---

## Scope Boundaries

**Nicht Teil dieser Arbeit:** Journal-Auswertungen und Kontoauszüge (kein Deep-Link und keine offensichtliche API dafür — geprüft: `accounting/journal` gibt 404 in der Oberfläche); Bankabgleich; Ersatz des Kreditorenpfads; automatisches Buchen ohne Freigabe.

**Ausdrücklich kein Ziel:** die Freigabe abschaffen. Der Befehl soll die Handarbeit ersetzen, nicht die Kontrolle.

---

## Risks & Dependencies

**Risk 1 — Ungeprüfter Schreibweg ins Hauptbuch.** Wird U5 vergessen, entsteht der einzige unbewachte Bexio-Schreibpfad. Gegenmassnahme: U5 ist blockierend, und die Verifikation verlangt eine ausgelöste Freigabeabfrage, keine Codelektüre.

**Risk 2 — Ersetzungssemantik beim PUT.** Falls omittierte Zeilen gelöscht werden, zerstört ein naives `edit` Buchungszeilen. Gegenmassnahme: U4 klärt empirisch und liefert `edit` erst danach.

**Risk 3 — Schreiben gegen den Produktivmandanten beim Entwickeln.** Es gibt keinen Testmandanten. Gegenmassnahme: Testbuchungen mit erkennbarer Belegnummer, Betrag 0.01, unmittelbar danach gelöscht — und jeder Schreibversuch nur mit Noëls Freigabe im Einzelfall.

**Dependency** — `GET /3.0/accounting/manual_entries` ist verifiziert. Der zugehörige **POST/PUT ist nicht verifiziert**; das ist die erste Aufgabe in U3 und kann den Zuschnitt ändern, falls Bexio dort eine andere Struktur erwartet.

---

## Definition of Done

- `list`, `show`, `create` ausgeliefert und getestet; `edit`/`delete` ausgeliefert, sofern U4 die Semantik geklärt hat, sonst dokumentiert offen.
- Die Beleg-702-Buchung ist per `create` reproduzierbar.
- Die Freigabeabfrage ist ausgelöst beobachtet worden.
- MCP-Operationen vorhanden, Server startet.
- READMEs und Bexio-Skill aktualisiert, `rulesync generate` gelaufen.

---

## Sources & Research

- Session 2026-08-03: vier Nachtragsbuchungen (Belege 702–705), eine Kontokorrektur `4400`→`4450`, zwei Steuercode-Ergänzungen `Vorsteuer8.1`. Alle von Hand, alle mit vorab bekannten Werten.
- Datumsverschiebung der Oberfläche: zweimal beobachtet (api-id 790 und 827).
- Guard: `ai-system/config/claude/hooks/external-action-guard.sh` — Ressourcenliste in der `elif`-Regex, Kommentar «api.bexio.com … stays hard-denied below, so writes go [via CLI]».
- CLI-Architektur: `bexio/cli.py` (Registrierung), `bexio/client.py` (`get_v3`, `post`, `put`), `bexio/commands/bills.py` (Muster mit create/edit), `tests/test_accounting.py` (Testmuster), `bexio/mcp_server.py` (`@mcp.tool()`).
- UI-Routen: `ai-system/.rulesync/skills/bexio/reference/ui-deep-links.md`.
