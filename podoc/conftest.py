# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from tempfile import TemporaryDirectory

from pytest import yield_fixture

from podoc import Podoc, add_default_handler
from podoc.utils import _open_test_file, _test_file_path


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
    yield _open_test_file('hello_ast.py')


@yield_fixture
def hello_pandoc():
    yield _open_test_file('hello.json')


@yield_fixture
def hello_pandoc_path():
    yield _test_file_path('hello.json')


@yield_fixture
def hello_markdown():
    yield _open_test_file('hello.md')
