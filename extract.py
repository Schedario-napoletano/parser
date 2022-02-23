import argparse
from typing import List, Tuple, Iterable, Optional

import logging

import re

import schedario

logger = logging

Word = str


class Definition: # XXX redo
    def __init__(self,
                 definition: Optional[str] = None,
                 alias_of: Optional[str] = None):
        self.definition = definition
        self.alias_of = alias_of
        if not self.definition and not self.alias_of:
            raise RuntimeError("Empty definition")

    def as_string(self) -> str:
        if self.definition:
            return self.definition
        if self.alias_of:
            return "v. " + self.alias_of

    def as_html(self) -> str:
        if self.definition:
            return self.definition
        if self.alias_of:
            return "&arr; <b>" + self.alias_of + "</b>"

    def __repr__(self):
        module = self.__class__.__module__
        prefix = "<%s%s " % (
            module + "." if module != "__main__" else "",
            self.__class__.__name__,
        )
        body = ""
        suffix = ">"

        if self.definition:
            body = "" + repr(self.definition)
        elif self.alias_of:
            body = "-> %s" % repr(self.alias_of)

        return prefix + body + suffix


Entry = Tuple[Word, Definition]



class SchedarioParser:
    def __init__(self):
        pass

    def parse(self) -> Iterable[Entry]: # XXX redo
        fragments = schedario.parse_fragments()

    def parse_column_words(self, parts: List[dict], index: int):
        while index < len(parts):
            # now parts[index] is the start of a definition

            # strip leading spaces if any
            while parts[index]["text"].isspace():
                index += 1
                continue

            # definitions are in bold
            # XXX definitions across pages
            if parts[index]["fontname"] != "Times-Bold":
                return
                # raise RuntimeError("Word %s should be bold!" % repr(parts[index]))

            word_dict = parts[index]

            # definition_top = word["top"]
            definition_left = word_dict["x0"]

            word_parts: List[dict] = []

            index += 1
            # 'a: x0=56.6994773202
            # a:  x0=56.69996332300562
            # diff:   0.00049
            while index < len(parts) and parts[index]["x0"] - 0.001 > definition_left:
                # print(parts[index]["text"], "<==", parts[index])

                word_parts.append(parts[index])
                index += 1

            word: str = word_dict["text"].strip(" :")

            yield word, self.make_definition(word_parts, word=word)

    def make_definition(self, definition_dicts: List[dict], word: str) -> Definition:
        definition = schedario.make_definition_text(definition_dicts)

        if m := re.match(r"^v\s?\. +(\w+)\.?", definition, flags=re.UNICODE):
            return Definition(alias_of=m.group(1).rstrip("."))

        # not really relevant with HTML markup
        # if definition.startswith("v") and not word.startswith("v"):
        #     logger.warning(f"Word {word} definition starts with v: {definition}")
        # elif len(definition) < 4:
        #     logger.warning(f"Word {word} definition is very short: {definition}")
        # elif definition[-1] not in ".!":
        #     logger.warning(f"Word {word} definition doesn't end with a dot: {definition}")

        return Definition(definition=definition)


def parse():
    return SchedarioParser().parse()


def main():
    p = argparse.ArgumentParser()
    p.parse_args()

    n = 0

    print("<html><head><style>dt { font-weight: bold; }</style></head><body><dl>")

    for word, definition in parse():
        print(f"<dt>{word}</dt><dd>{definition.as_html()}</dd>")
        n += 1
        # print(word)
        # print(n)

    print("</dl>")


if __name__ == '__main__':
    main()
