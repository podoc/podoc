# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from tempfile import TemporaryDirectory

from pytest import yield_fixture

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


@yield_fixture
def podoc():
    yield create_podoc()


@yield_fixture(params=['hello'])
def test_file(request):
    name = request.param
    yield name


def pytest_generate_tests(metafunc):
    """Generate the fixtures to test all format test files."""
    if 'lang' in metafunc.fixturenames:
        podoc = create_podoc()
        metafunc.parametrize('lang', podoc.languages)
