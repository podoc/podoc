# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from .tempdir import TemporaryDirectory

from pytest import fixture, yield_fixture

from podoc import add_default_handler, create_podoc


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
    return create_podoc()


@fixture(params=['hello'])
def test_file(request):
    name = request.param
    return name


def pytest_generate_tests(metafunc):
    """Generate the fixtures to test all format test files."""
    if 'lang' in metafunc.fixturenames:
        podoc = create_podoc(with_pandoc=False)
        metafunc.parametrize('lang', podoc.languages, ids=podoc.languages)
    if 'source_target' in metafunc.fixturenames:
        podoc = create_podoc(with_pandoc=False)
        metafunc.parametrize('source_target', podoc.conversion_pairs,
                             ids=(lambda pair: '-to-'.join(pair)))
