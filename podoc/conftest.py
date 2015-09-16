# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import yield_fixture
from tempfile import TemporaryDirectory

from podoc import Podoc, add_default_handler
from podoc.utils import _test_file_path, _load_test_file


#------------------------------------------------------------------------------
# Common fixtures
#------------------------------------------------------------------------------

add_default_handler('DEBUG')


@yield_fixture
def tempdir():
    with TemporaryDirectory() as tempdir:
        yield tempdir


@yield_fixture
def podoc():
    yield Podoc()


@yield_fixture
def hello_pandoc():
    yield _load_test_file('hello.json')


@yield_fixture
def hello_pandoc_path():
    yield _test_file_path('hello.json')


@yield_fixture
def hello_ast():
    yield _load_test_file('hello_ast.py')


@yield_fixture
def hello_markdown():
    yield _load_test_file('hello.md')
