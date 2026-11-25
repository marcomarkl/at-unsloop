#!/usr/bin/env python3
"""Prüft deutsche Texte auf Muster, die maschinell wirken.

Aufruf:
    python3 pruefen.py DATEI [DATEI ...]
    python3 pruefen.py - <<'EOF'
    Text
    EOF

Treffer sind Hinweise, keine Urteile. Exit-Code 0 ohne Treffer, 1 mit
Treffern, 2 bei Fehlern (etwa wenn die Wortliste fehlt).

Nur Python-Standardbibliothek, ab Python 3.9.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SKILL_ORDNER = Path(__file__).resolve().parent.parent
STANDARD_WORTLISTE = SKILL_ORDNER / "references" / "oesterreichisch.md"
STANDARD_ARTEFAKTE = SKILL_ORDNER / "references" / "artefakte.md"

# Halbgeviertstrich und Geviertstrich, als Escape geschrieben, damit die
# Datei selbst keines der Zeichen enthält.
STRICHE = "\u2013\u2014"
STRICH_KLASSE = "[-\u2013\u2014]"

REGELN = {
    "gedankenstrich": "Komma, Punkt oder Klammer statt Gedankenstrich",
    "spanne": "Spanne mit „bis“ schreiben",
    "kontrast": "Kontrastfigur, prüfen ob sie nötig ist (Häufung meiden)",
    "verbindungswort": "mehrere Absätze beginnen mit Verbindungswörtern",
    "doppelpunkt-pointe": "Doppelpunkt als Pointe, besser als ganzer Satz",
    "floskel": "Floskel oder Chat-Rest, meist streichbar",
    "ueberleitungsfrage": "rhetorische Überleitungsfrage, besser direkt sagen",
    "inline-header": "Liste mit fettem Schlagwort und Doppelpunkt",
    "listenzeichen": "kopiertes Listenzeichen, Listenformat des Zielsystems verwenden",
    "fett": "viel Fettdruck, nur wenige Schlüsselbegriffe hervorheben",
    "anfuehrungszeichen": "Anführungszeichen uneinheitlich, im Fließtext „so“",
    "verb-ausweichend": "ausweichendes Verb, oft reicht „ist“ oder „hat“",
    "verb-steif": "steifes Verb, schlichteres nehmen",
    "wortliste": "bundesdeutsches Wort oder Lehnübersetzung",
    "lehnuebersetzung": "„in“ vor Jahreszahl, besser „2024“ oder „im Jahr 2024“",
    "betrag": "Betrag mit Strich, besser „12 Euro“ oder „€ 12,00“",
    "artefakt": "Rest eines fremden Werkzeugs, entfernen",
    "platzhalter": "Platzhalter im Text",
    "emoji": "Emoji am Zeilenanfang",
    "trennlinie": "dekorative Trennlinie",
    "titel-grossschreibung": "Überschrift mit englischer Großschreibung",
}


class PruefFehler(Exception):
    """Fehler, der das Prüfen unmöglich macht (Exit-Code 2)."""


@dataclass
class Treffer:
    datei: str
    zeile: int
    regel: str
    ausschnitt: str
    hinweis: str


# ---------------------------------------------------------------------------
# Datenquellen
# ---------------------------------------------------------------------------

def lies_tabelle(pfad: Path, pflichtspalten: tuple[str, ...]) -> list[dict[str, str]]:
    """Liest die erste Markdown-Tabelle, die alle Pflichtspalten hat."""
    if not pfad.is_file():
        raise PruefFehler(f"Datei nicht gefunden: {pfad}")
    kopf: list[str] | None = None
    daten: list[dict[str, str]] = []
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        s = zeile.strip()
        if not s.startswith("|"):
            if kopf is not None and daten:
                break
            continue
        zellen = [z.strip() for z in s.strip("|").split("|")]
        if kopf is None:
            if all(p in zellen for p in pflichtspalten):
                kopf = zellen
            continue
        if set("".join(zellen)) <= set("-: "):
            continue
        daten.append(dict(zip(kopf, zellen)))
    if kopf is None or not daten:
        spalten = ", ".join(pflichtspalten)
        raise PruefFehler(f"Keine Tabelle mit den Spalten {spalten} in {pfad}")
    return daten


def lade_wortliste(pfad: Path) -> list[tuple[re.Pattern[str], str, str]]:
    eintraege = []
    for zeile in lies_tabelle(pfad, ("Statt", "Besser", "Prüfen")):
        if zeile.get("Prüfen", "").strip().lower() != "ja":
            continue
        besser = zeile.get("Besser", "").strip()
        for form in zeile.get("Statt", "").split("/"):
            form = form.strip().strip("`")
            if not form:
                continue
            kern = re.escape(form).replace(r"\ ", r"\s+")
            muster = re.compile(r"\b" + kern + r"(?:e|en|er|es|n|s|in|innen)?\b", re.IGNORECASE)
            eintraege.append((muster, form, besser))
    if not eintraege:
        raise PruefFehler(f"Wortliste ohne Einträge mit „ja“: {pfad}")
    return eintraege


def lade_artefakte(pfad: Path) -> list[tuple[str, str]]:
    eintraege = []
    for zeile in lies_tabelle(pfad, ("Muster", "Herkunft")):
        muster = zeile.get("Muster", "").strip().strip("`")
        if muster:
            eintraege.append((muster, zeile.get("Herkunft", "").strip()))
    if not eintraege:
        raise PruefFehler(f"Artefaktliste ohne Einträge: {pfad}")
    return eintraege


# ---------------------------------------------------------------------------
# Maskieren: Bereiche, die nicht geprüft werden
# ---------------------------------------------------------------------------

RE_URL = re.compile(r"(?:https?://|www\.)\S+")
RE_DATEI = re.compile(
    r"[\w./-]+\.(?:md|txt|py|js|ts|json|ya?ml|csv|pdf|docx?|xlsx?|pptx?|html?|png|jpe?g|svg|zip)\b",
    re.IGNORECASE,
)
RE_INLINE_CODE = re.compile(r"`[^`\n]*`")
RE_ZITAT = re.compile(r"„[^“„\n]{0,300}“")
RE_ZITATBLOCK = re.compile(r"^\s*(?:>\s?)+")


def maskiere(zeile: str, zitate: bool, urls: bool = True) -> str:
    """Ersetzt nicht zu prüfende Bereiche durch Leerzeichen (Positionen bleiben).

    Markdown-Zitatzeichen am Zeilenanfang werden ebenfalls ausgeblendet, damit
    Listen in Zitatblöcken wie gewöhnliche Listen behandelt werden.
    """
    zeichen = list(zeile)
    block = RE_ZITATBLOCK.match(zeile)
    if block:
        for i in range(block.end()):
            zeichen[i] = " "
    muster = [RE_INLINE_CODE] + ([RE_URL, RE_DATEI] if urls else []) + ([RE_ZITAT] if zitate else [])
    for rx in muster:
        for m in rx.finditer(zeile):
            for i in range(m.start(), m.end()):
                zeichen[i] = " "
    return "".join(zeichen)


# ---------------------------------------------------------------------------
# Regeln
# ---------------------------------------------------------------------------

RE_SPANNEN = [
    # Jahre: 2020-2024, 1998-99. ISO-Daten und Geschäftszahlen ausgenommen.
    re.compile(
        r"(?<![\d.\-/])(?:1[89]|20)\d{2}\s?" + STRICH_KLASSE
        + r"\s?(?:(?:1[89]|20)\d{2}|\d{2})(?![\d\-/\u2013\u2014]|\.\d)"
    ),
    # Uhrzeiten: 9-12 Uhr, 9.30-11 Uhr
    re.compile(
        r"(?<![\d.])(?:[01]?\d|2[0-4])(?:[.:][0-5]\d)?\s?" + STRICH_KLASSE
        + r"\s?(?:[01]?\d|2[0-4])(?:[.:][0-5]\d)?\s?Uhr\b"
    ),
    # Seiten: S. 12-18, Seite 12-18
    re.compile(r"\b(?:S\.|Seiten?)\s?\d+\s?" + STRICH_KLASSE + r"\s?\d+\b"),
    # Tage: 12.-14. Jänner
    re.compile(r"(?<![\d.])\d{1,2}\.\s?" + STRICH_KLASSE + r"\s?\d{1,2}\.(?=\s|$)"),
]
RE_BETRAG = re.compile(r"\d," + STRICH_KLASSE + r"{1,2}")
RE_STRICH = re.compile("[" + STRICHE + "]")
RE_BINDESTRICH_FREI = re.compile(r"(?<=[^\s|]) -{1,2} (?=[^\s|])")

RE_KONTRAST = [
    re.compile(r"\bnicht nur\b[^.!?]{0,150}?\bsondern\b", re.IGNORECASE),
    re.compile(r"\b(?:kein|keine|keinen|keiner|keines|nicht)\b[^.!?;]{1,60},\s*sondern\b", re.IGNORECASE),
    re.compile(r"\bes geht nicht (?:nur )?um\b", re.IGNORECASE),
]

RE_VERBINDUNG_ANFANG = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:Darüber hinaus|Zusätzlich|Außerdem|Ferner|Zudem|Des Weiteren"
    r"|Weiterhin|Überdies|Nicht zuletzt|Letztendlich|Abschließend|Andererseits|Gleichzeitig)\b"
)

RE_DOPPELPUNKT_POINTE = re.compile(
    r"(?:^\s*(?:[-*+>]\s+)?|(?<=[.!?] ))"
    r"(?:Das Ergebnis|Die Folge|Der Grund|Die Antwort|Das Fazit|Die Lösung|Der Clou"
    r"|Das Problem|Die Wahrheit|Der Haken|Das Beste|Kurz|Klar ist|Fest steht|Heißt"
    r"|Bedeutet|Sprich|Konkret|Mit anderen Worten|Übersetzt|Unterm Strich)\s?:"
)

RE_FLOSKEL = re.compile(
    r"\b(?:Kurz gesagt|Kurzum|Der Punkt ist|Ehrlich gesagt|Es ist wichtig zu (?:beachten|betonen)"
    r"|Es ist erwähnenswert|Erwähnenswert ist|Es sei darauf hingewiesen"
    r"|Zusammenfassend lässt sich sagen|Abschließend lässt sich sagen|Tauchen wir ein"
    r"|Lass(?:t)? uns (?:eintauchen|einen Blick)|In der heutigen (?:schnelllebigen )?(?:Welt|Zeit)"
    r"|Gute Frage|Ich hoffe, (?:das|dies) hilft|Gerne helfe ich"
    r"|Hier ist (?:der|die|das) (?:Artikel|Text|Entwurf|Beitrag|überarbeitete))"
    r"|(?:^|(?<=\s))(?:Gerne|Gern|Natürlich|Selbstverständlich)!"
)

RE_UEBERLEITUNGSFRAGE = re.compile(
    r"\b(?:Was (?:bedeutet|heißt) das(?: konkret| für [^?]{1,40})?|Warum ist das (?:wichtig|relevant)"
    r"|Und (?:jetzt|nun|dann)|Was steckt dahinter|Woran liegt das|Wie funktioniert das"
    r"|Klingt (?:kompliziert|gut|einfach))\?"
)

RE_INLINE_HEADER = re.compile(
    r"^\s*(?:[-*+•]|\d+[.)])\s+(?:\*\*|__)[^*_\n]{1,60}?(?::(?:\*\*|__)|(?:\*\*|__)\s*:)"
)
RE_LISTENZEICHEN = re.compile(r"^\s*[•●▪◦]\s")
RE_FETT = re.compile(r"\*\*[^*\n]+?\*\*|__[^_\n]+?__")

RE_VERB_AUSWEICHEND = re.compile(
    r"\b(?:dient|dienen|diente|dienten|fungiert|fungieren|fungierte|fungierten)\s+als\b"
    r"|\bstellt\b[^.!?,;]{0,40}\bdar\b|\bverfügt über\b",
    re.IGNORECASE,
)
RE_VERB_STEIF = re.compile(
    r"\b(?:verfasste|verfassten|verstarb|verstarben|bediente sich|bedienten sich"
    r"|erachtete|erachteten|leistete Unterstützung|siedelte über)\b",
    re.IGNORECASE,
)

RE_LEHNUEBERSETZUNG_JAHR = re.compile(r"\bin (?:19|20)\d{2}\b(?!\s*(?:Fällen|Euro|Stück|Exemplaren))")

RE_PLATZHALTER = re.compile(
    r"\[[^\]\n]*?(?:einfügen|ergänzen|Platzhalter|Name|Datum|Firma|TBD|XXX)[^\]\n]*\](?!\()"
    r"|\bLorem ipsum\b|\bX{3,}\b"
)
RE_EMOJI = re.compile(
    r"^\s*(?:[-*+>]\s+|#{1,6}\s+)?[\U0001F300-\U0001FAFF☀-➿⭐✅]"
)
RE_TRENNLINIE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
RE_UEBERSCHRIFT = re.compile(r"^\s*#{1,6}\s+(.+?)\s*#*\s*$")
FUNKTIONSWOERTER = {
    "Und", "Oder", "Aber", "Im", "In", "Am", "An", "Auf", "Aus", "Bei", "Mit", "Nach",
    "Von", "Vom", "Zu", "Zum", "Zur", "Für", "Über", "Unter", "Vor", "Der", "Die", "Das",
    "Dem", "Den", "Des", "Ein", "Eine", "Einer", "Eines", "Einem", "Einen", "Als", "Wie",
    "Ohne", "Gegen", "Durch", "Bis", "Ist", "Sind",
}
RE_WORT = re.compile(r"[\wÄÖÜäöüß-]+")


def ausschnitt(zeile: str, start: int, ende: int, rand: int = 30) -> str:
    a = max(0, start - rand)
    b = min(len(zeile), ende + rand)
    text = zeile[a:b].strip()
    return ("…" if a > 0 else "") + text + ("…" if b < len(zeile) else "")


def pruefe_text(
    text: str,
    datei: str,
    wortliste: list[tuple[re.Pattern[str], str, str]],
    artefakte: list[tuple[str, str]],
    ignoriert: set[str] | None = None,
) -> list[Treffer]:
    ignoriert = ignoriert or set()
    treffer: list[Treffer] = []

    def melde(nr: int, regel: str, roh: str, start: int, ende: int, hinweis: str | None = None) -> None:
        if regel in ignoriert:
            return
        treffer.append(Treffer(datei, nr, regel, ausschnitt(roh, start, ende), hinweis or REGELN[regel]))

    zeilen = text.splitlines()

    # Aktive Zeilen bestimmen: Codeblöcke, pruefen:aus-Bereiche und
    # Frontmatter-Begrenzer werden übersprungen.
    aktiv: list[tuple[int, str] | None] = []
    im_code = False
    im_aus = False
    frontmatter = bool(zeilen) and zeilen[0].strip() == "---"
    for index, roh in enumerate(zeilen):
        nr = index + 1
        s = roh.strip()
        if frontmatter:
            if index == 0:
                aktiv.append(None)
                continue
            if s == "---":
                frontmatter = False
                aktiv.append(None)
                continue
        if "pruefen:aus" in s:
            im_aus = True
            aktiv.append(None)
            continue
        if "pruefen:an" in s:
            im_aus = False
            aktiv.append(None)
            continue
        if s.startswith("```") or s.startswith("~~~"):
            im_code = not im_code
            aktiv.append(None)
            continue
        if im_code or im_aus:
            aktiv.append(None)
            continue
        aktiv.append((nr, roh))

    absatzanfaenge: list[tuple[int, str, re.Match[str]]] = []
    neuer_absatz = True
    deutsche_zeichen = False
    gerade_zeichen: list[tuple[int, str, int]] = []
    englische_zeichen: list[tuple[int, str, int]] = []
    fett_woerter = 0
    fett_bereiche = 0
    erste_fett: tuple[int, str, int, int] | None = None
    woerter_gesamt = 0

    for eintrag in aktiv:
        if eintrag is None:
            neuer_absatz = True
            continue
        nr, roh = eintrag
        if not roh.strip():
            neuer_absatz = True
            continue

        maske = maskiere(roh, zitate=True)
        maske_ohne_zitat = maskiere(roh, zitate=False)
        ist_ueberschrift = bool(RE_UEBERSCHRIFT.match(roh))

        # Artefakte stecken oft in URLs, daher bleiben URLs hier sichtbar.
        # Zitierte Erwähnungen („[cite: 1]“ in einer Änderungsliste) zählen nicht.
        maske_artefakt = maskiere(roh, zitate=True, urls=False)
        for muster, herkunft in artefakte:
            pos = maske_artefakt.find(muster)
            if pos >= 0:
                melde(nr, "artefakt", roh, pos, pos + len(muster), f"Rest aus {herkunft}: {muster}")

        # Spannen und Beträge zuerst, damit ihre Striche nicht doppelt zählen.
        belegt: set[int] = set()
        for rx in RE_SPANNEN:
            for m in rx.finditer(maske):
                melde(nr, "spanne", roh, m.start(), m.end())
                belegt.update(range(m.start(), m.end()))
        for m in RE_BETRAG.finditer(maske):
            melde(nr, "betrag", roh, m.start(), m.end())
            belegt.update(range(m.start(), m.end()))
        for m in RE_STRICH.finditer(maske):
            if m.start() not in belegt:
                melde(nr, "gedankenstrich", roh, m.start(), m.end())
        for m in RE_BINDESTRICH_FREI.finditer(maske):
            if m.start() not in belegt:
                melde(nr, "gedankenstrich", roh, m.start(), m.end(), "freistehender Bindestrich als Gedankenstrich")

        kontrast_belegt: set[int] = set()
        for rx in RE_KONTRAST:
            for m in rx.finditer(maske):
                if kontrast_belegt.intersection(range(m.start(), m.end())):
                    continue
                melde(nr, "kontrast", roh, m.start(), m.end())
                kontrast_belegt.update(range(m.start(), m.end()))

        if neuer_absatz and not ist_ueberschrift:
            m = RE_VERBINDUNG_ANFANG.match(maske)
            if m:
                absatzanfaenge.append((nr, roh, m))
        neuer_absatz = False

        for m in RE_DOPPELPUNKT_POINTE.finditer(maske):
            melde(nr, "doppelpunkt-pointe", roh, m.start(), m.end())
        for m in RE_FLOSKEL.finditer(maske):
            melde(nr, "floskel", roh, m.start(), m.end())
        for m in RE_UEBERLEITUNGSFRAGE.finditer(maske):
            melde(nr, "ueberleitungsfrage", roh, m.start(), m.end())

        m = RE_INLINE_HEADER.match(maske)
        if m:
            melde(nr, "inline-header", roh, m.start(), m.end())
        m = RE_LISTENZEICHEN.match(maske)
        if m:
            melde(nr, "listenzeichen", roh, m.start(), m.end())

        for m in RE_FETT.finditer(maske):
            fett_bereiche += 1
            fett_woerter += len(RE_WORT.findall(m.group(0)))
            if erste_fett is None:
                erste_fett = (nr, roh, m.start(), m.end())
        woerter_gesamt += len(RE_WORT.findall(maske))

        if "„" in maske_ohne_zitat or "„" in roh:
            deutsche_zeichen = True
        pos = maske_ohne_zitat.find('"')
        if pos >= 0:
            gerade_zeichen.append((nr, roh, pos))
        pos = maske_ohne_zitat.find("”")
        if pos >= 0:
            englische_zeichen.append((nr, roh, pos))

        for m in RE_VERB_AUSWEICHEND.finditer(maske):
            melde(nr, "verb-ausweichend", roh, m.start(), m.end())
        for m in RE_VERB_STEIF.finditer(maske):
            melde(nr, "verb-steif", roh, m.start(), m.end())

        for muster, form, besser in wortliste:
            for m in muster.finditer(maske):
                melde(
                    nr, "wortliste", roh, m.start(), m.end(),
                    f"„{m.group(0)}“: besser „{besser}“ (Zitate und Eigennamen bleiben unverändert)",
                )
        for m in RE_LEHNUEBERSETZUNG_JAHR.finditer(maske):
            melde(nr, "lehnuebersetzung", roh, m.start(), m.end())

        for m in RE_PLATZHALTER.finditer(maske):
            melde(nr, "platzhalter", roh, m.start(), m.end())
        m = RE_EMOJI.match(maske)
        if m:
            melde(nr, "emoji", roh, m.start(), m.end())
        if RE_TRENNLINIE.match(roh):
            melde(nr, "trennlinie", roh, 0, len(roh))

        ue = RE_UEBERSCHRIFT.match(maske)
        if ue:
            titel = ue.group(1)
            for teil in titel.split(":"):
                woerter = teil.split()
                gross = [w for w in woerter[1:] if w.strip("„“,.?!()") in FUNKTIONSWOERTER]
                if gross:
                    melde(nr, "titel-grossschreibung", roh, 0, len(roh),
                          f"„{gross[0]}“ in der Überschrift kleinschreiben")
                    break

    if len(absatzanfaenge) >= 2:
        for nr, roh, m in absatzanfaenge:
            melde(nr, "verbindungswort", roh, m.start(), m.end())

    if erste_fett and fett_bereiche >= 3 and woerter_gesamt and fett_woerter / woerter_gesamt > 0.05:
        nr, roh, a, b = erste_fett
        anteil = round(100 * fett_woerter / woerter_gesamt)
        melde(nr, "fett", roh, a, b, f"{fett_bereiche} fette Stellen, rund {anteil} % der Wörter")

    if deutsche_zeichen and gerade_zeichen:
        nr, roh, pos = gerade_zeichen[0]
        melde(nr, "anfuehrungszeichen", roh, pos, pos + 1,
              "gerade Anführungszeichen neben „deutschen“, im Fließtext einheitlich „so“")
    elif gerade_zeichen:
        nr, roh, pos = gerade_zeichen[0]
        melde(nr, "anfuehrungszeichen", roh, pos, pos + 1,
              "gerade Anführungszeichen im Fließtext, besser „so“")
    if englische_zeichen:
        nr, roh, pos = englische_zeichen[0]
        melde(nr, "anfuehrungszeichen", roh, pos, pos + 1, "englisches Anführungszeichen, im Deutschen „so“")

    treffer.sort(key=lambda t: (t.datei, t.zeile))
    return treffer


# ---------------------------------------------------------------------------
# Kommandozeile
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    for strom in (sys.stdout, sys.stderr):
        if hasattr(strom, "reconfigure"):
            strom.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Prüft deutsche Texte auf maschinell wirkende Muster.")
    parser.add_argument("dateien", nargs="+", help="Dateien (Klartext oder Markdown) oder - für die Standardeingabe")
    parser.add_argument("--json", action="store_true", help="Treffer als JSON ausgeben")
    parser.add_argument("--ignoriere-regel", action="append", default=[], metavar="REGEL",
                        help="Regel überspringen, mehrfach möglich")
    parser.add_argument("--regeln", action="store_true", help="alle Regeln auflisten und beenden")
    parser.add_argument("--wortliste", type=Path, default=STANDARD_WORTLISTE, help=argparse.SUPPRESS)
    parser.add_argument("--artefakte", type=Path, default=STANDARD_ARTEFAKTE, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.regeln:
        for name, text in REGELN.items():
            print(f"{name}: {text}")
        return 0

    unbekannt = [r for r in args.ignoriere_regel if r not in REGELN]
    if unbekannt:
        print(f"Unbekannte Regel: {', '.join(unbekannt)}. Liste mit --regeln.", file=sys.stderr)
        return 2

    try:
        wortliste = lade_wortliste(args.wortliste)
        artefakte = lade_artefakte(args.artefakte)
        alle: list[Treffer] = []
        for datei in args.dateien:
            if datei == "-":
                text = sys.stdin.buffer.read().decode("utf-8")
                name = "<stdin>"
            else:
                pfad = Path(datei)
                if not pfad.is_file():
                    raise PruefFehler(f"Datei nicht gefunden: {datei}")
                text = pfad.read_text(encoding="utf-8")
                name = datei
            alle.extend(pruefe_text(text, name, wortliste, artefakte, set(args.ignoriere_regel)))
    except (PruefFehler, UnicodeDecodeError) as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(t) for t in alle], ensure_ascii=False, indent=2))
    elif alle:
        for t in alle:
            print(f"{t.datei}:{t.zeile}: [{t.regel}] {t.hinweis}")
            print(f"    {t.ausschnitt}")
        print(f"\n{len(alle)} Hinweise. Jeden einzeln abwägen, nicht blind ersetzen.")
    else:
        print("Keine Treffer.")
    return 1 if alle else 0


if __name__ == "__main__":
    sys.exit(main())
