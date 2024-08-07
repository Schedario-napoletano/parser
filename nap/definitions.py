import re
from typing import Optional, Tuple, Dict, Union, List, Iterable

from nap.entries import parse_entries
from nap.models import Qualifier, AliasDefinition, DerivativeDefinition, RawDefinition, Entry, Fragment, BaseDefinition
from nap.normalization import compress_html

ABBREVIATIONS: Dict[str, Union[str, List[str]]] = {
    "abbr": "abbreviazione",
    "accr": "accrescitivo",
    "af": "aferesi",
    "agg": ["aggettivo", "aggettivale", "aggettivato"],
    "alt": "alterazione",
    "ant": "antico",
    "ap": "apocope",
    "artt": "preposizione articolata",
    "aus": "verbo ausiliare",
    "avv": ["avverbio", "locuzione avverbiale"],
    "c": "complemento",
    "card": "aggettivo numerale cardinale",
    "cond": "condizionale",
    "cong": "congiunzione",
    "congiunt": "congiuntivo",
    "contr": "contrazione",
    "corr": "correttamente",
    "det": "articolo determinativo",
    "dim": "diminuitivo",
    "distr": "aggettivo numerale distributivo",
    "ecc": "eccetera",
    "eccl": "ecclesiastico",
    "el": "elisione",
    "ep": "epentesi",
    "es": "esempio",
    "escl": ["esclamazione", "esclamativo"],
    "f": "sostantivo femminile",
    "fig": "figuratamente",
    "fr": "francese",
    "fraz": "aggettivo numerale frazionario",
    "freq": ["frequente", "frequentativo"],
    "fut": "futuro",
    "ger": "gerundio",
    "giapp": "giapponese",
    "gr": "greco",
    "impf": "imperfetto",
    "impt": "imperativo",
    "ind": "indicativo",
    "indef": "aggettivo e/o pronome indefinito",
    "indet": "articolo indeterminativo",
    "inf": "infantile",
    "ingl": "inglese",
    "inter": "interiezione",
    "interr": "aggettivo e/o pronome interrogativo",
    "intr": "verbo intransitivo",
    "ir": ["ironico", "ironicamente"],
    "it": ["italianizzazione", "italiano", "italianizzato"],
    "l": ["lettura", "leggere"],
    "lat": "latino",
    "m": "sostantivo maschile",
    "nap": "napoletano-e",
    "neg": "negazione",
    "neol": "neologismo",
    "onom": ["onomatopea", "onomatopeico"],
    "ord": "aggettivo numerale ordinale",
    "p": "passato",
    "part": "participio",
    "pl": "plurale",
    "poss": "aggettivo e/o pronome possessivo",
    "pr": "proverbio",  # ?
    "prep": "preposizione",
    "pres": "presente",
    "pron": ["pronome", "pronominale"],
    "prop": "nome proprio",
    "prov": "provenzale",
    "raff": "rafforzativo",
    "rem": "passato remoto",
    "rifl": "verbo riflessivo",
    "sec": "secolo",
    "sinc": "sincope",
    "s": "singolare",
    "sinon": "sinonimo",
    "sp": "spagnolo",
    "spr": "spregiativo",
    "sup": "superlativo",
    "ted": "tedesco",
    "tr": "verbo transitivo",
    "tronc": "troncamento",
    "v": ["vedere", "vedi"],
    "vezz": "vezzeggiativo",
    "voc": "vocativo",

    # additional, undocumented or composite ones
    "escl. d’impazienza": "esclamazione d’impazienza",
    "n.pr": "nome proprio",
    "n. pr": "nome proprio",
    "intr. pron": "verbo intransitivo pronominale",
    "intr. pr": "verbo intransitivo pronominale",
    "rifl. intr": "verbo intransitivo riflessivo",
    "intr. rifl": "verbo intransitivo riflessivo",
    "pr.f": "plurale femminile",
    "int": "interiezione",
    "m.pl": "sostantivo maschile plurale",
    "m. inv": "sostantivo maschile invariabile",
    "pl.m": "sostantivo maschile plurale",
    "m. pl": "sostantivo maschile plurale",
    "f.pl": "sostantivo femminile plurale",
    "f. pl": "sostantivo femminile plurale",
    "pl. f": "sostantivo femminile plurale",
    "pl.f": "sostantivo femminile plurale",
    "agg.f": "aggettivo femminile",
    "agg. f": "aggettivo femminile",
    "det. pl": "articolo determinativo plurale",
    "f. s.e pl": "sostantivo femminile singolare e plurale",
    "ant. det.": "articolo determinativo",

    # probably an alias of "impt" (imperativo)
    "imprt": "imperativo",

    "aferesi": "aferesi",
    "deformazione": "deformazione",
    "assimilazione": "assimilazione",
    "antica forma": "antica forma",

    "da": "da",

    "onom.  per": "onomatopea",

    "f. eagg": "sostantivo femminile e aggettivo",
    "m.eagg": "sostantivo maschile e aggettivo",
    "f. e agg": "sostantivo femminile e aggettivo",
    "m. e f": "sostantivo maschile e femminile",
    "pl m. e f": "sostantivo plurale maschile e femminile",
    "m. e agg": "sostantivo maschile e aggettivo",
    "m.e agg": "sostantivo maschile e aggettivo",
    "agg. e m": "sostantivo maschile e aggettivo",
    "m. e f. e agg": "sostantivo maschile e femminile e aggettivo",
    "m.-f. e agg": "sostantivo maschile e femminile e aggettivo",
    "m.- f. e agg": "sostantivo maschile e femminile e aggettivo",
    "m. e agg. e part": "sostantivo maschile e aggettivo e participio",
    "prep. e avv": "preposizione e avverbio",
    "agg. e part": "aggettivo e participio",
    "agg.  e part": "aggettivo e participio",
    "tr. e intr": "verbo transitivo e intransitivo",
    "tronc. e voc": "troncamento e vocativo",
}

RE_SEE_ALSO = re.compile(r"^v\s*\. +(\w[- \w]*’?)\s*\.?$", flags=re.UNICODE)

# "abbr", "abbr.di", "abbr di", "abbr. di", "abbr . di"
RE_ABBR = re.compile(r"^(%s)\s*((?:\.|\.?\s+)di)?$" % "|".join(re.escape(abbr) for abbr in ABBREVIATIONS),
                     flags=re.UNICODE)

RE_ALT_END_SLASH = re.compile(r"(.+)([eio])/([aeio])$")


def parse_qualifier(s: str, word_text: str) -> Tuple[Optional[str], bool]:
    """
    Parse a string as qualifier. Return (qualifier, derivative?) where `derivative?` is True if the qualifier indicates
    a derivative of some other word.

    E.g.: "it": non-derivative
          "it di": derivative: it's an "it" of what's next in the definition text.
    """
    if m := RE_ABBR.match(s):
        abbr = m.group(1)
        ends_with_di = bool(m.group(2))
        qualifier = ABBREVIATIONS[abbr]

        if qualifier == "da":
            return "da", True

        if qualifier == "vedere":
            return None, True

        if isinstance(qualifier, list):
            if abbr == "avv":
                if " " in word_text:
                    qualifier = "locuzione avverbiale"
                else:
                    qualifier = "avverbio"
            else:
                qualifier = qualifier[0]

        return qualifier, ends_with_di
    return None, False


def entry2definition(entry) -> BaseDefinition:
    word = entry.fragments[0]
    if not word.bold:
        print(entry.as_md())
        print(entry.fragments)
    assert word.bold

    # "hadda="
    # "lu,", # "ll’,"
    # "+++augurio"
    word_text = word.text.strip(" :").lstrip("+").rstrip("=,")
    fragments = entry.fragments[1:]

    # sometimes the colon is in its own fragment
    if len(fragments) > 2 and fragments[0].text.strip() == ":":
        # skip it
        fragments = fragments[1:]

    # sometimes the whole definition or its beginning is in a single bold fragment
    # "<b>unu: uno</b> <i>bla bla</i> bla."
    if m := re.match(r"^(\w+): (.+)$", word_text, flags=re.UNICODE):
        # "<b>chessà: chi sa.</b>"
        word_text = m.group(1)
        fragments = [Fragment(m.group(2))] + fragments
    elif not fragments:
        if m := re.match(r"^(\w+) v\. (\w+)\.?$", word_text, flags=re.UNICODE):
            # <b>felariéllo v. filariéllo.</b>
            return AliasDefinition(m.group(1), entry.initial_letter, m.group(2))
        else:
            raise RuntimeError("Empty definition: %s" % entry.as_md())

    # sometimes there’s a parenthesis between the word and the definition, and the opening parenthesis is bold
    # e.g. "<b>bla (</b> <i>something)</i>: blabla.". Variant: "<b>pepella: 1)</b> ..."
    for definition_prefix in ("(", ": 1)"):
        if word_text.endswith(definition_prefix):
            # move the prefix in the next fragment
            word_text = word_text[:-len(definition_prefix)].rstrip()
            fragments[0].prepend_text(definition_prefix)

    plain_text = " ".join(fragment.text for fragment in fragments).strip()

    if m := RE_SEE_ALSO.match(plain_text):
        return AliasDefinition(word_text, entry.initial_letter, m.group(1))

    qualifier: Optional[Qualifier] = None
    derivative = False

    # Arbitrary threshold: above this value this is probably not a qualifier
    # Note some words have two qualifiers: "<i>q1</i> e <i>q2</i>. (…)"
    if fragments[0].italic and len(fragments[0].text) < 20:
        prefix = fragments[0].text.strip(" .")
        qualifier, derivative = parse_qualifier(prefix, word_text=word_text)
        if qualifier:
            fragments = fragments[1:]
            # "<i>agg</i>. blabla" -> qualifier=agg, definition = "blabla" (and not ". blabla")
            if fragments[0].text.startswith("."):
                fragments[0].text = fragments[0].text.lstrip(". ")

    # basic definition
    if derivative \
            and fragments[0].bold \
            and len(fragments) == 1 \
            and re.match(r"^([ ,’!a-zA-ZìàùèéÀÙÈÉ]+)\s*\.?$", plain_text):
        return DerivativeDefinition(word_text, entry.initial_letter, fragments[0].text.strip(" ."), qualifier=qualifier)

    return RawDefinition(word_text, entry.initial_letter, fragments, qualifier=qualifier)


def explode_definition(definition: BaseDefinition) -> list[BaseDefinition]:
    """
    Explode a definition. In most cases, this results in a list with only this definition, but in some cases the
    definition includes multiple words; in this case the first one holds the definition unchanged, while the other(s)
    are aliased to it.

    For example "nicchio/a" becomes "nicchio" + an alias "nicchia".
    """
    word = definition.word.replace("–", "-")
    qualifier = definition.qualifier

    if (
            # Avoid unnecessary comparisons
            not (set(word) & {"-", "/", ","})

            # These are not declinations
            or word in {"votta-votta", "ih, gioia", }
    ):
        return [definition]

    # Some declined words have declined definitions as well
    if isinstance(definition, RawDefinition) and "-" in definition.definition:
        return [definition]

    # Specific case
    if word == "carnale/o-a" and qualifier == "aggettivo":
        definition.word = "carnale"
        return [
            definition,
            definition.aliased_as("carnalo"),
            definition.aliased_as("carnala"),
        ]

    if isinstance(definition, AliasDefinition) and "-" not in word and ", " in word:
        words = word.split(", ")
        definition.word = words[0]
        return [definition] + [
            definition.aliased_as(word)
            for word in words[1:]
        ]

    if words := {
        "abbasta che-ca": ["abbasta che", "abbasta ca"],
        "avasta che-ca": ["avasta che", "avasta ca"],
        "commara-e, commarella": ["commara", "commare", "commarella"],
        "creianza, creiaturo-a": ["creianza", "creiaturo", "creiatura"],
        "falzariga, falzarica": ["falzariga", "falzarica"],
        "nchiova, nchiovatélla": ["nchiova", "nchiovatélla"],
        "sciò-sciòmmo": ["sciò", "sciòmmo"],
        "tiénnero-tènnera": ["tiénnero", "tènnera"],
        "Nannina-Nanninèlla": ["Nannina", "Nanninèlla"],
    }.get(word):
        definition.word = words[0]
        return [definition] + [
            definition.aliased_as(word)
            for word in words[1:]
        ]

    if word in {
        "liésto-lèsta",
        "liticariello-liticarella",
        "litratto-litrattiello",
        "lìzzeto-lézzeta",
        "muscillo-muscella",
        "Nannina-Nanninèlla",
        "nigro-negra",
        "nnutto-nnotta",
        "nzevuso-nzevosa",
        "sciò-sciòmmo",
        "strillazzàro-strillazzèra",
        "tiénnero-tènnera",
    }:
        word1, word2 = word.split("-")
        definition.word = word1
        return [
            definition,
            definition.aliased_as(word2),
        ]

    # nicchio/a, passaggiere/o
    if m := RE_ALT_END_SLASH.match(word):
        if definition.qualifier is None:
            root, end1, end2 = m.groups()

            definition.word = root + end1
            return [
                definition,
                definition.aliased_as(root + end2)
            ]

    if "/" in word:
        print(f"Skipping suspicious word {word} ({qualifier})")
        return []

    # Be careful about grammar here: the feminine form of -uolo is -ola, not -uola.
    if m := \
            (qualifier in {
                # Qualifiers without gender, meaning we can keep them for both forms
                None,
                "accrescitivo",
                "aggettivo", "aggettivo numerale cardinale", "aggettivo e participio",
                "aggettivo e/o pronome indefinito",
                "alterazione",
                "avverbio",
            } and (
                     # -o/-a and similar: uttavo-a, cantalesia-o
                     re.match(r"(.+)([aeo])-([aeo])$", word)
                     # # vecchiariello-ella, vicchiariéllo-èlla, scurdariello-èlla -> TODO verify if it's -ella or -iella
                     # or re.match(r"(.+i)([eé]llo)-([eè]lla)$", word)

                     # -uosto/-osta: vuosto-vòsta
                     or re.match(r"(.+)(uosto)-(òsta)$", word)
                     # -uso/-osa: vuzzuluso-osa, zuzzuso-ósa, merruoietuso-osa
                     # -oso/-osa: porposo-ósa
                     or re.match(r"(.+[ibcdfglmnprstvz])([ouù]so)-([oó]sa)$", word)
                     # -isco/-esca: veperìsco-ésca
                     or re.match(r"(.+)(ìsco)-(ésca)$", word)
                     # -iuolo/-iola: stuppaiuolo-iòla
                     or re.match(r"(.+)(iuolo)-(iòla)$", word)
                     # -uolo/-ola: vasciaiuolo-òla
                     or re.match(r"(.+)(uolo)-([oò]la)$", word)
                     # -ulo/-ola: pressarùlo-òla
                     or re.match(r"(.+)(ùlo)-(òla)$", word)
                     # -illo/-ella: tummulillo-ella, teccatìllo-ella, peccerillo-élla
                     or re.match(r"(.+[bcdfglmnprstvz])([iì]llo)-([eé]lla)$", word)
                     # -isso/-essa: scarfisso-éssa
                     or re.match(r"(.+)(isso)-(éssa)$", word)
                     # -itro/-etra: pollitro-etra
                     or re.match(r"(.+)(itro)-(etra)$", word)
                     # -utto/-otta: scurrùtto-òtta
                     or re.match(r"(.+)(ùtto)-(òtta)$", word)
                     # -olo/-ulella: zìtolo-ulélla
                     or re.match(r"(.+)(olo)-(ulélla)$", word)

                     # cc + -iullo/-olla: utricciullo-olla
                     or re.match(r"(.+c)(iullo)-(olla)$", word)
             )
            ) or \
            (qualifier in {
                "sostantivo maschile", "sostantivo femminile",
            } and (
                     # maschile: trainiero-e, spitaliere-o, vestiàmma-e, piribìsso-i, pulizzastivale-i
                     # femminile: tiritosta-o, visciòla-e
                     re.match(r"(.+)([aeo])-([aeio])$", word)
             )
            ):
        # print("SPLIT", word, definition.qualifier)

        root, end1, end2 = m.groups()
        definition.word = root + end1

        return [
            definition,
            definition.aliased_as(root + end2)
        ]

    if "-" in word:
        print("Possible split:", word, f"[{definition.qualifier}]" if definition.qualifier else "",
              f"=> {definition.definition}" if isinstance(definition, RawDefinition) else "")

    return [definition]


def _parse_definitions(entries: Optional[Iterable[Entry]] = None):
    """Parse definitions, but don't dedupe them. See parse_definitions() instead."""
    if entries is None:
        entries = parse_entries()

    for entry in entries:
        first_text = entry.fragments[0].text.strip()
        # false-positives
        if first_text in {"g:", "pepaiuola:", "svettare.", "le parole che iniziano o la"} \
                or first_text.startswith("nel passaggio dal latino,"):
            continue

        # See 1.pdf, p.114, on the middle left
        if first_text == ".:" and entry.fragments[1].text == "antico nome di Villaricca.":
            entry.fragments[0].text = "Panicuocolo:"
            entry.fragments[0].bold = True
            entry.fragments[1].italic = False

        definition = entry2definition(entry)

        # false-positives: "g", "nz-", "mb-"
        if definition.word == "g" or definition.word.endswith("-"):
            continue

        # for debugging
        definition._fragments = entry.fragments

        # Some entries are merged together
        yield from explode_definition(definition)

        yield definition


def parse_definitions(entries: Optional[Iterable[Entry]] = None):
    seen: set[str] = set()

    for definition in _parse_definitions(entries):
        # Some definitions are duplicated
        if definition.word in seen:
            continue

        seen.add(definition.word)

        yield definition


def parse_definition_dicts(entries: Optional[Iterable[Entry]] = None, debug=False):
    for definition in parse_definitions(entries):
        definition_dict = definition.as_dict(debug=debug)

        if not re.match(r"[-A-ZÈa-zàéèìïòóù’' ]+[!?]?$", definition_dict["word"]):
            print("/!\\ possible parsing issue on word:", repr(definition_dict["word"]))

        if text := definition_dict.get("definition"):
            definition_dict["definition"] = compress_html(text)

        yield definition_dict
