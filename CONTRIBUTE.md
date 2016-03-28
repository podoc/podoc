# Contributing

* We welcome all contributions,code or documentation !
* Please create a GitHub issue for discussion *before* you start contributing code or documentation.

## Code structure

* Every file `file.py` must be tested in `tests/test_file.py`.
* Every format is implemented in a `podoc/formatname/` subdirectory.
* Every format provides test files in `podoc/formatname/test_files/examplename.ext`. Static files (images) are all saved in `markdown/test_files/`.

## Code quality

* We use `flake8` to test the code quality.
* All code files should follow the same structure with the comments and docstrings.
* Ensure that `make test` works and that 100% of the lines are covered by the test suite.
* Test with the latest release of pandoc available on GitHub.

## Pull requests

* For pull requests, create a feature branch on your fork and propose a PR against master.
