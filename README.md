# Schedario napoletano (parser)

This repository contains code to extract the definitions from the two PDF files of the
[<i>Schedario napoletano</i>][1] written by Giuseppe Giacco.

As of 2022/03/13 this extracts 22,443 definitions.

[1]: http://www.vesuvioweb.com/it/2012/01/giuseppe-giacco-schedario-napoletano/

## Run

Download both parts of the <i>Schedario</i> as `1.pdf` and `2.pdf`.
Then run:

    poetry run python extract.py --json definitions.json

The output JSON can then be used to feed [the website][w].

[w]: https://github.com/Schedario-napoletano/website/tree/main/_data
