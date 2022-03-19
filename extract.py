import argparse
import json
from typing import List

from nap import parse_definitions


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json")
    opts = p.parse_args()

    json_path = opts.json
    json_definitions: List[dict] = []

    try:
        for definition in parse_definitions():
            if json_path:
                json_definitions.append(definition.as_dict())
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    finally:
        if json_path:
            with open(json_path, "w") as f:
                json.dump(json_definitions, f, sort_keys=True, ensure_ascii=False)


if __name__ == '__main__':
    main()
