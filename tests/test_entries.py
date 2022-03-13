import pytest

from nap import entries as e
from nap.models import Fragment


@pytest.fixture
def abbaccamiento_fragments():
    # abbacamiento: m.
    #  accordo segreto.
    # abbaccarse: intr. pron. colludere,
    #  accordarsi.
    # abbacchià: tr. abbachiare.
    # abbacchiarse: rifl. abbattersi.
    return [(0.00044, Fragment('abbaccamiento: ', bold=True)),
            (83.22046, Fragment('m', italic=True)),
            (89.70046, Fragment('. ', bold=True)),
            (2.88006, Fragment('accordo segreto.')),
            (0.00096, Fragment('abbaccarse:', bold=True)),
            (51.30047, Fragment(' ', italic=True)),
            (59.82047, Fragment('intr. ', italic=True)),
            (83.58045, Fragment('pron. ', italic=True)),
            (111.30045, Fragment('colludere, ')),
            (2.88066, Fragment('accordarsi.')),
            (0.00098, Fragment('abbacchià: ', bold=True)),
            (49.38048, Fragment('tr.', italic=True)),
            (57.66047, Fragment(' ', bold=True)),
            (60.18047, Fragment('abbacchiare. ')),
            (0.00055, Fragment('abbacchiarse:', bold=True)),
            (59.64048, Fragment(' ')),
            (62.16047, Fragment('rifl', italic=True)),
            (73.20047, Fragment('. abbattersi.'))]


def test_parse_entries(abbaccamiento_fragments):
    entries = e.parse_entries(indented_fragments=abbaccamiento_fragments)
    first_texts = [entry.fragments[0].text.strip() for entry in entries]
    assert ['abbaccamiento:', 'abbaccarse:', 'abbacchià:', 'abbacchiarse:'] == first_texts
