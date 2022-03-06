from dataclasses import dataclass
from typing import List, Optional, Iterable

Word = str
Qualifier = str


@dataclass
class Fragment:
    text: str
    bold: bool
    italic: bool

    def strip_formatting(self):
        self.bold = False
        self.italic = False

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
    template = ""

    def __init__(self, word: str, initial_letter: str, *, qualifier: Optional[Qualifier] = None):
        self.word = word
        self.qualifier = qualifier
        self.initial_letter = initial_letter

    def as_md(self):
        raise NotImplementedError()

    def as_dict(self):
        return {
            "template": self.template,
            "word": self.word,
            "qualifier": self.qualifier,
        }


class RawDefinition(BaseDefinition):
    template = "html"

    def __init__(self, word: str, initial_letter: str, fragments: List[Fragment],
                 *, qualifier: Optional[Qualifier] = None):
        super().__init__(word, initial_letter, qualifier=qualifier)
        self.fragments = fragments

    def as_md(self):
        q = f"_{self.qualifier}_ " if self.qualifier else ""
        return f"{self.word}: {q}{' '.join(fragment.as_md() for fragment in self.fragments)}"

    def as_dict(self):
        d = super().as_dict()
        d["html"] = ' '.join(fragment.as_html() for fragment in self.fragments)
        return d


class DerivativeDefinition(BaseDefinition):
    template = "derivative"

    def __init__(self, word: str, initial_letter: str, derive_from: str, **kwargs):
        super().__init__(word, initial_letter, **kwargs)
        self.derive_from = derive_from

    def as_md(self):
        if self.qualifier == "da":
            q = "da"
        else:
            q = self.qualifier + " di"

        return f"{self.word}: _{q}_ {self.derive_from}"

    def as_dict(self):
        d = super().as_dict()
        d["qualifier"] = "da" if self.qualifier == "da" else self.qualifier + " di"
        d["target"] = self.derive_from
        return d


class AliasDefinition(BaseDefinition):
    template = "alias"

    def __init__(self, word: str, initial_letter: str, alias_of: str, **kwargs):
        super().__init__(word, initial_letter, **kwargs)
        self.alias_of = alias_of

    def as_md(self):
        return f"{self.word} → {self.alias_of}"

    def as_dict(self):
        d = super().as_dict()
        d["target"] = self.alias_of
        return d