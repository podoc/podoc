# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from .tempdir import TemporaryDirectory

from pytest import fixture, yield_fixture

from podoc import add_default_handler, Podoc  # noqa


#------------------------------------------------------------------------------
# Common fixtures
#------------------------------------------------------------------------------

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
@fixture(params=['hello', 'notebook'])
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
        metafunc.parametrize('source_target', podoc.conversion_pairs,
                             ids=(lambda pair: '-to-'.join(pair)))
