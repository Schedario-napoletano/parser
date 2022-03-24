import argparse
import json

from nap.definitions import parse_definition_dicts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--debug", action="store_true")
    p.add_argument("output_path", nargs="?", default="definitions.json")
    opts = p.parse_args()

    with open(opts.output_path, "w") as f:
        json.dump(list(parse_definition_dicts(debug=opts.debug)), f, sort_keys=True, ensure_ascii=False)


if __name__ == '__main__':
    main()
