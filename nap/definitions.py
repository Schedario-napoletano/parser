from typing import Optional, Tuple, Dict, Union, List, Iterable
import re

from nap.models import Qualifier, AliasDefinition, DerivativeDefinition, RawDefinition, Entry
from nap.entries import parse_entries

ABBREVIATIONS: Dict[str, Union[str, List[str]]] = {
    "abbr": "abbreviazione",
    "accr": "accrescitivo",
    "af": "aferesi",
    "agg": ["aggettivo", "aggettivale", "aggettivato"],
    "alt": "alterazione",
    "ant": "antico",
    "ap": "apocope",
    "artt": "preposizione articolata",
    "aus": "verbo ausiliare",
    "avv": ["avverbio", "locuzione avverbiale"],
    "c": "complemento",
    "card": "aggettivo numerale cardinale",
    "cond": "condizionale",
    "cong": "congiunzione",
    "congiunt": "congiuntivo",
    "contr": "contrazione",
    "corr": "correttamente",
    "det": "articolo determinativo",
    "dim": "diminuitivo",
    "distr": "aggettivo numerale distributivo",
    "ecc": "eccetera",
    "eccl": "ecclesiastico",
    "el": "elisione",
    "ep": "epentesi",
    "es": "esempio",
    "escl": ["esclamazione", "esclamativo"],
    "f": "sostantivo femminile",
    "fig": "figuratamente",
    "fr": "francese",
    "fraz": "aggettivo numerale frazionario",
    "freq": ["frequente", "frequentativo"],
    "fut": "futuro",
    "ger": "gerundio",
    "giapp": "giapponese",
    "gr": "greco",
    "impf": "imperfetto",
    "impt": "imperativo",
    "ind": "indicativo",
    "indef": "aggettivo e/o pronome indefinito",
    "indet": "articolo indeterminativo",
    "inf": "infantile",
    "ingl": "inglese",
    "inter": "interiezione",
    "interr": "aggettivo e/o pronome interrogativo",
    "intr": "verbo intransitivo",
    "ir": ["ironico", "ironicamente"],
    "it": ["italianizzazione", "italiano", "italianizzato"],
    "l": ["lettura", "leggere"],
    "lat": "latino",
    "m": "sostantivo maschile",
    "nap": "napoletano-e",
    "neg": "negazione",
    "neol": "neologismo",
    "onom": ["onomatopea", "onomatopeico"],
    "ord": "aggettivo numerale ordinale",
    "p": "passato",
    "part": "participio",
    "pl": "plurale",
    "poss": "aggettivo e/o pronome possessivo",
    "pr": "proverbio",
    "prep": "preposizione",
    "pres": "presente",
    "pron": ["pronome", "pronominale"],
    "prop": "nome proprio",
    "prov": "provenzale",
    "raff": "rafforzativo",
    "rem": "passato remoto",
    "rifl": "verbo riflessivo",
    "sec": "secolo",
    "sinc": "sincope",
    "s": "singolare",
    "sinon": "sinonimo",
    "sp": "spagnolo",
    "spr": "spregiativo",
    "sup": "superlativo",
    "ted": "tedesco",
    "tr": "verbo transitivo",
    "tronc": "troncamento",
    "v": ["vedere", "vedi"],
    "vezz": "vezzeggiativo",
    "voc": "vocativo",

    # additional, undocumented/combined ones
    "escl. d’impazienza": "esclamazione d’impazienza",
    "n.pr": "nome proprio",
    "n. pr": "nome proprio",
    "intr. pron": "verbo intransitivo pronominale",
    "intr. pr": "verbo intransitivo pronominale",
    "rifl. intr": "verbo intransitivo riflessivo",
    "intr. rifl": "verbo intransitivo riflessivo",
    "pr.f": "plurale femminile",
    "int": "interiezione",
    "m.pl": "sostantivo maschile plurale",
    "m. inv": "sostantivo maschile invariabile",
    "pl.m": "sostantivo maschile plurale",
    "m. pl": "sostantivo maschile plurale",
    "f.pl": "sostantivo femminile plurale",
    "f. pl": "sostantivo femminile plurale",
    "pl. f": "sostantivo femminile plurale",
    "pl.f": "sostantivo femminile plurale",
    "agg.f": "aggettivo femminile",
    "agg. f": "aggettivo femminile",
    "det. pl": "articolo determinativo plurale",
    "f. s.e pl": "sostantivo femminile singolare e plurale",
    # probably an alias of "impt" (imperativo)
    "imprt": "imperativo",

    "aferesi": "aferesi",
    "deformazione": "deformazione",
    "assimilazione": "assimilazione",
    "antica forma": "antica forma",

    "da": "da",

    "onom.  per": "onomatopea",

    "f. eagg": "sostantivo femminile e aggettivo",
    "m.eagg": "sostantivo maschile e aggettivo",
    "f. e agg": "sostantivo femminile e aggettivo",
    "m. e f": "sostantivo maschile e femminile",
    "pl m. e f": "sostantivo plurale maschile e femminile",
    "m. e agg": "sostantivo maschile e aggettivo",
    "m.e agg": "sostantivo maschile e aggettivo",
    "agg. e m": "sostantivo maschile e aggettivo",
    "m. e f. e agg": "sostantivo maschile e femminile e aggettivo",
    "m.-f. e agg": "sostantivo maschile e femminile e aggettivo",
    "m.- f. e agg": "sostantivo maschile e femminile e aggettivo",
    "m. e agg. e part": "sostantivo maschile e aggettivo e participio",
    "prep. e avv": "preposizione e avverbio",
    "agg. e part": "aggettivo e participio",
    "agg.  e part": "aggettivo e participio",
    "tr. e intr": "verbo transitivo e intransitivo",
    "tronc. e voc": "troncamento e vocativo",
}

RE_SEE_ALSO = re.compile(r"^v\s*\. +(\w+)\s*\.?$", flags=re.UNICODE)

# "abbr", "abbr.di", "abbr di", "abbr. di", "abbr . di"
RE_ABBR = re.compile(r"^(%s)\s*((?:\.|\.?\s+)di)?$" % "|".join(re.escape(abbr) for abbr in ABBREVIATIONS),
                     flags=re.UNICODE)


def parse_qualifier(s: str, word_text: str) -> Tuple[Optional[str], bool]:
    """
    Parse a string as qualifier. Return (qualifier, derivative?) where `derivative?` is True if the qualifier indicates
    a derivative of some other word.

    E.g.: "it": non-derivative
          "it di": derivative: it's an "it" of what's next in the definition text.
    """
    if m := RE_ABBR.match(s):
        abbr = m.group(1)
        ends_with_di = bool(m.group(2))
        qualifier = ABBREVIATIONS[abbr]

        if qualifier == "da":
            return "da", True

        if isinstance(qualifier, list):
            if abbr == "avv":
                if " " in word_text:
                    qualifier = "locuzione avverbiale"
                else:
                    qualifier = "avverbio"
            else:
                qualifier = qualifier[0]

        return qualifier, ends_with_di
    return None, False


def entry2definition(entry):
    word = entry.fragments[0]
    if not word.bold:
        print(entry.as_md())
        print(entry.fragments)
    assert word.bold

    # "hadda="
    word_text = word.text.strip(" :=")
    fragments = entry.fragments[1:]

    # sometimes the colon is in its own fragment
    if len(fragments) > 2 and fragments[0].text.strip() == ":":
        fragments = fragments[1:]

    if not fragments:
        if m := re.match(r"^(\w+): (.+)$", word_text, flags=re.UNICODE):
            # "**chessà: chi sa.**"
            word_text = m.group(1)
            word.text = m.group(2)
            fragments = [word]
        elif m := re.match(r"^(\w+) v\. (\w+)\.?$", word_text, flags=re.UNICODE):
            # **felariéllo v. filariéllo.**
            return AliasDefinition(m.group(1), entry.initial_letter, m.group(2))
        else:
            raise RuntimeError("Empty definition: %s" % entry.as_md())

    plain_text = " ".join(fragment.text for fragment in fragments).strip()

    if m := RE_SEE_ALSO.match(plain_text):
        return AliasDefinition(word_text, entry.initial_letter, m.group(1))

    qualifier: Optional[Qualifier] = None
    derivative = False

    # Arbitrary threshold: above this value this is probably not a qualifier
    if fragments[0].italic and len(fragments[0].text) < 20:
        prefix = fragments[0].text.strip(" .")
        qualifier, derivative = parse_qualifier(prefix, word_text=word_text)
        if qualifier:
            fragments = fragments[1:]

    # basic definition
    if derivative \
            and fragments[0].bold \
            and len(fragments) == 1 \
            and re.match(r"^([ ,’!a-zA-ZìàùèéÀÙÈÉ]+)\s*\.?$", plain_text):
        return DerivativeDefinition(word_text, entry.initial_letter, fragments[0].text.strip(" ."), qualifier=qualifier)

    return RawDefinition(word_text, entry.initial_letter, fragments, qualifier=qualifier)


def parse_definitions(entries: Optional[Iterable[Entry]] = None):
    if entries is None:
        entries = parse_entries()

    for entry in entries:
        first_text = entry.fragments[0].text.strip()
        # false-positives
        if first_text in {"g:", "pepaiuola:", "svettare.", "le parole che iniziano o la"} \
                or first_text.startswith("nel passaggio dal latino,"):
            continue

        # See 1.pdf, p.114, on the middle left
        if first_text == ".:" and entry.fragments[1].text == "antico nome di Villaricca.":
            entry.fragments[0].text = "Panicuocolo:"
            entry.fragments[0].bold = True
            entry.fragments[1].italic = False

        # TODO some entries are merged together: "viécchio-vècchia"

        yield entry2definition(entry)
