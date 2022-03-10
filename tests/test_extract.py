import clj

import extract


def _test_file1_page1_column_1():  # FIXME
    n = 28
    defs = clj.take(n, extract.parse_definitions())

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
