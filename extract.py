import argparse
import os
from typing import List, Tuple, Iterable, Optional

import logging
import pdfplumber
import tempfile

import subprocess

import re
from pdfplumber.page import Page
from pdfplumber.display import PageImage

MARGIN_TOP = 0.0
MARGIN_LEFT = 50.0
MARGIN_RIGHT = 50.0
MARGIN_BOTTOM = 70.0

COLUMN_ABSCISSES = (
    (None, 0.36),
    (0.37, 0.64),
    (0.65, None),
)

FILES = (
    # filename -> first page
    ("1.pdf", 5),
    ("2.pdf", 1),
)

logger = logging


class Definition:
    def __init__(self, word: str,
                 definition: Optional[str] = None,
                 alias_of: Optional[str] = None):
        self.word = word
        self.definition = definition
        self.alias_of = alias_of

    def __repr__(self):
        module = self.__class__.__module__
        prefix = "<%s%s %s" % (
            module + "." if module != "__main__" else "",
            self.__class__.__name__,
            repr(self.word),
        )
        body = ""
        suffix = ">"

        if self.definition:
            body = ": " + repr(self.definition)
        elif self.alias_of:
            body = " -> %s" % repr(self.alias_of)

        return prefix + body + suffix


def get_column_x0_x1(page_width: int, column_index: int) -> Tuple[float, float]:
    width = float(page_width)
    x0, x1 = COLUMN_ABSCISSES[column_index]
    if x0:
        x0 *= width
    else:
        x0 = MARGIN_LEFT

    if x1:
        x1 *= width
    else:
        x1 = width - MARGIN_RIGHT

    return x0, x1


def clean_text(text: str):
    return re.sub(r"\s+", " ", text).strip()


def make_definition(word_dict: dict, definition_dicts: List[dict]) -> Definition:
    word: str = word_dict["text"].strip(" :")
    definition = clean_text(" ".join(
        # TODO keep the semantic of the fontname as well
        part["text"] for part in definition_dicts
    ))

    if m := re.match(r"^v\s?\. (\w+)\.?", definition, flags=re.UNICODE):
        return Definition(word, alias_of=m.group(1))

    if definition.startswith("v") and not word.startswith("v"):
        logger.warning(f"Word {word} definition starts with v: {definition}")
    elif definition[-1] not in ".!":
        logger.warning(f"Word {word} definition doesn't end with a dot: {definition}")
    elif len(definition) < 4:
        logger.warning(f"Word {word} definition is very short: {definition}")

    return Definition(word, definition=definition)


# image = page.to_image()
# show_image(image.reset().debug_tablefinder())
def show_image(img: PageImage):
    """show_image(page.to_image())."""
    file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    file.close()
    filename = file.name
    img.save(filename)
    subprocess.call(["open", filename])
    input("[press enter when done]")
    os.unlink(filename)


"""
## Bugs ##

1.pdf, page[5], column 3, at the end:
    abbentà: --> [' ', 'intr.', ... 'v.', ' ', 'abbiénto); ', '2) ', 'v.', ' ']
    avventà. abbentato  --> ['v.', ' avventato. ']
The last bold word of the penultimate definition is at the beginning of the last word.

1.pdf, pages[7], column 3, near the end: "accettà"'s last word is not included in the definition

1.pdf, pages[9]
    Column 1
    !!! accocchiamiento // v.
    Column 2
    !!! acconnescennere // v.
    Column 0
    !!! accumpagnamiento // v.
    Column 1
    !!! accunnescennenza // v.
    !!! accundiscendenza. accunnescennere // v.
All these above represent a part where the text is justified like so:

    | some-long-word:             v. |
    |  some-long-alias.              |
    | some-long-word:             v. |
    |  some-long-alias.              |

"""


def parse_page(page: Page, skip_intro=False):
    for column_index in range(3):
        print("Column", column_index)
        # logger.info("Column %d", column_index)
        x0, x1 = get_column_x0_x1(page.width, column_index)
        column = page.crop((x0, MARGIN_TOP, x1, page.height - MARGIN_BOTTOM))
        yield from parse_column(column, skip_intro=skip_intro if column_index == 0 else False)


def parse_column(column: Page, skip_intro=False):
    parts = column.extract_words(
        # consider as 'words' close characters that share the same value for these properties
        extra_attrs=["fontname", "size"],
        # keep spaces so that we get a bunch of words at once
        keep_blank_chars=True)

    index = 0

    if skip_intro:
        # Skip "S C H E D A R I O   N A P O L E T A N O" + "A"
        while True:
            current: str = parts[index]["text"]
            if current.isspace() or current.upper() == current:
                index += 1
                continue

            break

    yield from parse_words(parts, index)


def parse_words(parts: List[dict], index: int) -> Iterable[Definition]:
    while index < len(parts):
        # now parts[index] is the start of a definition

        # strip leading spaces if any
        while parts[index]["text"].isspace():
            index += 1
            continue

        # definitions are in bold
        if parts[index]["fontname"] != "Times-Bold":
            raise RuntimeError("Word %s should be bold!" % repr(parts[index]))

        word = parts[index]

        # definition_top = word["top"]
        definition_left = word["x0"]

        word_parts: List[dict] = []

        index += 1
        # 'a: x0=56.6994773202
        # a:  x0=56.69996332300562
        while index < len(parts) and parts[index]["x0"] - 0.01 > definition_left:
            # print(parts[index]["text"], "<==", parts[index])

            word_parts.append(parts[index])
            index += 1

        yield make_definition(word, word_parts)


def parse_all():
    for filename, first_page in FILES:
        with pdfplumber.open(filename) as pdf:
            for page_index in range(first_page, len(pdf.pages)):
                page = pdf.pages[page_index]
                is_first_page = page_index == first_page
                yield from parse_page(page, skip_intro=is_first_page)


def main():
    p = argparse.ArgumentParser()
    p.parse_args()

    n = 0

    for word in parse_all():
        n += 1
        # print(word)

    print(n)


if __name__ == '__main__':
    main()
