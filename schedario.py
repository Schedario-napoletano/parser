import io
from collections import namedtuple
from typing import Tuple, List, Optional

import re

import pdfplumber
from pdfplumber.page import Page

MARGIN_TOP = 0.0
MARGIN_LEFT = 50.0
MARGIN_RIGHT = 50.0
MARGIN_BOTTOM = 70.0

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

# don't include punctuation that can be part of words, such as ’ ("’a")
PUNCTUATION = {".", ",", ";", ":", "!", "?", "…", "..."}

SIMPLE_FONTS = {"Times-Roman", "ODNMDG+TTE2D674C8t00", "Courier", "ODNMDG+TTE2D6D9E8t00", "ODNMDG+TTE16BE550t00"}
BOLD_FONTS = {"Times-Bold", "Times-BoldItalic"}
ITALIC_FONTS = {"Times-Italic", "Times-BoldItalic", "ODNMDG+TTE2D6BEA8t00"}
ALL_FONTS = SIMPLE_FONTS | BOLD_FONTS | ITALIC_FONTS

Fragment = namedtuple("Fragment", ("indent", "text", "bold", "italic"))


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
        # consider as 'words' close characters that share the same value for these properties
        extra_attrs=["fontname", "size"],
        # keep spaces so that we get a bunch of words at once
        keep_blank_chars=True,
        # don't try to match "words" across lines to avoid false-positives
        y_tolerance=1)

    index = 0

    if skip_intro:
        # Skip "S C H E D A R I O   N A P O L E T A N O" + "A"
        # TODO we need to skip the other letters as well
        while True:
            current: str = fragments[index]["text"]
            if current.isspace() or current.upper() == current:
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

        yield Fragment(
            indent=indent,
            text=fragment["text"],
            bold=font in BOLD_FONTS,
            italic=font in ITALIC_FONTS)


def parse_fragments_from_page(page: Page, skip_intro=False):
    for column_index in range(COLUMNS_COUNT):
        column = get_column(page, column_index)
        yield from _parse_fragments_from_column(column,skip_intro=skip_intro if column_index == 0 else False)


def parse_fragments():
    for filename, first_page in FILES:
        print("File", filename)

        with pdfplumber.open(filename) as pdf:
            is_first_page = True
            for page_index, page in enumerate(pdf.pages[first_page:]):
                print("Page", page_index + first_page + 1)

                # if filename == "1.pdf" and page_index in {10, 13, 31, 33, 37}:
                #     continue  # skip problematic pages for now

                yield from parse_fragments_from_page(page, skip_intro=is_first_page)
                is_first_page = False


def apply_font(text: str, font: str):
    if not text or text.isspace():
        return text

    if font in BOLD_FONTS:
        text = f"<b>{text}</b>"

    if font in ITALIC_FONTS:
        text = f"<i>text</i>"

    if font not in ALL_FONTS:
        print(f"Unknown font {font} for text {repr(text)}")

    return text


def make_definition_text(word_dicts: List[dict]):
    words = []
    current_word_fragments: List[str] = []
    current_font: Optional[str] = None

    def append_current_word_fragments():
        if current_word_fragments:
            words.append(apply_font("".join(current_word_fragments).strip(), current_font))

    for word_dict in word_dicts:
        font = word_dict["fontname"]
        part_text = word_dict["text"]

        if not current_font:
            if not part_text.isspace():
                current_font = font
            words.append(apply_font(part_text, font))
            continue

        if part_text in PUNCTUATION and current_word_fragments:
            # remove trailing spaces before punctuation
            current_word_fragments[-1] = current_word_fragments[-1].rstrip()

        if current_font != font:
            if part_text in PUNCTUATION:
                # include punctuation in the current font part otherwise we have things like:
                #   "blabla<b>.</b>"
                current_word_fragments.append(part_text)
                continue

            append_current_word_fragments()
            current_word_fragments = []
            current_font = font

        current_word_fragments.append(part_text)

    append_current_word_fragments()

    text_writer = io.StringIO()

    first = True
    for word in words:
        if first:
            first = False
        elif word not in PUNCTUATION:
            text_writer.write(" ")
        text_writer.write(word)

    text_writer.seek(0)
    text = text_writer.read()

    text = text.strip()
    # remove spaces before dots and columns
    text = re.sub(r"\s+([.:])", "\\1", text)
    # add a space after commas if needed
    text = re.sub(r"([,;])(?=\w)", "\\1 ", text)

    # merge spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text
