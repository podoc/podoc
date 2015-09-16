# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from tempfile import TemporaryDirectory

from pytest import yield_fixture

from podoc import Podoc, add_default_handler
# from podoc.plugin import iter_plugin_fixtures
from podoc.utils import _load_test_file, _test_file_path


#------------------------------------------------------------------------------
# Common fixtures
#------------------------------------------------------------------------------

logging.getLogger().setLevel(logging.DEBUG)
add_default_handler('DEBUG')

# # Generate all example fixtures from all loaded plugins.
# for fixture in iter_plugin_fixtures():
#     print("add", fixture.__name__)
#     globals()[fixture.__name__] = yield_fixture(fixture)


@yield_fixture
def tempdir():
    with TemporaryDirectory() as tempdir:
        yield tempdir


@yield_fixture
def podoc():
    yield Podoc()


@yield_fixture
def hello_ast():
    yield _load_test_file('hello_ast.py')


@yield_fixture
def hello_pandoc():
    yield _load_test_file('hello.json')


@yield_fixture
def hello_pandoc_path():
    yield _test_file_path('hello.json')


@yield_fixture
def hello_markdown():
    yield _load_test_file('hello.md')


# from pprint import pprint
# pprint(sorted(globals().keys()))
