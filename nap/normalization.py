import re
from typing import Iterable, Iterator, Optional

from nap.models import Fragment

# don't include punctuation that can be part of words, such as ’ ("’a")
PUNCTUATION = {".", ",", ";", ":", "!", "?", "…", "..."}


def simplify_html(html: str) -> str:
    html = re.sub(r"</b>(\s*)<b>", "\\1", html)
    html = re.sub(r"</i>(\s*)<i>", "\\1", html)

    return html


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


"""
# ##### Old code for reference ##############################

def apply_font(text: str, font: str):
    if not text or text.isspace():
        return text

    if True:  # font in BOLD_FONTS:
        text = f"<b>{text}</b>"

    if True:  # font in ITALIC_FONTS:
        text = f"<i>text</i>"

    if True:  # font not in ALL_FONTS:
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

    import io
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
"""
