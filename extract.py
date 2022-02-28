import argparse
import string
from typing import List, Optional, Iterator
import logging
import re

import clj

import schedario

# This should be as low as possible such that it doesn't generate false-positives
#                  0.0005 too low
INDENT_TOLERANCE = 0.0009
# Minimum indentation of big letters 'A', 'B', 'C', etc.
LETTER_MIN_INDENT = 60.0

logger = logging

Word = str
Qualifier = str

ABBREVIATIONS = [
    "abbr", "accr", "af", "agg", "alt", "ant", "ap", "artt", "aus", "avv",
    "c", "card", "cond", "cong", "congiunt", "contr", "corr",
    "det", "dim", "distr", "ecc", "eccl", "el", "ep", "es", "escl",
    "f", "fig", "fr", "fraz", "freq", "fut", "ger", "giapp", "gr",
    "impf", "impt", "ind", "indef", "indet", "inf", "ingl", "inter", "interr", "intr", "ir", "it",
    "l", "lat", "m", "nap", "neg", "neol", "onom", "ord", "p", "part", "pl", "poss", "pr", "prep",
    "pres", "pron", "prop", "prov", "raff", "rem", "rifl", "sec", "sinc", "s", "sinon", "sp", "spr",
    "sup", "ted", "tr", "tronc", "v", "vezz", "voc",

    # additional, undocumented ones
    "n.pr.", "n. pr.",  # nome proprio
    # FIXME we don't catch "Biase: _n.pr._  Biagio."
    #                      "Cànneta: _n.pr._  Candida."
    #                      "Capemonte: _n.pr._  Capodimonte."

    "imprt",  # probably an alias of "impt" (imperativo)
]

RE_SEE_ALSO = re.compile(r"^v\s*\. +(\w+)\s*\.?$", flags=re.UNICODE)

# Note: there's also "m. e agg." = 2 abbreviations
RE_ABBR = re.compile(r"^%s$" % "|".join(re.escape(abbr) for abbr in ABBREVIATIONS),
                     flags=re.UNICODE)


class Entry:
    def __init__(self, fragments: List[schedario.Fragment]):
        self.fragments = list(schedario.compress_fragments(fragments))

    def as_md(self, sep=" "):
        return sep.join(fragment.as_md() for fragment in self.fragments)


class Definition:
    def __init__(self, word: str, fragments: List[schedario.Fragment], *, qualifier: Optional[Qualifier] = None):
        self.word = word
        self.qualifier = qualifier
        self.fragments = fragments

    def as_md(self):
        q = f"[{self.qualifier}] " if self.qualifier else ""
        return f"{self.word}: {q}{' '.join(fragment.as_md() for fragment in self.fragments)}"


# NOTE: challenge this inheritance model if necessary
class SimpleDefinition(Definition):
    def __init__(self, word: str, definition: str, **kwargs):
        super().__init__(word, [], **kwargs)
        self.definition = definition

    def as_md(self):
        q = f"[{self.qualifier}] " if self.qualifier else ""
        return f"{self.word}: {q}{self.definition} [SIMPLE DEF]"


class AliasDefinition(Definition):
    def __init__(self, word: str, alias_of: str):
        super().__init__(word, [])
        self.alias_of = alias_of

    def as_md(self):
        return f"{self.word} → {self.alias_of}"


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
                yield Entry(current_fragments)
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

                raise RuntimeError("Expected bold fragment, got: %r" % fragment)

            # yield the current definition (if any) and start a new one
            if current_fragments:
                yield Entry(current_fragments)
                current_fragments = []

        current_fragments.append(fragment)

    if current_fragments:
        yield Entry(current_fragments)

    if known_letters:
        print("remaining letters:", known_letters)


def entry2definition(entry):
    word = entry.fragments[0]
    assert word.bold

    word_text = word.text.strip(" :")
    fragments = entry.fragments[1:]

    # sometimes the colon is in its own fragment
    if len(fragments) > 2 and fragments[0].text.strip() == ":":
        fragments = fragments[1:]

    if not fragments:
        raise RuntimeError("Empty definition: %s" % entry.as_md())

    plain_text = " ".join(fragment.text for fragment in fragments).strip()

    if m := RE_SEE_ALSO.match(plain_text):
        return AliasDefinition(word_text, m.group(1))

    if fragments[0].italic:
        prefix = fragments[0].text.strip(" .")
        if RE_ABBR.match(prefix):
            return Definition(word_text, fragments[1:], qualifier=prefix)

    if m := re.match(r"^([ ,’!a-zA-ZàùèéÀÙÈÉ]+)\s*\.?$", plain_text):
        return SimpleDefinition(word_text, m.group(1))

    return Definition(word_text, fragments)


def parse_definitions():
    for entry in parse_entries():
        yield entry2definition(entry)


def main():
    p = argparse.ArgumentParser()
    p.parse_args()

    # print("<html><head><style>dt { font-weight: bold; }</style></head><body><dl>")

    try:
        for definition in parse_definitions():
            if isinstance(definition, (AliasDefinition, SimpleDefinition)):
                continue

            if definition.qualifier:  # refine those as well, but later
                continue

            # Print only the definitions that we need to refine
            print(definition.as_md())
    except (KeyboardInterrupt, BrokenPipeError):
        pass


if __name__ == '__main__':
    main()
