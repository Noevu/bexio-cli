# bexio-cli + bexio-mcp

🇬🇧 [English version](README.md)

Ein Tool, mit dem du dein [Bexio](https://www.bexio.com)-Konto direkt vom Terminal deines Computers aus steuern kannst — ohne im Browser zu klicken. Enthält ausserdem einen MCP-Server, damit KI-Assistenten wie Claude direkt im Gespräch mit Bexio kommunizieren können.

**Was du damit machen kannst:**
- Rechnungen für alle Daueraufträge mit einem einzigen Befehl erstellen
- Rechnungs- und Offerten-PDFs in grossen Mengen herunterladen
- Alles anzeigen, was überfällig ist oder noch im Entwurf liegt
- Stunden erfassen, Projekte verwalten, Zahlungen eintragen
- Bexio mit anderen Tools und Skripten verbinden

Entwickelt und gepflegt von [Noevu](https://noevu.ch) — einer Schweizer Webagentur spezialisiert auf [KI-gestützte Automatisierung für Schweizer KMU](https://noevu.ch/de/leistungen/ki-automatisierung).

**Warum ein Terminal-Tool statt im Browser klicken?**

- **Geschwindigkeit.** Was 10 Minuten Klicken kostet, dauert 10 Sekunden.
- **Massenverarbeitung.** Rechnungen für 30 Daueraufträge auf einmal erstellen. 50 PDFs in einem Durchgang herunterladen. Das geht im Browser nicht.
- **Automatisierung.** Zeitgesteuert ausführen — Rechnungen werden jeden Monat automatisch erstellt, ohne manuelle Schritte.
- **Kein Browser nötig.** Läuft auf Servern, in Skripten, in Pipelines — überall, wo Python läuft.
- **KI-bereit.** Mit KI-Tools wie Claude oder ChatGPT verbinden, damit dein KI-Assistent Bexio-Daten direkt abrufen und aktualisieren kann.
- **Kostenlos und Open Source.** Kein zusätzliches Abo. Läuft auf deinem Gerät.

---

## Was ist ein Terminal?

Das Terminal ist eine textbasierte Möglichkeit, deinen Computer zu steuern. Auf dem Mac: **⌘ Leertaste** drücken, `Terminal` eingeben, Enter drücken. Unter Windows: nach **Eingabeaufforderung** oder **PowerShell** suchen. Du tippst einen Befehl und drückst Enter — der Computer erledigt den Rest.

---

## Einrichtung (einmalig)

### Schritt 1 — Python installieren

Das Tool benötigt Python 3.10 oder neuer. Prüfen, ob du es bereits hast:

```
python3 --version
```

Wenn `Python 3.10` oder höher erscheint, bist du bereit. Andernfalls herunterladen unter [python.org/downloads](https://www.python.org/downloads/).

### Schritt 2 — Tool installieren

Diesen Befehl ins Terminal kopieren und Enter drücken:

```
pipx install git+https://github.com/noevu/bexio-cli
```

Falls `pipx` nicht gefunden wird, zuerst installieren:

```
pip install pipx
```

Dann den Installationsbefehl wiederholen.

### Schritt 3 — Mit Bexio verbinden

Du brauchst einen API-Token — stell dir das wie ein Passwort vor, mit dem das Tool in deinem Auftrag mit Bexio kommuniziert.

**Token holen:**
1. In Bexio einloggen
2. Zu **Einstellungen → API-Token** navigieren
3. Neuen Token erstellen und kopieren

**Token speichern:**

```
bexio auth login
```

Token einfügen, wenn du gefragt wirst. Er wird sicher im Passwort-Manager deines Systems gespeichert (macOS Schlüsselbund, Windows Credential Manager oder Linux Secret Service) — du musst ihn nicht nochmals eingeben.

**Verbindung prüfen:**

```
bexio auth status
```

---

## So funktioniert es

Jeder Befehl folgt demselben Muster:

```
bexio  [was]  [aktion]  [nummer oder optionen]
```

Zum Beispiel:
- `bexio invoices list` — alle Rechnungen anzeigen
- `bexio invoices show 47` — Details von Rechnung 47 anzeigen
- `bexio orders create-invoice 23` — Rechnung aus Auftrag 23 erstellen

**Wie finde ich die Nummer?** Das gewünschte Element in Bexio im Browser öffnen. Die Nummer steht am Ende der URL — zum Beispiel `https://office.bexio.com/index.php/kb_invoice/show/id/47` → die Nummer ist **47**.

---

## Was du tun kannst

### Rechnungen

```
bexio invoices list                      alle Rechnungen anzeigen
bexio invoices list --status open        nur offene (unbezahlte) Rechnungen
bexio invoices list --status draft       nur Entwürfe
bexio invoices show 47                   Details von Rechnung 47
bexio invoices search "Muster AG"        Rechnungen nach Name suchen
bexio invoices pdf 47                    Rechnung 47 als PDF herunterladen
bexio invoices send 47                   Rechnung 47 per E-Mail senden
bexio invoices issue 47                  Rechnung 47 ausstellen
bexio invoices cancel 47                 Rechnung 47 stornieren
bexio invoices copy 47                   Rechnung 47 kopieren
```

Weitere Status-Filter: `partial` (teilweise bezahlt), `paid` (bezahlt), `cancelled` (storniert)

### Aufträge

```
bexio orders list                        alle Aufträge anzeigen
bexio orders list --recurring            nur Daueraufträge anzeigen
bexio orders show 23                     Details von Auftrag 23
bexio orders search "Hosting"            Aufträge nach Name suchen
bexio orders create-invoice 23           Rechnung aus Auftrag 23 erstellen
bexio orders pdf 23                      Auftrag 23 als PDF herunterladen
bexio orders delete 23                   Auftrag 23 löschen
```

### Offerten

```
bexio quotes list                        alle Offerten anzeigen
bexio quotes list --status accepted      nur akzeptierte Offerten
bexio quotes show 12                     Details von Offerte 12
bexio quotes send 12                     Offerte 12 per E-Mail senden
bexio quotes accept 12                   Offerte 12 als akzeptiert markieren
bexio quotes decline 12                  Offerte 12 als abgelehnt markieren
bexio quotes create-order 12             Offerte 12 in Auftrag umwandeln
bexio quotes create-invoice 12           Offerte 12 direkt in Rechnung umwandeln
bexio quotes pdf 12                      Offerte 12 als PDF herunterladen
```

### Kontakte

```
bexio contacts list                      alle Kontakte anzeigen
bexio contacts search "Muster"           Kontakte nach Name suchen
bexio contacts show 5                    Details von Kontakt 5
bexio contacts create --name "Muster AG" --email info@muster.ch
bexio contacts edit 5 --email neu@muster.ch
bexio contacts delete 5
```

Für eine Person (kein Unternehmen) `--firstname` und `--lastname` statt `--name` verwenden, und `--type 2` hinzufügen:

```
bexio contacts create --firstname Anna --lastname Muster --phone "+41 44 000 00 00" --type 2
```

### Zahlungen

Zahlungen zu einer Rechnung erfassen oder abrufen:

```
bexio payments list 47                   Zahlungen zu Rechnung 47 anzeigen
bexio payments create 47 --amount 1500.00 --date 2024-03-01
```

### Lieferantenrechnungen (Bills)

```
bexio bills list                         alle Lieferantenrechnungen anzeigen
bexio bills show abc-123                 Details einer Lieferantenrechnung
bexio bills mark-paid abc-123            als bezahlt markieren
```

### Projekte

```
bexio projects list                      alle Projekte anzeigen
bexio projects show 20                   Projektdetails anzeigen
bexio projects create --name "Website Redesign" --contact-id 5
bexio projects archive 20                abgeschlossenes Projekt archivieren
```

Meilensteine und Arbeitspakete sind ebenfalls verfügbar.

### Zeiterfassung

```
bexio timesheets list                    alle Zeiteinträge anzeigen
bexio timesheets create --date 2024-03-15 --duration 02:30 --project-id 20 --text "Kundengespräch"
bexio timesheets delete 77
```

### Mahnungen

```
bexio reminders list 47                  Mahnungen zu Rechnung 47 anzeigen
bexio reminders create 47                Mahnung für Rechnung 47 erstellen
bexio reminders send 47 30               Mahnung 30 (zu Rechnung 47) per E-Mail senden
bexio reminders pdf 47 30                Mahnung als PDF herunterladen
```

### Stammdaten (Steuern, Konten, Währungen usw.)

```
bexio taxes list
bexio accounts list
bexio vat-periods list
bexio currencies list
bexio payment-types list
bexio units list
bexio countries list
```

---

## Häufige Aufgaben

**Rechnungen für alle Daueraufträge auf einmal erstellen:**

1. Daueraufträge anzeigen: `bexio orders list --recurring`
2. Die ID-Nummern in der ersten Spalte notieren
3. `bexio orders create-invoice 23` für jede Nummer ausführen

Oder — wenn du mit Skripten vertraut bist — alles automatisch erledigen lassen. Frage deine Entwicklerin oder deinen Entwickler.

**Alle offenen Rechnungs-PDFs herunterladen:**

1. `bexio invoices list --status open` — IDs notieren
2. `bexio invoices pdf 47` — für jede ID wiederholen

---

## Ergebnisse in eine Datei speichern

`> dateiname.txt` nach einem beliebigen Befehl anhängen, um die Ausgabe in eine Textdatei zu schreiben:

```
bexio invoices list > rechnungen.txt
```

---

## Hilfe erhalten

Jeder Befehl unterstützt `--help`, um verfügbare Optionen anzuzeigen:

```
bexio --help
bexio invoices --help
bexio invoices list --help
```

---

## Mit KI-Assistenten verwenden (MCP)

bexio-cli enthält einen MCP-Server, über den KI-Assistenten direkt im Gespräch mit deinem Bexio-Konto kommunizieren können — keine Befehle auswendig lernen, kein Klicken.

Du kannst zum Beispiel sagen:
- *«Zeige mir alle offenen Rechnungen»*
- *«Erstelle Rechnungen für alle Daueraufträge»*
- *«Erfasse 2.5 Stunden auf Projekt 20 für heute»*
- *«Welche Lieferantenrechnungen sind diesen Monat noch offen?»*

Die KI entscheidet, welche Bexio-Aktionen nötig sind, und führt sie aus.

### Installation mit MCP-Unterstützung

Diesen einen Befehl ausführen — er installiert bexio-cli und konfiguriert automatisch alle KI-Tools, die auf deinem Computer gefunden werden:

```
curl -sSL https://raw.githubusercontent.com/noevu/bexio-cli/main/scripts/install_mcp.py | python3
```

Oder manuell installieren:

```
pipx install "git+https://github.com/noevu/bexio-cli[mcp]"
```

Dann mit dem gewünschten KI-Tool verbinden:

---

### Claude Desktop

Konfigurationsdatei:
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bexio": {
      "command": "bexio-mcp"
    }
  }
}
```

Claude Desktop neu starten. Bexio-Tools erscheinen automatisch im Tools-Panel.

---

### Claude Code (Terminal)

```
claude mcp add bexio -s user -- bexio-mcp
```

---

### Gemini CLI

Konfigurationsdatei: `~/.gemini/settings.json`

```json
{
  "mcpServers": {
    "bexio": {
      "command": "bexio-mcp",
      "args": []
    }
  }
}
```

---

### Codex CLI / Codex Desktop (OpenAI)

Konfigurationsdatei: `~/.codex/config.toml`

```toml
[mcp_servers.bexio]
type = "stdio"
command = "bexio-mcp"
args = []

[mcp_servers.bexio.env]
```

---

### Was die KI tun kann

Rund 35 Tools für Rechnungen, Aufträge, Offerten, Kontakte, Zahlungen, Artikel, Lieferantenrechnungen, Projekte, Zeiterfassung, Mahnungen und Stammdaten. Funktioniert mit jedem MCP-kompatiblen KI-Assistenten.

---

## Für Entwicklerinnen und Entwickler

Vollständige Befehlsreferenz, Contribution-Guide und Scripting-Beispiele:

```sh
git clone https://github.com/noevu/bexio-cli
cd bexio-cli
pip install -e .
python -m unittest discover -s tests -v
```

Das Tool basiert auf reinem Python (stdlib + `keyring`), ohne externe HTTP-Bibliotheken.

---

## Hilfe oder individuelle Automatisierung?

Jemanden gesucht, der das einrichtet, Bexio-Workflows automatisiert oder massgeschneiderte Integrationen entwickelt? [Noevu kontaktieren](https://noevu.ch/de/leistungen/ki-automatisierung) — eine Schweizer Webagentur spezialisiert auf [KI-gestützte Automatisierung für Schweizer KMU](https://noevu.ch/de/leistungen/ki-automatisierung).

## Lizenz

MIT
