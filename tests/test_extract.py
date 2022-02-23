import clj

import extract


def test_first_entry():
    word, definition = clj.first(extract.parse())
    text: str = definition.as_html()
    assert text.startswith("1) <i>det. f. che si usa davanti ai nomi che cominciano con consonante</i>")
    assert text.endswith("4) <i>artt</i>. alla.")


def test_file1_page1_column_1():
    n = 28
    pairs = list(clj.take(n, extract.parse()))

    words = [word for word, _ in pairs]
    assert len(words) == n

    print(pairs[15][1])

    assert words == [
        "’a", "a", "a’!", "ab hoc e ab hac", "abaterno",
        "abbaaglià", "abbabbïà", "abbaccamiento", "abbaccarse", "abbacchià",
        "abbacchiarse", "abbacchiato", "abbacchio", "abbachino", "abbachisto",
        "àbbaco",
        "abbadà", "abbafagnà", "abbafarse", "abbafògna", "abbafuogno",
        "abbagaglià", "abbaglià", "abbagliamento", "abbagliamiénto", "abbagliato",
        "abbaglio", "abbagnà",
    ]
