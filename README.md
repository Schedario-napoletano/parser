# Schedario napoletano (extract)

This repository contains code to extract the content of the [<i>Schedario napoletano</i> by Giuseppe Giacco][1].

As of 2022/02/10 this extracts 22087 definitions.

[1]: http://www.vesuvioweb.com/it/2012/01/giuseppe-giacco-schedario-napoletano/

## Run

Download both parts of the Schedario as `1.pdf` and `2.pdf`.
Then run:

    poetry run python extract.py --json definitions.json
