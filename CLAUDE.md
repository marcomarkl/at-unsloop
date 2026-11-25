# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Worum es geht

Dieses Repository ist ein Plugin mit einem einzigen Skill (`at-unsloop`) im offenen SKILL.md-Format. Der Skill enthält Schreibregeln für deutsche Texte, die weitergegeben werden: österreichisches Deutsch, keine Gedankenstriche, Ton und Form nach Zweck und Zielgruppe, keine maschinell wirkenden Muster. Er soll anbieterneutral in der Claude-App, in Cowork, in Claude Code, in Codex und in ChatGPT laufen. Ein Build-Schritt existiert nicht.

## Befehle

Der Skill liegt unter `plugins/at-unsloop/skills/at-unsloop/`, unten mit `$S` abgekürzt.

```bash
S=plugins/at-unsloop/skills/at-unsloop
python3 -m unittest discover tests                          # alle Tests
python3 -m unittest tests.test_pruefen.Spannen.test_jahre   # ein einzelner Test
python3 $S/scripts/pruefen.py README.md CLAUDE.md $S/SKILL.md $S/references/*.md   # Selbstprüfung, muss „Keine Treffer.“ melden
python3 $S/scripts/pruefen.py - < text.txt                  # beliebigen Text prüfen
python3 $S/scripts/pruefen.py --regeln                      # Regelnamen für --ignoriere-regel
claude plugin validate .                                    # Marktplatz für Claude Code
claude plugin validate plugins/at-unsloop                   # Plugin-Manifest für Claude Code
```

Exit-Codes des Skripts: 0 ohne Treffer, 1 mit Treffern, 2 bei Fehlern (fehlende oder unlesbare Wortliste, unbekannte Regel, keine Datei).

## Aufbau, der sich erst über mehrere Dateien erschließt

Zwei Ökosysteme teilen sich denselben Skill-Ordner, jedes mit eigenem Manifest und eigenem Marktplatz. Die ChatGPT-Desktop-App liest den Codex-Marktplatz, Arbeitsbereiche in ChatGPT können das Plugin direkt aus GitHub importieren. In ChatGPT im Browser wird für Einzelnutzer nur der Skill-Ordner als ZIP hochgeladen.

- Claude (Claude-App, Cowork und Claude Code): `.claude-plugin/marketplace.json` im Hauptordner und `plugins/at-unsloop/.claude-plugin/plugin.json`. Über das Claude-Konto installiert, gilt das Plugin auf allen Oberflächen. Über `claude plugin install` installiert, bleibt es lokal.
- Codex und ChatGPT-Desktop-App: `.agents/plugins/marketplace.json` im Hauptordner und `plugins/at-unsloop/plugin.json` im Format „Agent Plugins“ (Schema `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`, `additionalProperties: false`, erlaubt sind nur `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions`).

Beide Plugin-Manifeste tragen dieselben Angaben. Wer Version oder Beschreibung ändert, ändert beide. Beide finden den Skill über die Konvention `skills/<name>/SKILL.md`, ein `skills`-Feld braucht keines. Die Marktplätze verweisen mit `./plugins/at-unsloop` auf das Plugin. Ein Plugin direkt im Hauptordner (`"source": "./"`) bestätigt keine der beiden Dokumentationen.

`SKILL.md` wird bei jedem Auslösen geladen, die Dateien in `references/` nur bei Bedarf. Deshalb gehören Details, Listen und Beispiele nach `references/`, nicht in `SKILL.md`. `README.md` und diese Datei sind nur für Menschen und werden vom Skill nicht geladen.

Die Markdown-Tabellen in `references/` sind zugleich Daten des Prüfskripts, es gibt keine zweite Kopie im Code:

- `references/oesterreichisch.md`: Das Skript liest die erste Tabelle mit den Spalten `Statt | Besser | Prüfen`. Gemeldet werden nur Zeilen mit `ja`, Varianten in „Statt“ sind mit `/` getrennt.
- `references/artefakte.md`: Das Skript liest die erste Tabelle mit den Spalten `Muster | Herkunft`. Die Muster sind wörtliche Teilzeichenketten, Backticks werden entfernt.

Spaltennamen zu ändern bricht das Skript (Exit 2). Die Tabellen stehen zwischen `<!-- pruefen:aus -->` und `<!-- pruefen:an -->`, damit die Selbstprüfung ihre eigenen Einträge nicht meldet. Das Skript findet `references/` relativ zu seinem eigenen Ort (`scripts/` und `references/` liegen nebeneinander im Skill-Ordner), nicht relativ zum Arbeitsordner.

`pruefen.py` prüft zeilenweise auf einer maskierten Kopie der Zeile, die Positionen bleiben dabei erhalten. Ausgeblendet werden Inline-Code, URLs, Dateinamen, Zitate in „…“ und Zitatzeichen am Zeilenanfang. Ganz übersprungen werden Codeblöcke, `pruefen:aus`-Bereiche und die Frontmatter-Begrenzer. Zwei Prüfungen weichen davon ab:

- Artefakte werden mit sichtbaren URLs geprüft, weil Tracking-Parameter in Links stecken.
- Die Anführungszeichen-Prüfung lässt Zitate sichtbar, weil sie sonst nichts fände.

Spannen und Beträge werden vor den Gedankenstrichen geprüft, damit ein Strich nicht doppelt zählt. Neue Regeln brauchen einen Eintrag in `REGELN`, sonst funktioniert `--ignoriere-regel` nicht.

## Regeln für Änderungen

Alle Markdown-Dateien halten die Regeln des Skills selbst ein, die Selbstprüfung muss sauber bleiben. Absichtlich fehlerhafte Beispiele stehen nur in `pruefen:aus`-Blöcken, wie in `references/beispiele.md`.

In Python-Dateien und in dieser Datei stehen Halbgeviert- und Geviertstrich nur als Escape (`\u2013`, `\u2014`), nie als Zeichen. Beim Schreiben über die Werkzeuge wurden Escapes schon mehrfach zu echten Zeichen umgewandelt, und die Selbstprüfung bemerkt das in Inline-Code nicht. Nach dem Schreiben daher prüfen, etwa mit `grep -n 'u2013' $S/scripts/pruefen.py`, und bei Bedarf per Skript zurückersetzen.

Die Tests laden `pruefen.py` über `importlib` und tragen das Modul vor dem Ausführen in `sys.modules` ein. Ohne diesen Eintrag scheitert der `dataclass` mit `from __future__ import annotations`.

Vorgaben für `SKILL.md`:

- Das Frontmatter enthält nur `name` und `description`. Die Beschreibung bleibt unter 600 Zeichen und nennt nur Auslöser.
- Der Text bleibt bei rund 1.300 Wörtern. Eine Fassung mit 1.886 Wörtern war im Blindvergleich nicht besser, Details und Abläufe gehören nach `references/`.
- Er nennt keinen Anbieter oder Modellnamen.
- Er verweist nicht auf den Skill, aus dem er entstanden ist.
- Absolut sind nur zwei Regeln, keine erfundenen Fakten und keine Gedankenstriche. Alles andere ist als Tendenz mit Begründung formuliert.

Änderungen am Verhalten lassen sich nur mit echten Ausgaben belegen. Bisher bewährt hat sich, dem Modell `SKILL.md` und einige typische Aufträge zu geben (Kundenmail, Post ohne Zielgruppe, Teams-Nachricht, Überarbeitung mit Artefakten und Zitat, readme-Abschnitt), mit Opus und Fable. Die Ausgaben laufen dann durch `pruefen.py`.

Das ZIP für den Upload in ChatGPT im Browser enthält nur den Skill-Ordner, der Befehl steht im README.
