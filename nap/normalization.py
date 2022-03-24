import re
from typing import Iterable, Iterator, Optional

from nap.models import Fragment

# don't include punctuation that can be part of words, such as ’ ("’a")
PUNCTUATION = {".", ",", ";", ":", "!", "?", "…", "..."}


def _is_punctuation(s: str):
    return s.strip() in PUNCTUATION


def compress_fragment(fragment: Fragment, *, strip_left=False, strip_right=False):
    """
    Compress a fragment in-place.
    """
    fragment.text = re.sub(r"\s+", " ", fragment.text)
    # # remove spaces before dots, colons, closing parentheses
    fragment.text = re.sub(r"\s+([.:)])", "\\1", fragment.text)
    # add a space after commas if needed; remove spaces before
    fragment.text = re.sub(r"\s*([,;])(?=\w)", "\\1 ", fragment.text, flags=re.UNICODE)
    # remove spaces after open parentheses
    fragment.text = re.sub(r"([(])\s+", "\\1", fragment.text)

    if strip_left:
        fragment.text = fragment.text.lstrip()

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
    current_fragment: Optional[Fragment] = None
    is_first = True

    for fragment in fragments:
        fragment = compress_fragment(fragment)

        if current_fragment is None:
            current_fragment = fragment
            continue

        # same formatting or space: append it
        # Note this means "<b>foo</b> <i>bar</i>" may become "<b>foo </b><i>bar</i>"
        if (fragment.bold == current_fragment.bold and fragment.italic == current_fragment.italic) \
                or fragment.text.isspace():
            current_fragment.text += fragment.text
            continue

        if _is_punctuation(fragment.text):
            # Don't leave punctuation alone
            # Note this could be challenged: "<i>foo</i>." may be better than "<i>foo.</i>".
            current_fragment.text = current_fragment.text.rstrip() + fragment.text.lstrip()
            continue

        current_fragment = compress_fragment(current_fragment, strip_left=is_first)
        if current_fragment.text:
            is_first = False
            yield current_fragment
        current_fragment = fragment

    if current_fragment:
        # This is the last one: strip trailing spaces
        current_fragment = compress_fragment(current_fragment, strip_left=is_first, strip_right=True)
        if current_fragment.text:
            yield current_fragment
