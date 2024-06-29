from dataclasses import dataclass
from typing import List, Optional, Iterable

Word = str
Qualifier = str


@dataclass
class Fragment:
    text: str
    bold: bool = False
    italic: bool = False

    def remove_formatting(self):
        self.bold = False
        self.italic = False

    def prepend_text(self, prefix: str):
        self.text = prefix + self.text

    def append_text(self, suffix: str):
        self.text += suffix

    def copy(self):
        # noinspection PyArgumentList
        return self.__class__(text=self.text, bold=self.bold, italic=self.italic)

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


class Entry:
    def __init__(self, fragments: Iterable[Fragment], initial_letter: str):
        self.fragments = list(fragments)
        self.initial_letter = initial_letter

    def as_md(self, sep=" "):
        return sep.join(fragment.as_md() for fragment in self.fragments)


class BaseDefinition:
    definition_type = ""

    def __init__(self, word: str, initial_letter: str, *, qualifier: Optional[Qualifier] = None):
        self.word = word
        self.qualifier = qualifier
        self.initial_letter = initial_letter
        # for debugging
        self._fragments: Optional[List[Fragment]] = None

    def as_md(self):
        raise NotImplementedError()

    def as_dict(self, debug=False):
        d = {
            "definition_type": self.definition_type,
            "word": self.word,
            "qualifier": self.qualifier,
            "initial_letter": self.initial_letter,
        }
        if debug and self._fragments:
            d["_fragments"] = [f.as_md() for f in self._fragments]
        return d

    def aliased_as(self, alias: str, qualifier: Optional[Qualifier] = None):
        target_word = self.word
        if isinstance(self, AliasDefinition):
            target_word = self.alias_of

        alias_ = AliasDefinition(
            alias_of=target_word,
            word=alias,
            qualifier=qualifier or self.qualifier,
            initial_letter=alias[0].upper()
        )
        alias_._fragments = self._fragments
        return alias_

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.word} ({self.qualifier})>"


class RawDefinition(BaseDefinition):
    definition_type = "default"

    def __init__(self, word: str, initial_letter: str, fragments: List[Fragment],
                 *, qualifier: Optional[Qualifier] = None):
        super().__init__(word, initial_letter, qualifier=qualifier)
        self.fragments = fragments

    @property
    def definition(self):
        return ' '.join(fragment.as_html() for fragment in self.fragments)

    def as_md(self):
        q = f"_{self.qualifier}_ " if self.qualifier else ""
        return f"{self.word}: {q}{' '.join(fragment.as_md() for fragment in self.fragments)}"

    def as_dict(self, debug=False):
        d = super().as_dict(debug=debug)
        d["definition"] = self.definition
        return d


class DerivativeDefinition(BaseDefinition):
    definition_type = "derivative"

    def __init__(self, word: str, initial_letter: str, derive_from: str, **kwargs):
        super().__init__(word, initial_letter, **kwargs)
        self.derive_from = derive_from

    def as_md(self):
        if self.qualifier == "da":
            q = "da"
        else:
            q = self.qualifier + " di"

        return f"{self.word}: _{q}_ {self.derive_from}"

    def as_dict(self, debug=False):
        d = super().as_dict(debug=debug)
        d["qualifier"] = "da" if self.qualifier == "da" else self.qualifier + " di"
        d["target"] = self.derive_from
        return d


class AliasDefinition(BaseDefinition):
    definition_type = "alias"

    def __init__(self, word: str, initial_letter: str, alias_of: str, **kwargs):
        super().__init__(word, initial_letter, **kwargs)
        self.alias_of = alias_of

    def as_md(self):
        return f"{self.word} → {self.alias_of}"

    def as_dict(self, debug=False):
        d = super().as_dict(debug=debug)
        d["target"] = self.alias_of
        return d
