import schedario


def test_make_definition_text():
    defs = [
        {"fontname": "Times-Roman", "text": "a"},
        {"fontname": "Times-Roman", "text": "b"},
        {"fontname": "Times-Italic", "text": "c"},
        {"fontname": "Times-Roman", "text": "."},
    ]
    assert schedario.make_definition_text(defs) == "a b <i>c.</i>"
