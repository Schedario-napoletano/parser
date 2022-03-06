import argparse
import string
from collections import defaultdict
from typing import List, Optional, Iterator, Union, Dict, Tuple
import logging
import re

import json

import schedario

# This should be as low as possible such that it doesn't generate false-positives
#                  0.0005 is too low
INDENT_TOLERANCE = 0.0009
# Minimum indentation of big letters 'A', 'B', 'C', etc.
LETTER_MIN_INDENT = 60.0

logger = logging

Word = str
Qualifier = str

ABBREVIATIONS: Dict[str, Union[Qualifier, List[Qualifier]]] = {
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
RE_ABBR = re.compile(r"^(%s)((?:\s*\.?\s+|\.)di)?$" % "|".join(re.escape(abbr) for abbr in ABBREVIATIONS),
                     flags=re.UNICODE)


class Entry:
    def __init__(self, fragments: List[schedario.Fragment], initial_letter: str):
        self.fragments = list(schedario.compress_fragments(fragments))
        self.initial_letter = initial_letter

    def as_md(self, sep=" "):
        return sep.join(fragment.as_md() for fragment in self.fragments)


class BaseDefinition:
    template = ""

    def __init__(self, word: str, initial_letter: str, *, qualifier: Optional[Qualifier] = None):
        self.word = word
        self.qualifier = qualifier
        self.initial_letter = initial_letter

    def as_md(self):
        raise NotImplementedError()

    def as_dict(self):
        return {
            "template": self.template,
            "word": self.word,
            "qualifier": self.qualifier,
        }


class RawDefinition(BaseDefinition):
    template = "markdown"

    def __init__(self, word: str, initial_letter: str, fragments: List[schedario.Fragment],
                 *, qualifier: Optional[Qualifier] = None):
        super().__init__(word, initial_letter, qualifier=qualifier)
        self.fragments = fragments

    def as_md(self):
        q = f"_{self.qualifier}_ " if self.qualifier else ""
        return f"{self.word}: {q}{' '.join(fragment.as_md() for fragment in self.fragments)}"

    def as_dict(self):
        d = super().as_dict()
        d["markdown_text"] = ' '.join(fragment.as_md() for fragment in self.fragments)
        return d


class DerivativeDefinition(BaseDefinition):
    template = "derivative"

    def __init__(self, word: str, initial_letter: str, derive_from: str, **kwargs):
        super().__init__(word, initial_letter, **kwargs)
        self.derive_from = derive_from

    def as_md(self):
        if self.qualifier == "da":
            q = "da"
        else:
            q = self.qualifier + " di"

        return f"{self.word}: _{q}_ {self.derive_from}"

    def as_dict(self):
        d = super().as_dict()
        d["qualifier"] = "da" if self.qualifier == "da" else self.qualifier + " di"
        d["derive_from"] = self.derive_from
        return d


class AliasDefinition(BaseDefinition):
    template = "alias"

    def __init__(self, word: str, initial_letter: str, alias_of: str, **kwargs):
        super().__init__(word, initial_letter, **kwargs)
        self.alias_of = alias_of

    def as_md(self):
        return f"{self.word} → {self.alias_of}"

    def as_dict(self):
        d = super().as_dict()
        d["alias_of"] = self.alias_of
        return d


def parse_qualifier(s: str, word_text: str) -> Tuple[Optional[Qualifier], bool]:
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
            return qualifier, True

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


def parse_entries() -> Iterator[Entry]:
    current_letter: Optional[str] = None
    current_fragments: List[schedario.Fragment] = []

    known_letters = set(string.ascii_uppercase) - {"K", "W", "X", "Y"}

    for indent, fragment in schedario.parse_indented_fragments():
        if fragment.text.isspace():
            continue

        stripped_text = fragment.text.strip()

        # Big letters
        if indent > LETTER_MIN_INDENT and fragment.bold and re.match(r"[A-Z]$", stripped_text):
            if current_fragments:
                yield Entry(current_fragments, current_letter)
                current_fragments = []

            # This is a false-positive in the middle of a word. It's the only one in the whole document, so it's
            # simpler to ignore it here rather than make complicated code to automatically detect it.
            if current_letter == stripped_text == "P":
                continue

            current_letter = stripped_text
            print("Letter:", current_letter)
            known_letters.remove(current_letter)
            continue

        # fragment close to the left: start of a definition
        if indent <= INDENT_TOLERANCE:
            if not fragment.bold:
                # This letter contains only some text
                if current_letter == "J":
                    continue

                # This is the introductory text of the letter
                if current_letter == "G" and fragment.text.startswith("(di molte parole"):
                    continue

                if fragment.text.strip() == "N.B.":
                    continue

                raise RuntimeError("Expected bold fragment, got: %r" % fragment)

            # yield the current definition (if any) and start a new one
            if current_fragments:
                yield Entry(current_fragments, current_letter)
                current_fragments = []

        current_fragments.append(fragment)

    if current_fragments:
        yield Entry(current_fragments, current_letter)

    if known_letters:
        print("remaining letters:", known_letters)


def entry2definition(entry):
    word = entry.fragments[0]
    if not word.bold:
        print(entry.as_md())
        print(entry.fragments)
    assert word.bold

    word_text = word.text.strip(" :")
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
        else:
            print("CAN’T PARSE QUALIFIER:", fragments[0], "for word", word)

    # basic definition
    if derivative \
            and fragments[0].bold \
            and len(fragments) == 1 \
            and re.match(r"^([ ,’!a-zA-ZìàùèéÀÙÈÉ]+)\s*\.?$", plain_text):
        return DerivativeDefinition(word_text, entry.initial_letter, fragments[0].text.strip(), qualifier=qualifier)

    return RawDefinition(word_text, entry.initial_letter, fragments, qualifier=qualifier)


def parse_definitions():
    for entry in parse_entries():
        first_text = entry.fragments[0].text
        # false-positives
        if first_text in {"g:", "pepaiuola:", "svettare.", "le parole che iniziano o la"} \
                or first_text.startswith("nel passaggio dal latino,"):
            continue

        # See 1.pdf, p.114, on the middle left
        if first_text == ".:" and entry.fragments[1].text == "antico nome di Villaricca.":
            entry.fragments[0].text = "Panicuocolo:"
            entry.fragments[0].bold = True
            entry.fragments[1].italic = False

        yield entry2definition(entry)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json")
    opts = p.parse_args()

    json_path = opts.json
    json_definitions: Dict[str, List[dict]] = defaultdict(list)

    try:
        for definition in parse_definitions():
            if json_path:
                json_definitions[definition.initial_letter].append(definition.as_dict())
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    finally:
        if json_path:
            with open(json_path, "w") as f:
                json.dump(json_definitions, f, sort_keys=True, ensure_ascii=False)


if __name__ == '__main__':
    main()
