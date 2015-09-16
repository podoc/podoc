# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import os.path as op

from pytest import yield_fixture
from tempfile import TemporaryDirectory

from podoc import Podoc, add_default_handler


#------------------------------------------------------------------------------
# Common fixtures
#------------------------------------------------------------------------------

add_default_handler('DEBUG')


def _load_test_file(filename):
    curdir = op.realpath(op.dirname(__file__))
    path = op.join(curdir, 'test_files/' + filename)
    ext = op.splitext(filename)[1]
    if ext == '.json':
        with open(path, 'r') as f:
            return json.load(f)
    elif ext == '.py':
        assert op.splitext(filename)[0].endswith('_ast')
        with open(path, 'r') as f:
            contents = f.read()
        ns = {}
        exec(contents, {}, ns)
        return ns['ast']


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
def hello_ast():
    yield _load_test_file('hello_ast.py')
