# -*- coding: utf-8 -*-

"""py.test utilities."""

#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

import logging
from itertools import product
from tempfile import TemporaryDirectory

from pytest import fixture, yield_fixture

from podoc import add_default_handler, Podoc  # noqa


#-------------------------------------------------------------------------------------------------
# Common fixtures
#-------------------------------------------------------------------------------------------------

logging.getLogger().setLevel(logging.DEBUG)
add_default_handler('DEBUG')


@yield_fixture
def tempdir():
    with TemporaryDirectory() as tempdir:
        yield tempdir


@fixture
def podoc():
    return Podoc(with_pandoc=False)


# List of test files to test.
@fixture(params=['hello', 'simplenb'])
def test_file(request):
    name = request.param
    return name


def pytest_generate_tests(metafunc):
    """Generate the fixtures to test all format test files."""
    if 'lang' in metafunc.fixturenames:
        podoc = Podoc(with_pandoc=False)
        langs = podoc.languages
        metafunc.parametrize('lang', langs, ids=langs)
    if 'source_target' in metafunc.fixturenames:
        podoc = Podoc(with_pandoc=False)
        cp = podoc.conversion_pairs
        # Add source => target for all source => ast, ast => target in conversion pairs.
        sources = [lang for lang, _ in cp if _ == 'ast']
        target = [lang for _, lang in cp if _ == 'ast']
        cp.extend([(a, b) for (a, b) in product(sources, target) if a != b])
        print(cp)
        metafunc.parametrize('source_target', cp, ids=(lambda pair: '-to-'.join(pair)))
