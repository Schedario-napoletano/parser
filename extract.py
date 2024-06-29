import argparse
import json
import os

from nap.definitions import parse_definition_dicts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--debug", action="store_true")
    p.add_argument("--diff", "-D", action="store_true",
                   help="Print a diff of the existing definitions (if any) with the new ones")
    p.add_argument("--dry-run", "-n", action="store_true", help="Don't actually save the definitions")
    p.add_argument("output_path", nargs="?", default="definitions.json")
    opts = p.parse_args()

    definitions = list(parse_definition_dicts(debug=opts.debug))

    if opts.diff and os.path.isfile(opts.output_path):
        with open(opts.output_path) as f:
            old_definitions = json.load(f)
            print_diff(old_definitions, definitions)

    if opts.dry_run:
        return

    with open(opts.output_path, "w") as f:
        json.dump(definitions, f, sort_keys=True, ensure_ascii=False)


def print_diff(definitions1: list[dict], definitions2: list[dict], verbose=False):
    removed_definitions = 0
    added_definitions = 0
    updated_definitions = 0
    unchanged_definitions = 0

    definitions1 = sorted(definitions1, key=lambda d: d["word"])
    definitions2 = sorted(definitions2, key=lambda d: d["word"])

    i = 0
    j = 0

    while True:
        if i >= len(definitions1):
            added_definitions += len(definitions2) - j
            break

        if j >= len(definitions2):
            removed_definitions += len(definitions1) - i
            break

        def1 = definitions1[i]
        def2 = definitions2[j]

        if def1 == def2:
            unchanged_definitions += 1
            i += 1
            j += 1
            continue

        w1 = def1["word"]
        w2 = def2["word"]

        if w1 == w2:
            updated_definitions += 1
            i += 1
            j += 1
            continue

        if w1 < w2:
            if verbose:
                print("-" + w1)
            removed_definitions += 1
            i += 1
            continue

        if w1 > w2:
            if verbose:
                print("+" + w2)
            added_definitions += 1
            j += 1
            continue

    print(unchanged_definitions or "no", "unchanged definitions")
    print(removed_definitions or "no", "removed definitions")
    print(updated_definitions or "no", "updated definitions")
    print(added_definitions or "no", "added definitions")


if __name__ == '__main__':
    main()
