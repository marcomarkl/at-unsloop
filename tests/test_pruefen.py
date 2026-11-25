"""Tests für scripts/pruefen.py. Aufruf: python3 -m unittest discover tests"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SKRIPT = SKILL / "scripts" / "pruefen.py"

_spec = importlib.util.spec_from_file_location("pruefen", SKRIPT)
pruefen = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules["pruefen"] = pruefen
_spec.loader.exec_module(pruefen)

WORTLISTE = pruefen.lade_wortliste(pruefen.STANDARD_WORTLISTE)
ARTEFAKTE = pruefen.lade_artefakte(pruefen.STANDARD_ARTEFAKTE)

HG = "\u2013"  # Halbgeviertstrich
GV = "\u2014"  # Geviertstrich


def regeln(text: str) -> set[str]:
    return {t.regel for t in pruefen.pruefe_text(text, "test", WORTLISTE, ARTEFAKTE)}


class Striche(unittest.TestCase):
    def test_halbgeviert_und_geviert(self):
        self.assertIn("gedankenstrich", regeln(f"Das ist gut {HG} sehr gut."))
        self.assertIn("gedankenstrich", regeln(f"Das ist gut{GV}sehr gut."))

    def test_ohne_strich(self):
        self.assertEqual(regeln("Das ist gut, sehr gut."), set())

    def test_freistehender_bindestrich(self):
        self.assertIn("gedankenstrich", regeln("Die Strecke Wien - Graz ist kurz."))

    def test_markdown_liste_ist_kein_strich(self):
        self.assertEqual(regeln("- Punkt eins\n- Punkt zwei"), set())

    def test_liste_im_zitatblock(self):
        self.assertEqual(regeln("> - Punkt eins\n> - Punkt zwei"), set())
        self.assertIn("inline-header", regeln("> - **Status:** Alles gut."))

    def test_bindestrich_im_wort(self):
        self.assertEqual(regeln("Die E-Mail kam per Chat- und Teams-Nachricht."), set())


class Spannen(unittest.TestCase):
    def test_jahre(self):
        self.assertEqual(regeln("Von 2020-2024 lief das Projekt."), {"spanne"})
        self.assertEqual(regeln(f"Das Projekt lief 2020{HG}2024."), {"spanne"})

    def test_uhrzeit_seite_tag(self):
        self.assertIn("spanne", regeln("Geöffnet 9-12 Uhr."))
        self.assertIn("spanne", regeln("Siehe S. 12-18."))
        self.assertIn("spanne", regeln("Lieferung 12.-14. Jänner."))

    def test_iso_datum_und_geschaeftszahl(self):
        self.assertEqual(regeln("Stand 2026-11-25 im Akt."), set())
        self.assertEqual(regeln("Die GZ 2026-0.123.456 liegt vor."), set())

    def test_mit_bis(self):
        self.assertEqual(regeln("Von 2020 bis 2024 lief das Projekt."), set())


class Satzmuster(unittest.TestCase):
    def test_kontrast(self):
        self.assertIn("kontrast", regeln("Das ist nicht nur schnell, sondern auch billig."))
        self.assertEqual(regeln("Das ist schnell und billig."), set())

    def test_kontrast_nur_einmal(self):
        treffer = pruefen.pruefe_text(
            "Das ist nicht nur schnell, sondern auch billig.", "test", WORTLISTE, ARTEFAKTE
        )
        self.assertEqual(len([t for t in treffer if t.regel == "kontrast"]), 1)

    def test_verbindungswoerter(self):
        text = "Außerdem gilt das.\n\nZudem gilt jenes."
        self.assertIn("verbindungswort", regeln(text))
        self.assertNotIn("verbindungswort", regeln("Außerdem gilt das.\n\nDas gilt auch."))

    def test_doppelpunkt_pointe(self):
        self.assertIn("doppelpunkt-pointe", regeln("Wir haben getestet. Das Ergebnis: alles gut."))
        self.assertEqual(regeln("Die Ergebnisse der Prüfung sind gut."), set())

    def test_floskel_und_frage(self):
        self.assertIn("floskel", regeln("Kurz gesagt, es passt."))
        self.assertIn("floskel", regeln("Gerne! Der Bericht folgt."))
        self.assertIn("ueberleitungsfrage", regeln("Was bedeutet das konkret? Wir sparen Zeit."))

    def test_verben(self):
        self.assertIn("verb-ausweichend", regeln("Das Haus dient als Museum."))
        self.assertIn("verb-steif", regeln("Er verfasste drei Bücher."))
        self.assertEqual(regeln("Das Haus ist ein Museum. Er schrieb drei Bücher."), set())


class Form(unittest.TestCase):
    def test_inline_header(self):
        self.assertIn("inline-header", regeln("- **Flexibilität:** Das System passt sich an."))
        self.assertEqual(regeln("- Das System passt sich an."), set())

    def test_fett(self):
        text = "**Eins** und **zwei** und **drei** sind fett."
        self.assertIn("fett", regeln(text))
        self.assertEqual(regeln("Ein **wichtiger** Begriff in einem längeren Satz mit vielen Wörtern."), set())

    def test_emoji_trennlinie_titel(self):
        self.assertIn("emoji", regeln("\U0001F680 Start"))
        self.assertIn("trennlinie", regeln("Text\n\n---\n\nText"))
        self.assertIn("titel-grossschreibung", regeln("## Die Wichtigsten Vorteile Im Überblick"))
        self.assertEqual(regeln("## Die wichtigsten Vorteile im Überblick"), set())

    def test_frontmatter_ist_keine_trennlinie(self):
        self.assertEqual(regeln("---\nname: test\n---\n\nText."), set())

    def test_listenzeichen(self):
        self.assertIn("listenzeichen", regeln("• Punkt eins"))


class Zeichen(unittest.TestCase):
    def test_gemischte_anfuehrungszeichen(self):
        self.assertIn("anfuehrungszeichen", regeln('Er sagte „gut“ und dann "schlecht".'))

    def test_gerade_zeichen_im_code(self):
        self.assertEqual(regeln('Er sagte „gut“. Der Befehl lautet `echo "x"`.'), set())

    def test_codeblock(self):
        self.assertEqual(regeln(f'```\nDas ist gut {HG} sehr "gut"\n```'), set())

    def test_betrag(self):
        self.assertEqual(regeln(f"Das kostet 12,{HG} im Monat."), {"betrag"})

    def test_platzhalter(self):
        self.assertIn("platzhalter", regeln("Sehr geehrte [Name einfügen],"))
        self.assertEqual(regeln("Siehe [Name](https://example.at)."), set())


class Wortliste(unittest.TestCase):
    def test_bundesdeutsch(self):
        self.assertIn("wortliste", regeln("Im Januar treffen wir uns."))
        self.assertIn("wortliste", regeln("Das macht Sinn."))
        self.assertEqual(regeln("Im Jänner treffen wir uns."), set())

    def test_zitat_bleibt(self):
        self.assertEqual(regeln("Im Bericht steht „Treffen im Januar“."), set())

    def test_lehnuebersetzung_jahr(self):
        self.assertIn("lehnuebersetzung", regeln("Das war in 2024 so."))

    def test_artefakt(self):
        self.assertIn("artefakt", regeln("Quelle unter https://x.at/?utm_source=chatgpt.com"))
        self.assertIn("artefakt", regeln("Viele nutzen das [cite: 1] bereits."))

    def test_zitiertes_artefakt(self):
        self.assertEqual(regeln("Die Zitiermarke „[cite: 1]“ ist entfernt."), set())

    def test_pruefen_aus(self):
        text = f"<!-- pruefen:aus -->\nIm Januar {HG} sicher.\n<!-- pruefen:an -->\nIm Jänner."
        self.assertEqual(regeln(text), set())


class Kommandozeile(unittest.TestCase):
    def lauf(self, *args: str, eingabe: str = "", cwd: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SKRIPT), *args],
            input=eingabe.encode("utf-8"), capture_output=True, cwd=cwd,
        )

    def test_ohne_treffer(self):
        self.assertEqual(self.lauf("-", eingabe="Ein schlichter Satz.").returncode, 0)

    def test_mit_treffer(self):
        self.assertEqual(self.lauf("-", eingabe=f"Gut {HG} sehr gut.").returncode, 1)

    def test_fehlende_wortliste(self):
        ergebnis = self.lauf("--wortliste", "/gibt/es/nicht.md", "-", eingabe="Text.")
        self.assertEqual(ergebnis.returncode, 2)

    def test_anderer_arbeitsordner(self):
        with tempfile.TemporaryDirectory() as ordner:
            ergebnis = self.lauf("-", eingabe="Im Januar.", cwd=ordner)
        self.assertEqual(ergebnis.returncode, 1)
        self.assertIn("wortliste", ergebnis.stdout.decode("utf-8"))

    def test_unbekannte_regel(self):
        self.assertEqual(self.lauf("--ignoriere-regel", "gibtsnicht", "-", eingabe="x").returncode, 2)


if __name__ == "__main__":
    unittest.main()
