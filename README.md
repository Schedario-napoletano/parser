# Schedario napoletano (parser)

This repository contains code to extract the definitions from the two PDF files of the
[<i>Schedario napoletano</i>][1] written by Giuseppe Giacco.

This extracts 23k unique definitions, of which 5k are aliases.

[1]: http://www.vesuvioweb.com/it/2012/01/giuseppe-giacco-schedario-napoletano/

## Run

Download both parts of the <i>Schedario</i> as `1.pdf` and `2.pdf`. Then run:

    poetry run python extract.py [<path>].

The output JSON can then be used to feed [the website][w]. If `<path>` is not provided, it defaults
to `definitions.json`.

[w]: https://github.com/Schedario-napoletano/website/tree/main/_data

### Advanced usage

The script supports additional options:

    poetry run python extract.py [--dry-run] [--diff]

* `--dry-run`: don't actually write the definitions in a file
* `--diff`: print some diff between the existing definitions (if any) and the new ones. This is useful to see changes
  when editing the code logic.