# at-unsloop

Ein Plugin mit Schreibregeln für deutsche Texte, die veröffentlicht oder weitergegeben werden. Es sorgt für österreichisches Deutsch ohne Gedankenstriche, richtet Ton und Form nach Zweck und Zielgruppe und vermeidet die Muster, an denen man maschinell erzeugte Texte erkennt.

Das Plugin enthält einen einzigen Skill im offenen SKILL.md-Format. Es funktioniert in Claude Code, in Codex und in der ChatGPT-Desktop-App. In der Claude-App und in ChatGPT im Browser wird der Skill als ZIP hochgeladen.

Diese Datei ist für Menschen gedacht. Das Modell lädt nur `SKILL.md` und bei Bedarf die Dateien in `references/`.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `.claude-plugin/marketplace.json` | Marktplatz für Claude Code |
| `.agents/plugins/marketplace.json` | Marktplatz für Codex und ChatGPT |
| `plugins/at-unsloop/.claude-plugin/plugin.json` | Plugin-Manifest für Claude Code |
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

### Claude Code

In einer Claude-Code-Sitzung genügt eine Zeile:

```
/plugin install at-unsloop --marketplace marcomarkl/at-unsloop
```

Ältere Versionen von Claude Code brauchen zwei Schritte:

```
/plugin marketplace add marcomarkl/at-unsloop
/plugin install at-unsloop@at-unsloop
```

### Codex und ChatGPT-Desktop-App

Den Marktplatz fügst du in der Codex-CLI hinzu:

```bash
codex plugin marketplace add marcomarkl/at-unsloop
```

Danach steht at-unsloop im Plugin-Verzeichnis von Codex und der ChatGPT-Desktop-App zur Installation bereit. Wie dieses Verzeichnis aussieht und in welchen Tarifen Plugins verfügbar sind, beschreibt die Dokumentation von OpenAI.

### Claude-App und ChatGPT im Browser

Dort wird nur der Skill als ZIP hochgeladen. Nach dem Klonen packst du ihn so:

```bash
git clone https://github.com/marcomarkl/at-unsloop.git
cd at-unsloop/plugins/at-unsloop/skills && zip -r at-unsloop.zip at-unsloop -x '*/__pycache__/*'
```

Das ZIP lädst du in den Einstellungen der jeweiligen App im Bereich für Skills hoch. Damit das Prüfskript läuft, muss dort die Code-Ausführung aktiv sein. Ohne sie wirkt der Skill trotzdem, das Modell prüft dann von Hand.

Sind andere Stil-Skills mit eigenen Regeln für deutsche Texte installiert, deaktivierst du sie besser. Sonst greifen zwei Regelwerke auf dieselben Texte, und das Modell muss zwischen ihnen vermitteln. Aus demselben Grund installierst du at-unsloop nur auf einem Weg je App.

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
