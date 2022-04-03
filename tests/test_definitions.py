import clj

from nap import definitions
from nap.models import Fragment, Entry, AliasDefinition


def test_file1_page1_column_1():
    n = 28
    defs = clj.take(n, definitions.parse_definitions())

    words = [d.word for d in defs]
    assert len(words) == n

    assert words == [
        "’a", "a", "a’!", "ab hoc e ab hac", "abaterno",
        "abbaaglià", "abbabbïà", "abbaccamiento", "abbaccarse", "abbacchià",
        "abbacchiarse", "abbacchiato", "abbacchio", "abbachino", "abbachisto",
        "àbbaco",
        "abbadà", "abbafagnà", "abbafarse", "abbafògna", "abbafuogno",
        "abbagaglià", "abbaglià", "abbagliamento", "abbagliamiénto", "abbagliato",
        "abbaglio", "abbagnà",
    ]


def test_ll():
    entry = Entry(
        [Fragment("ll’, ", bold=True),
         Fragment("v.", italic=True),
         Fragment(" l’.  ", bold=True)], initial_letter="L")

    definition = definitions.entry2definition(entry)
    assert isinstance(definition, AliasDefinition)
    assert definition.word == "ll’"
    assert definition.alias_of == "l’"


def test_alias_with_hyphen_and_space():
    entry = Entry(
        [Fragment('abbasta che-ca ', bold=True),
         Fragment('v.', italic=True),
         Fragment(' basta che-ca.', bold=True)], initial_letter="A")

    definition = definitions.entry2definition(entry)
    assert isinstance(definition, AliasDefinition)
    assert definition.word == "abbasta che-ca"
    assert definition.alias_of == "basta che-ca"
