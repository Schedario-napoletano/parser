import os.path
import re
import string
from typing import Tuple, List, Optional, Iterator, cast, Iterable

import json
import pdfplumber
from pdfplumber.page import Page

from nap.models import Fragment, Entry
from nap.normalization import compress_fragments

SIMPLE_FONTS = {"Times-Roman", "ODNMDG+TTE2D674C8t00", "Courier", "ODNMDG+TTE2D6D9E8t00", "ODNMDG+TTE16BE550t00"}
BOLD_FONTS = {"Times-Bold", "Times-BoldItalic"}
ITALIC_FONTS = {"Times-Italic", "Times-BoldItalic", "ODNMDG+TTE2D6BEA8t00"}
ALL_FONTS = SIMPLE_FONTS | BOLD_FONTS | ITALIC_FONTS

MARGIN_TOP = 0.0
MARGIN_LEFT = 50.0
MARGIN_RIGHT = 50.0
MARGIN_BOTTOM = 70.0

# number of points from the top of the first column of the first page that we should ignore because they contain
# the title of the document.
START_TOP = 71.0

# This represents the max amount we tolerate on the left to consider a fragment as "first on the left".
# It should be as low as possible such that it doesn't create false-positives but also not too low so that it doesn't
# create false-negatives.
#                  0.0005 is too low
# suggietà: 0.00118
# troia:    0.00125
# sóracia:  0.00131
INDENT_TOLERANCE = 0.0014

# Minimum indentation of big letters 'A', 'B', 'C', etc.
LETTER_MIN_INDENT = 60.0

FILES = (
    # filename -> first page
    ("1.pdf", 5),
    ("2.pdf", 1),
)

COLUMN_ABSCISSES = (
    (None, 0.36),
    (0.37, 0.64),
    (0.65, None),
)
COLUMNS_COUNT = len(COLUMN_ABSCISSES)

FRAGMENTS_CACHE_PATH = "fragments.jsons"

IndentedFragment = Tuple[float, Fragment]


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


def get_column(page: Page, column_index: int) -> Page:
    x0, x1 = get_column_x0_x1(page.width, column_index)
    return page.crop((x0, MARGIN_TOP, x1, page.height - MARGIN_BOTTOM))


def _parse_fragments_from_column(column: Page, skip_intro=False):
    fragments = column.extract_words(
        # This is necessary to properly match the 'ε' fragments that, because they are in a different font, are never
        # well-aligned with the rest of the text on the same line.
        use_text_flow=True,
        # consider as 'words' close characters that share the same value for these properties
        extra_attrs=["fontname", "size"],
        # keep spaces so that we get a bunch of words at once
        keep_blank_chars=True,
        # don't try to match "words" across lines to avoid false-positives
        y_tolerance=1)

    index = 0

    if skip_intro:
        # Skip "S C H E D A R I O   N A P O L E T A N O" but not the letter "A"
        while True:
            fragment = fragments[index]
            top: float = fragment["top"]
            text: str = fragment["text"]
            if text.isspace() or (text.upper() == text and top < START_TOP):
                index += 1
                continue

            break

    fragments = fragments[index:]
    del index

    if not fragments:
        return

    minimum_x0: float = min(f["x0"] for f in fragments)

    for i, fragment in enumerate(fragments):
        indent = fragment["x0"] - minimum_x0
        font: str = fragment["fontname"]
        text = fragment["text"]

        if font == "Symbol" and text == "e":
            # Not sure what it is: it's rare and most of the time invisible. In one occurrence it looks like a ";".
            continue

        yield indent, Fragment(
            text=fragment["text"],
            bold=font in BOLD_FONTS,
            italic=font in ITALIC_FONTS)


def parse_fragments_from_page(page: Page, skip_intro=False):
    for column_index in range(COLUMNS_COUNT):
        column = get_column(page, column_index)
        yield from _parse_fragments_from_column(column, skip_intro=skip_intro if column_index == 0 else False)


def _parse_indented_fragments() -> Iterator[IndentedFragment]:
    for filename, first_page in FILES:
        print("File", filename)

        with pdfplumber.open(filename) as pdf:
            is_first_page = True
            for page_index, page in enumerate(pdf.pages[first_page:]):
                print("Page", page_index + first_page + 1)

                yield from parse_fragments_from_page(page, skip_intro=is_first_page)
                is_first_page = False


def parse_indented_fragments(cache=True) -> Iterator[IndentedFragment]:
    if not cache:
        return _parse_indented_fragments()

    if not os.path.isfile(FRAGMENTS_CACHE_PATH):
        with open(FRAGMENTS_CACHE_PATH, "w") as f:
            for indent, fragment in _parse_indented_fragments():
                json.dump({
                    # Ensure the text is at the beginning of the line to make the file easier to skim through by a human
                    "_text": fragment.text,
                    "bold": fragment.bold,
                    "indent": indent,
                    "italic": fragment.italic,
                }, f, sort_keys=True, ensure_ascii=False)
                f.write("\n")

    with open(FRAGMENTS_CACHE_PATH) as f:
        for line in f:
            d: dict = json.loads(line)
            yield d["indent"], Fragment(d["_text"], italic=d["italic"], bold=d["bold"])


def parse_entries(indented_fragments: Optional[Iterable[IndentedFragment]] = None) -> Iterator[Entry]:
    current_letter: Optional[str] = None
    current_fragments: List[Fragment] = []

    known_letters = set(string.ascii_uppercase) - {"K", "W", "X", "Y"}

    if indented_fragments is None:
        indented_fragments = parse_indented_fragments()

    for indent, fragment in indented_fragments:
        if fragment.text.isspace():
            continue

        stripped_text = fragment.text.strip()

        # Big letters
        if indent > LETTER_MIN_INDENT and fragment.bold and re.match(r"[A-Z]$", stripped_text):
            if current_fragments:
                yield Entry(compress_fragments(current_fragments), cast(str, current_letter))
                current_fragments = []

            # This is a false-positive in the middle of a word. It's the only one in the whole document, so it's
            # simpler to ignore it here rather than make complicated code to automatically detect it.
            if current_letter == stripped_text == "P":
                # TODO: maybe yield the entry, so it'll be merged with the rest of the text and avoid the
                #   'antico nome di Villaricca' issue in definitions.py.
                # yield Entry([fragment], "P")
                continue

            current_letter = stripped_text
            print("Letter:", current_letter)
            known_letters.remove(cast(str, current_letter))
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
                yield Entry(compress_fragments(current_fragments), cast(str, current_letter))
                current_fragments = []

        current_fragments.append(fragment)

    if current_fragments:
        yield Entry(compress_fragments(current_fragments), cast(str, current_letter))

    if known_letters:
        print("remaining letters:", known_letters)
