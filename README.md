# at-unsloop

Ein Plugin mit Schreibregeln für deutsche Texte, die veröffentlicht oder weitergegeben werden. Es sorgt für österreichisches Deutsch ohne Gedankenstriche, richtet Ton und Form nach Zweck und Zielgruppe und vermeidet die Muster, an denen man maschinell erzeugte Texte erkennt.

Das Plugin enthält einen einzigen Skill im offenen SKILL.md-Format. Als Plugin läuft es in der Claude-App, in Cowork, in Claude Code, in Codex und in der ChatGPT-Desktop-App. In ChatGPT im Browser wird der Skill als ZIP hochgeladen.

Diese Datei ist für Menschen gedacht. Das Modell lädt nur `SKILL.md` und bei Bedarf die Dateien in `references/`.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `.claude-plugin/marketplace.json` | Marktplatz für die Claude-App, Cowork und Claude Code |
| `.agents/plugins/marketplace.json` | Marktplatz für Codex und die ChatGPT-Desktop-App |
| `plugins/at-unsloop/.claude-plugin/plugin.json` | Plugin-Manifest für Claude |
| `plugins/at-unsloop/plugin.json` | Plugin-Manifest im Format „Agent Plugins“ für Codex und ChatGPT |
| `plugins/at-unsloop/skills/at-unsloop/` | der Skill selbst |
| `tests/` | Tests für das Prüfskript |

Im Skill-Ordner liegen:

| Datei | Inhalt |
|---|---|
| `SKILL.md` | Kernregeln, werden bei jedem Auslösen geladen |
| `references/beispiele.md` | Vorher-Nachher-Paare für Überarbeitungen |
| `references/oesterreichisch.md` | Wortliste, Grammatik und Ausnahmen, zugleich Datenquelle des Prüfskripts |
| `references/artefakte.md` | Reste fremder Chatbots, die beim Überarbeiten entfernt werden |
| `scripts/pruefen.py` | Prüfskript, nur Python-Standardbibliothek |

## Installation

### Claude-App, Cowork und Claude Code (empfohlen)

Über dein Claude-Konto steht das Plugin überall zur Verfügung, im Chat, in Cowork und in Claude Code:

1. In der Claude-App das Menü „Customize“ öffnen und den Reiter „Plugins“ wählen.
2. Im Bereich „Personal plugins“ auf „+“ klicken und „Add marketplace“ wählen.
3. `marcomarkl/at-unsloop` eingeben und das Plugin at-unsloop installieren.

Claude Code holt Plugins aus dem Konto beim Start einer Sitzung, solange es mit demselben Konto angemeldet ist.

### Nur Claude Code, ohne Konto

Wer at-unsloop nur auf einem Rechner in Claude Code nutzen will, installiert es dort direkt. In einer Claude-Code-Sitzung genügt eine Zeile:

```
/plugin install at-unsloop --marketplace marcomarkl/at-unsloop
```

Ältere Versionen von Claude Code brauchen zwei Schritte:

```
/plugin marketplace add marcomarkl/at-unsloop
/plugin install at-unsloop@at-unsloop
```

Diese Installation bleibt auf dem Rechner und erscheint nicht im Claude-Konto. Ist at-unsloop schon über das Konto installiert, lässt du sie weg, sonst lädt Claude Code den Skill doppelt.

### Codex und ChatGPT-Desktop-App

Den Marktplatz fügst du in der Codex-CLI hinzu:

```bash
codex plugin marketplace add marcomarkl/at-unsloop
```

Danach steht at-unsloop im Plugin-Verzeichnis von Codex zur Installation bereit. Die ChatGPT-Desktop-App zeigt den Marktplatz nach einem Neustart als eigene Quelle in ihrem Plugin-Verzeichnis, im Arbeitsmodus und in Codex innerhalb der App. Von dort installierst du das Plugin.

### ChatGPT-Arbeitsbereiche

In Business, Enterprise und Edu kann ein Admin das Plugin direkt aus dem GitHub-Repository `marcomarkl/at-unsloop` in den Arbeitsbereich importieren und aktuell halten. Die Mitglieder installieren es danach selbst.

### ChatGPT im Browser

Ob sich im Browser Plugins aus einem eigenen Marktplatz installieren lassen, beschreibt OpenAI nicht. Sicher funktioniert der Upload des Skills aus dem Plugin als ZIP. Nach dem Klonen packst du ihn so:

```bash
git clone https://github.com/marcomarkl/at-unsloop.git
cd at-unsloop/plugins/at-unsloop/skills && zip -r at-unsloop.zip at-unsloop -x '*/__pycache__/*'
```

In ChatGPT öffnest du in der Seitenleiste „Plugins“, dann das „Plugin Directory“ und dort den Reiter „Skills“. Über „Create“ und „Upload from your computer“ lädst du das ZIP hoch. ChatGPT prüft den Skill zuerst, danach ist er in der Regel sofort verfügbar. Zeigt die Oberfläche einen Schalter zum Aktivieren, schaltest du ihn ein.

Skills gibt es laut OpenAI in den Tarifen Business, Enterprise, Healthcare und Edu. In Arbeitsbereichen muss ein Admin das Hochladen von Skills erlauben. Damit das Prüfskript läuft, muss die Code-Ausführung aktiv sein. Ohne sie wirkt der Skill trotzdem, das Modell prüft dann von Hand.

Sind andere Stil-Skills mit eigenen Regeln für deutsche Texte installiert, deaktivierst du sie besser. Sonst greifen zwei Regelwerke auf dieselben Texte, und das Modell muss zwischen ihnen vermitteln.

## Prüfskript

Das Skript meldet Muster wie Gedankenstriche, Spannen mit Strich, Kontrastfiguren, Doppelpunkt-Pointen, bundesdeutsche Wörter, gemischte Anführungszeichen, Inline-Header-Listen und Reste fremder Werkzeuge. Treffer sind Hinweise, keine Urteile.

```bash
python3 plugins/at-unsloop/skills/at-unsloop/scripts/pruefen.py text.md
python3 plugins/at-unsloop/skills/at-unsloop/scripts/pruefen.py - < text.txt
python3 plugins/at-unsloop/skills/at-unsloop/scripts/pruefen.py --json text.md
python3 plugins/at-unsloop/skills/at-unsloop/scripts/pruefen.py --regeln
```

Mit `--ignoriere-regel NAME` lässt sich eine Regel abschalten, mehrfach möglich. Der Exit-Code ist 0 ohne Treffer, 1 mit Treffern und 2 bei Fehlern, etwa wenn die Wortliste fehlt.

Neue Wörter kommen in die Tabelle in `references/oesterreichisch.md`. Gemeldet werden nur Zeilen mit „ja“ in der Spalte „Prüfen“.

## Entwicklung

```bash
python3 -m unittest discover tests
claude plugin validate .
claude plugin validate plugins/at-unsloop
```

Zur Selbstprüfung läuft das Skript auch über die eigenen Dateien. Es darf dabei nichts finden:

```bash
python3 plugins/at-unsloop/skills/at-unsloop/scripts/pruefen.py README.md CLAUDE.md plugins/at-unsloop/skills/at-unsloop/SKILL.md plugins/at-unsloop/skills/at-unsloop/references/*.md
```

## Lizenz

MIT, siehe `LICENSE`.

## Stand

November 2026.
