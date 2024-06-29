#! /bin/bash -ex
poetry run mypy nap tests *.py
poetry run pytest
