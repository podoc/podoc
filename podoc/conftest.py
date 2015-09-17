# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from tempfile import TemporaryDirectory

from pytest import yield_fixture

from podoc import Podoc, add_default_handler
from podoc.testing import open_test_file, get_test_file_path


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
    yield Podoc()


@yield_fixture
def hello_ast():
    yield open_test_file('hello_ast.py')


@yield_fixture
def hello_pandoc():
    yield open_test_file('hello.json')


@yield_fixture
def hello_pandoc_path():
    yield get_test_file_path('hello.json')


@yield_fixture
def hello_markdown():
    yield open_test_file('hello.md')
