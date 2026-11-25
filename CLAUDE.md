# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Worum es geht

Dieser Ordner ist selbst ein Skill im offenen SKILL.md-Format (`name: at-unsloop`). Er enthält Schreibregeln für deutsche Texte, die weitergegeben werden: österreichisches Deutsch, keine Gedankenstriche, Ton und Form nach Zweck und Zielgruppe, keine maschinell wirkenden Muster. Er soll anbieterneutral in Claude Code, der Claude-App, ChatGPT und Codex laufen. Ein Build-Schritt existiert nicht.

## Befehle

```bash
python3 -m unittest discover tests                          # alle Tests
python3 -m unittest tests.test_pruefen.Spannen.test_jahre   # ein einzelner Test
python3 scripts/pruefen.py SKILL.md README.md CLAUDE.md references/*.md   # Selbstprüfung, muss „Keine Treffer.“ melden
python3 scripts/pruefen.py - < text.txt                     # beliebigen Text prüfen
python3 scripts/pruefen.py --regeln                         # Regelnamen für --ignoriere-regel
```

Exit-Codes des Skripts: 0 ohne Treffer, 1 mit Treffern, 2 bei Fehlern (fehlende oder unlesbare Wortliste, unbekannte Regel).

## Aufbau, der sich erst über mehrere Dateien erschließt

`SKILL.md` wird bei jedem Auslösen geladen, die Dateien in `references/` nur bei Bedarf. Deshalb gehören Details, Listen und Beispiele nach `references/`, nicht in `SKILL.md`. `README.md` und diese Datei sind nur für Menschen und werden vom Skill nicht geladen.

Die Markdown-Tabellen in `references/` sind zugleich Daten des Prüfskripts, es gibt keine zweite Kopie im Code:

- `references/oesterreichisch.md`: Das Skript liest die erste Tabelle mit den Spalten `Statt | Besser | Prüfen`. Gemeldet werden nur Zeilen mit `ja`, Varianten in „Statt“ sind mit `/` getrennt.
- `references/artefakte.md`: Das Skript liest die erste Tabelle mit den Spalten `Muster | Herkunft`. Die Muster sind wörtliche Teilzeichenketten, Backticks werden entfernt.

Spaltennamen zu ändern bricht das Skript (Exit 2). Die Tabellen stehen zwischen `<!-- pruefen:aus -->` und `<!-- pruefen:an -->`, damit die Selbstprüfung ihre eigenen Einträge nicht meldet.

`pruefen.py` prüft zeilenweise auf einer maskierten Kopie der Zeile, die Positionen bleiben dabei erhalten. Ausgeblendet werden Inline-Code, URLs, Dateinamen, Zitate in „…“ und Zitatzeichen am Zeilenanfang. Ganz übersprungen werden Codeblöcke, `pruefen:aus`-Bereiche und die Frontmatter-Begrenzer. Zwei Prüfungen weichen davon ab:

- Artefakte werden mit sichtbaren URLs geprüft, weil Tracking-Parameter in Links stecken.
- Die Anführungszeichen-Prüfung lässt Zitate sichtbar, weil sie sonst nichts fände.

Spannen und Beträge werden vor den Gedankenstrichen geprüft, damit ein Strich nicht doppelt zählt. Neue Regeln brauchen einen Eintrag in `REGELN`, sonst funktioniert `--ignoriere-regel` nicht.

## Regeln für Änderungen

Alle Markdown-Dateien halten die Regeln des Skills selbst ein, die Selbstprüfung muss sauber bleiben. Absichtlich fehlerhafte Beispiele stehen nur in `pruefen:aus`-Blöcken, wie in `references/beispiele.md`.

In Python-Dateien stehen Halbgeviert- und Geviertstrich nur als Escape (`–`, `—`), nie als Zeichen. Beim Schreiben über die Werkzeuge wurden Escapes schon einmal zu echten Zeichen umgewandelt. Nach dem Schreiben daher prüfen, etwa mit `grep -n 'u2013' scripts/pruefen.py`, und bei Bedarf zurückersetzen.

Die Tests laden `scripts/pruefen.py` über `importlib` und tragen das Modul vor dem Ausführen in `sys.modules` ein. Ohne diesen Eintrag scheitert der `dataclass` mit `from __future__ import annotations`.

Vorgaben für `SKILL.md`:

- Das Frontmatter enthält nur `name` und `description`. Die Beschreibung bleibt unter 600 Zeichen und nennt nur Auslöser.
- Der Text bleibt bei rund 1.800 Wörtern.
- Er nennt keinen Anbieter oder Modellnamen.
- Er verweist nicht auf den Skill, aus dem er entstanden ist.
- Absolut sind nur zwei Regeln, keine erfundenen Fakten und keine Gedankenstriche. Alles andere ist als Tendenz mit Begründung formuliert.

Änderungen am Verhalten lassen sich nur mit echten Ausgaben belegen. Bisher bewährt hat sich, dem Modell `SKILL.md` und einige typische Aufträge zu geben (Kundenmail, Post ohne Zielgruppe, Teams-Nachricht, Überarbeitung mit Artefakten und Zitat, readme-Abschnitt), mit Opus und Fable. Die Ausgaben laufen dann durch `pruefen.py`.

Das ZIP für den Upload enthält weder `tests/` noch diese Datei, der Befehl steht im README.
