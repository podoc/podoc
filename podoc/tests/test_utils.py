# -*- coding: utf-8 -*-

"""Test utility functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging
import os.path as op

from pytest import mark

from ..utils import (Bunch, Path, open_text, save_text,
                     pandoc, has_pandoc, get_pandoc_formats)

logger = logging.getLogger(__name__)

require_pandoc = mark.skipif(not(has_pandoc()),
                             reason='pypandoc is not available')


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_bunch():
    obj = Bunch()
    obj['a'] = 1
    assert obj.a == 1
    obj.b = 2
    assert obj['b'] == 2
    assert obj.copy().a == 1


def test_path():
    print(Path(__file__))
    assert Path(__file__).exists()


#------------------------------------------------------------------------------
# Test file I/O
#------------------------------------------------------------------------------

def test_open_save_text(tempdir):
    path = op.join(tempdir, 'test.txt')
    save_text(path, 'hello *world*')
    assert open_text(path) == 'hello *world*'


def test_pandoc():
    out = pandoc('hello *world*', 'json', format='markdown')
    assert isinstance(json.loads(out), list)

    sl, tl = get_pandoc_formats()
    assert 'markdown' in sl
    assert 'markdown' in tl
