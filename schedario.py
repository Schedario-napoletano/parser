import io
from dataclasses import dataclass
from typing import Tuple, List, Optional, Iterator, Iterable

import re

import pdfplumber
from pdfplumber.page import Page

MARGIN_TOP = 0.0
MARGIN_LEFT = 50.0
MARGIN_RIGHT = 50.0
MARGIN_BOTTOM = 70.0

# number of points from the top of the first column of the first page that we should ignore because they contain
# the title of the document.
START_TOP = 71.0

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


@dataclass
class Fragment:
    text: str
    bold: bool
    italic: bool

    def compress(self, strip_right=False):
        if strip_right:
            self.text = self.text.rstrip()

        if not self.text:
            self.bold = False
            self.italic = False
        elif self.text.isspace():
            self.text = " "
            self.bold = False
            self.italic = False

        return self

    def as_html(self):
        t = self.text
        if t.isspace() or not t:
            return t
        if self.bold:
            t = f"<b>{t}</b>"
        if self.italic:
            t = f"<i>{t}</i>"
        return t

    def as_md(self):
        """
        Return a markdown representation of the fragment. This can be convenient to have a concise representation
        in the terminal.
        """
        t = self.text
        if t.isspace() or not t:
            return t
        if self.bold:
            t = f"**{t}**"
        if self.italic:
            t = f"_{t}_"
        return t


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


def parse_indented_fragments() -> Iterator[Tuple[float, Fragment]]:
    for filename, first_page in FILES:
        print("File", filename)

        with pdfplumber.open(filename) as pdf:
            is_first_page = True
            for page_index, page in enumerate(pdf.pages[first_page:]):
                print("Page", page_index + first_page + 1)

                # for debugging
                # if filename == "1.pdf" and first_page + first_page + 1 < page_index + first_page + 1 < 72:
                #     continue

                # if filename == "1.pdf" and page_index in {10, 13, 31, 33, 37}:
                #     continue  # skip problematic pages for now

                yield from parse_fragments_from_page(page, skip_intro=is_first_page)
                is_first_page = False


def _is_punctuation(s: str):
    return s.strip() in PUNCTUATION


def compress_fragments(fragments: Iterable[Fragment]) -> Iterator[Fragment]:
    """
    Reduce the number of fragments in input by combining them as much as possible.
    """
    current_fragment: Optional[Fragment] = None
    for fragment in fragments:
        if current_fragment is None:
            current_fragment = fragment
            continue

        if fragment.bold == current_fragment.bold and fragment.italic == current_fragment.italic:
            current_fragment.text += fragment.text
            continue

        # Don't leave punctuation alone
        if not current_fragment.bold and not current_fragment.italic and _is_punctuation(fragment.text):
            current_fragment.text += fragment.text.strip()
            continue

        yield current_fragment.compress()
        current_fragment = fragment

    if current_fragment:
        # This is the last one: strip trailing spaces
        if current_fragment.text.isspace():
            return

        yield current_fragment.compress(strip_right=True)


# ##### Old code for reference ##############################

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


# XXX remove me once we've included all the useful code above
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

        # TODO import in compress_fragments
        if part_text in PUNCTUATION and current_word_fragments:
            # remove trailing spaces before punctuation
            current_word_fragments[-1] = current_word_fragments[-1].rstrip()

        # TODO import in compress_fragments
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

    # TODO idem
    text = text.strip()
    # remove spaces before dots and columns
    text = re.sub(r"\s+([.:])", "\\1", text)
    # add a space after commas if needed
    text = re.sub(r"([,;])(?=\w)", "\\1 ", text)

    # merge spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text
