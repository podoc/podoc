# -*- coding: utf-8 -*-
# flake8: noqa

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from ..core import Podoc, open_text, save_text


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_open_save_text(tempdir):
    path = op.join(tempdir, 'test.txt')
    contents = 'hello\nworld'

    save_text(path, contents)
    assert open_text(path) == contents


def test_podoc_trivial():
    contents = 'hello *world*!'

    podoc = Podoc()
    assert podoc.convert_contents(contents) == contents
