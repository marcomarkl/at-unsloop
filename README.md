# at-unsloop

Ein Skill mit Schreibregeln für deutsche Texte, die veröffentlicht oder weitergegeben werden. Er sorgt für österreichisches Deutsch ohne Gedankenstriche, richtet Ton und Form nach Zweck und Zielgruppe und vermeidet die Muster, an denen man maschinell erzeugte Texte erkennt. Das Format folgt dem offenen SKILL.md-Standard und funktioniert in Claude Code, in der Claude-App, in ChatGPT und in Codex.

Diese Datei ist für Menschen gedacht. Das Modell lädt nur `SKILL.md` und bei Bedarf die Dateien in `references/`.

## Aufbau

| Datei | Inhalt |
|---|---|
| `SKILL.md` | Kernregeln, werden bei jedem Auslösen geladen |
| `references/beispiele.md` | Vorher-Nachher-Paare für Überarbeitungen |
| `references/oesterreichisch.md` | Wortliste, Grammatik und Ausnahmen, zugleich Datenquelle des Prüfskripts |
| `references/artefakte.md` | Reste fremder Chatbots, die beim Überarbeiten entfernt werden |
| `scripts/pruefen.py` | Prüfskript, nur Python-Standardbibliothek |
| `tests/test_pruefen.py` | Tests für das Prüfskript |

## Installation

Zuerst das Repository klonen:

```bash
git clone https://github.com/marcomarkl/at-unsloop.git
```

In Claude Code genügt dann ein Symlink in den persönlichen Skill-Ordner, aufgerufen im Ordner, in den geklont wurde:

```bash
ln -s "$PWD/at-unsloop" ~/.claude/skills/at-unsloop
```

Für die Claude-App und für ChatGPT wird der Ordner als ZIP hochgeladen. Das Archiv enthält den Ordner `at-unsloop` mit `SKILL.md` auf oberster Ebene. Tests und Entwicklerdateien werden nicht gebraucht:

```bash
zip -r at-unsloop.zip at-unsloop -x 'at-unsloop/tests/*' 'at-unsloop/*/__pycache__/*' 'at-unsloop/.*' 'at-unsloop/CLAUDE.md'
```

Das ZIP lädst du in den Einstellungen der jeweiligen App im Bereich für Skills hoch. Damit das Prüfskript läuft, muss dort die Code-Ausführung aktiv sein. Ohne sie wirkt der Skill trotzdem, das Modell prüft dann von Hand. In Codex kommt der Ordner in dessen Skill-Verzeichnis, den genauen Ort nennt die Codex-Dokumentation.

Sind andere Stil-Skills mit eigenen Regeln für deutsche Texte installiert, deaktivierst du sie besser. Sonst greifen zwei Regelwerke auf dieselben Texte, und das Modell muss zwischen ihnen vermitteln.

## Prüfskript

Das Skript meldet Muster wie Gedankenstriche, Spannen mit Strich, Kontrastfiguren, Doppelpunkt-Pointen, bundesdeutsche Wörter, gemischte Anführungszeichen, Inline-Header-Listen und Reste fremder Werkzeuge. Treffer sind Hinweise, keine Urteile.

```bash
python3 scripts/pruefen.py text.md
python3 scripts/pruefen.py - < text.txt
python3 scripts/pruefen.py --json text.md
python3 scripts/pruefen.py --regeln
```

Mit `--ignoriere-regel NAME` lässt sich eine Regel abschalten, mehrfach möglich. Der Exit-Code ist 0 ohne Treffer, 1 mit Treffern und 2 bei Fehlern, etwa wenn die Wortliste fehlt.

Neue Wörter kommen in die Tabelle in `references/oesterreichisch.md`. Gemeldet werden nur Zeilen mit „ja“ in der Spalte „Prüfen“.

## Tests

```bash
python3 -m unittest discover tests
```

Zur Selbstprüfung läuft das Skript auch über die eigenen Dateien. Es darf dabei nichts finden:

```bash
python3 scripts/pruefen.py SKILL.md README.md CLAUDE.md references/*.md
```

## Lizenz

MIT, siehe `LICENSE`.

## Stand

November 2026.
