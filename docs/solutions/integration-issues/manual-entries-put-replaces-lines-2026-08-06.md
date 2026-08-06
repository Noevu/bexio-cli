# Der v3-PUT auf Sammelbuchungen ersetzt den ganzen Zeilensatz

**Datum:** 2026-08-06 · **Kategorie:** integration-issues · **Betrifft:** `bexio manual-entries edit`, `PUT /3.0/accounting/manual_entries/<id>`

## Frage

Verhält sich `PUT /3.0/accounting/manual_entries/<id>` wie der v4-PUT auf Lieferantenrechnungen
(patch-artig für Skalare, aber Ersetzung bei `attachment_ids`) — oder ersetzt er den kompletten
Zeilensatz? Davon hängt ab, ob ein naives `edit` Buchungszeilen zerstört.

## Empirische Klärung

Kein Testmandant vorhanden, deshalb im Produktivmandanten mit 0.01 CHF auf zwei Aufwandskonten
(6945 Rundungsdifferenz / 6949 Währungsverluste / 6940 Bankspesen — Erfolgsrechnung netto null),
Freigabe von Noël am 2026-08-06, beide Testbuchungen unmittelbar danach gelöscht.

1. Dreizeilige Buchung angelegt → API-ID **832** (Soll 6945 0.02 / Haben 6949 0.01 / Haben 6940 0.01).
2. `PUT` mit nur **zwei** Zeilen gesendet (Soll 6945 0.01 / Haben 6949 0.01).
3. Zurückgelesen: die Buchung hat **zwei** Zeilen. Die ausgelassene Zeile 6940 ist **gelöscht**.

## Ergebnis

**Ersetzungssemantik.** Was nicht im PUT steht, existiert danach nicht mehr. Ein `edit`, das nur
das Datum ändern will und die Zeilen weglässt, würde eine Buchung leeren.

Weitere Beobachtungen aus demselben Lauf:

- **Bexio vergibt keine Belegnummer automatisch.** `reference_nr` bleibt `null`, wenn beim POST
  nichts mitgegeben wird. Der CLI weist beim Anlegen ohne `--reference-nr` darauf hin.
- **Das Datum kommt wörtlich zurück** (`2026-08-06` gesendet, `2026-08-06` gelesen) — die
  Verschiebung um einen Tag ist ein Anzeigeverhalten der Weboberfläche, kein API-Verhalten.
- **Zeilen tragen im POST-Echo teils `"id": null`**, im gespeicherten Zustand aber echte IDs.
  Diese IDs sowie `date`, `created_by_user_id`, `edited_by_user_id` je Zeile sind read-only und
  werden beim Zurückschreiben entfernt (`strip_line`).

## Konsequenz im Code

`bexio/commands/manual_entries.py`:

- `edit` **ohne** `--line` liest die bestehenden Zeilen, säubert sie und schickt sie vollständig
  zurück — nur Kopf-Felder (`date`, `reference_nr`) ändern sich.
- `edit` **mit** `--line` behandelt die übergebenen Zeilen als vollständigen neuen Satz; der
  Hilfetext sagt das ausdrücklich («omitted lines are gone»).
- Vor jedem Schreibversuch läuft die Bilanzprüfung — auch im Merge-Pfad, damit eine bereits
  unbilanzierte gespeicherte Buchung nicht unbemerkt zurückgeschrieben wird.

## Verwandt

- `bexio/commands/bills.py` — derselbe Fallstrick beim v4-PUT mit `attachment_ids`.
- `docs/plans/2026-08-03-001-feat-manual-entries-plan.md` — Risk 2, hier aufgelöst.
