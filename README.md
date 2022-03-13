# Schedario napoletano (parser)

This repository contains code to extract the definitions from the two PDF files of the
[<i>Schedario napoletano</i>][1] written by Giuseppe Giacco.

As of 2022/03/13 this extracts 22443 definitions.

This is still a work in progress.

[1]: http://www.vesuvioweb.com/it/2012/01/giuseppe-giacco-schedario-napoletano/

## Run

Download both parts of the Schedario as `1.pdf` and `2.pdf`.
Then run:

    poetry run python extract.py --json definitions.json

The output JSON can then be used to generate [the website][w].

[w]: https://github.com/Schedario-napoletano/website/tree/main/_data
