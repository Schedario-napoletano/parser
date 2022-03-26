import pytest

import nap.normalization as n
from nap.models import Fragment


@pytest.fixture
def word():
    return Fragment(text="parola")


def test_compress_fragment(word):
    assert word == n.compress_fragment(word)

    assert Fragment("a b") == n.compress_fragment(Fragment("a         b"))
    assert Fragment("a b") == n.compress_fragment(Fragment("a \n b"))
    assert Fragment("a: parola.") == n.compress_fragment(Fragment("a : parola  ."))
    assert Fragment("a, b") == n.compress_fragment(Fragment("a,b"))
    assert Fragment("a, b") == n.compress_fragment(Fragment("a ,b"))

    assert Fragment("a ") == n.compress_fragment(Fragment("a    "))
    assert Fragment("a") == n.compress_fragment(Fragment("a    "), strip=True)
    assert Fragment(" a ") == n.compress_fragment(Fragment("   a "))
    assert Fragment("a") == n.compress_fragment(Fragment("   a "), strip=True)

    assert Fragment(".") == n.compress_fragment(Fragment(".", bold=True, italic=True))

    f = Fragment("'", bold=True)
    assert f == n.compress_fragment(f)

    assert Fragment(" ") == n.compress_fragment(Fragment("   \n ", italic=True))

    assert Fragment("(hey)") == n.compress_fragment(Fragment("( hey   )"))


def test_compress_fragments(word):
    assert [] == list(n.compress_fragments([]))
    assert [word] == list(n.compress_fragments([word]))

    assert [Fragment("a b")] == list(n.compress_fragments([Fragment("a"), Fragment(" b")]))
    assert [Fragment("a b")] == list(n.compress_fragments([Fragment("a   "), Fragment(" b")]))

    assert [Fragment("a b", italic=True)] \
           == list(n.compress_fragments([Fragment("a   ", italic=True), Fragment(" b", italic=True)]))

    assert [Fragment("a", italic=True), Fragment("b")] \
           == list(n.compress_fragments([Fragment("a   ", italic=True), Fragment(" b")]))

    assert [Fragment("a", italic=True), Fragment("b", bold=True)] \
           == list(n.compress_fragments([Fragment("a   ", italic=True), Fragment(" b", bold=True)]))

    assert [Fragment("a.", italic=True)] \
           == list(n.compress_fragments([Fragment("a   ", italic=True), Fragment(" . ")]))

    # Strip leading/trailing spaces
    assert [Fragment("con")] == list(n.compress_fragments([Fragment(""), Fragment("con"), Fragment("   ")]))
    assert [Fragment("con")] == list(n.compress_fragments([Fragment("  con  ")]))
    assert [Fragment("con le")] == list(n.compress_fragments([Fragment("  con"), Fragment(" le  ")]))

    # include spaces in current formatting
    assert [Fragment("le mani", bold=True)] == \
           list(n.compress_fragments([Fragment("le", bold=True), Fragment("  "), Fragment("mani", bold=True)]))

    # Strip spaces before dots
    assert [Fragment("ciao", italic=True), Fragment(". ciao")] == \
           list(n.compress_fragments([Fragment("ciao", italic=True), Fragment(" . ciao")]))

    # Strip spaces inside parentheses
    assert [Fragment("("), Fragment("volgare", italic=True), Fragment(")")] == \
           list(n.compress_fragments([Fragment("( "), Fragment("volgare", italic=True), Fragment(" )")]))


def test_compress_html():
    # Remove spaces before dots
    assert "<i>intr</i>. far qualcosa" == n.compress_html(" <i>intr</i> . far qualcosa")
    # Idem commas
    assert "<i>bla</i>, far qualcosa" == n.compress_html(" <i>bla</i> , far qualcosa")
