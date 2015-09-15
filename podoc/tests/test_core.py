# -*- coding: utf-8 -*-
# flake8: noqa

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from pytest import yield_fixture

from ..core import Podoc, open_text, save_text


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@yield_fixture
def podoc():
    yield Podoc()


@yield_fixture
def contents():
    contents = 'hello *world*!'
    yield contents


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_open_save_text(tempdir, contents):
    path = op.join(tempdir, 'test.txt')

    save_text(path, contents)
    assert open_text(path) == contents


def test_podoc_trivial(podoc, contents):
    assert podoc.convert_contents(contents) == contents
