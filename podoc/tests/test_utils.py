# -*- coding: utf-8 -*-

"""Test utility functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging
import os.path as op

from pytest import mark, raises

from ..utils import (Bunch, Path, load_text, dump_text, _get_file,
                     assert_equal,
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


def test_assert_equal():
    assert_equal([0], [0])

    assert_equal({'a': 1, 'b': [2, 3], '_c': 0},
                 {'a': 1, 'b': [2, 3], '_c': 1})

    with raises(AssertionError):
        assert_equal({'a': 1, 'b': [2, 3], '_c': 0},
                     {'a': 1, 'b': [2, 4], '_c': 0})


#------------------------------------------------------------------------------
# Test file I/O
#------------------------------------------------------------------------------

def test_open_dump_text(tempdir):
    path = op.join(tempdir, 'test.txt')
    dump_text('hello *world*', path)
    assert load_text(path) == 'hello *world*'
    assert _get_file(path, 'r').read() == 'hello *world*'
    with open(path, 'r') as f:
        assert _get_file(f, 'r').read() == 'hello *world*'


def test_pandoc():
    out = pandoc('hello *world*', 'json', format='markdown')
    assert isinstance(json.loads(out), list)

    sl, tl = get_pandoc_formats()
    assert 'markdown' in sl
    assert 'markdown' in tl
