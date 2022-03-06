import re
from typing import Iterable, Iterator, Optional

from nap.models import Fragment

# don't include punctuation that can be part of words, such as ’ ("’a")
PUNCTUATION = {".", ",", ";", ":", "!", "?", "…", "..."}


def _is_punctuation(s: str):
    return s.strip() in PUNCTUATION


def compress_fragment(fragment, strip_right=False):
    """
    Compress a fragment in-place.
    """
    fragment.text = re.sub(r"\s+", " ", fragment.text)
    # # remove spaces before dots and columns
    fragment.text = re.sub(r" ([.:])", "\\1", fragment.text)
    # add a space after commas if needed
    fragment.text = re.sub(r"([,;])(?=\w)", "\\1 ", fragment.text, flags=re.UNICODE)

    if strip_right:
        fragment.text = fragment.text.rstrip()

    if _is_punctuation(fragment.text) or not fragment.text:
        fragment.strip_formatting()
    elif fragment.text.isspace():
        fragment.text = " "
        fragment.strip_formatting()

    return fragment


def compress_fragments(fragments: Iterable[Fragment]) -> Iterator[Fragment]:
    """
    Reduce the number of fragments in input by combining them as much as possible.
    """
    # TODO: '<b>foo</b>', ' ', '<b>bar</b>' == '<b>foo bar</b>'
    # TODO: '<i>foo</i>', ' . bar' == '<i>foo</i>', '. bar'

    current_fragment: Optional[Fragment] = None
    for fragment in fragments:
        fragment = compress_fragment(fragment)

        if current_fragment is None:
            current_fragment = fragment
            continue

        # same formatting: append it
        if fragment.bold == current_fragment.bold and fragment.italic == current_fragment.italic:
            current_fragment.text += fragment.text
            continue

        if _is_punctuation(fragment.text):
            # Don't leave punctuation alone
            current_fragment.text = current_fragment.text.rstrip() + fragment.text.lstrip()
            continue

        current_fragment = compress_fragment(current_fragment)
        if current_fragment.text:
            yield current_fragment
        current_fragment = fragment

    if current_fragment:
        # This is the last one: strip trailing spaces
        current_fragment = compress_fragment(current_fragment, strip_right=True)
        if current_fragment.text:
            yield current_fragment
