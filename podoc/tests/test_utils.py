# -*- coding: utf-8 -*-

"""Test utility functions."""


#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

import json
import logging
import os.path as op

from pytest import mark

from ..utils import (Bunch, Path, load_text, dump_text, _get_file, _merge_str, _shorten_string,
                     _get_resources_path, _save_resources, _load_resources,
                     get_test_file_path, _create_dir_if_not_exists,
                     pandoc, has_pandoc, get_pandoc_formats,
                     )

logger = logging.getLogger(__name__)

require_pandoc = mark.skipif(not(has_pandoc()),
                             reason='pypandoc is not available')


#-------------------------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------------------------

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


def test_merge_str():
    assert _merge_str(['a', 'b', None, 'c']) == ['ab', None, 'c']


def test_shorten_string():
    s = _shorten_string('*' * 60)
    assert s.startswith('*' * 10)
    assert s.endswith('*' * 10)
    assert '(...)' in s


def test_create_dir_if_not_exists(tempdir):
    assert not _create_dir_if_not_exists(tempdir)
    assert _create_dir_if_not_exists(op.join(tempdir, 'test'))
    assert op.exists(op.join(tempdir, 'test'))


#-------------------------------------------------------------------------------------------------
# Test resources
#-------------------------------------------------------------------------------------------------

def test_get_test_file_path():
    path = get_test_file_path('markdown', 'hello.md')
    assert op.exists(path)
    assert op.basename(path) == 'hello.md'


def test_get_resources_path():
    res_path = _get_resources_path('/path/to/test.ext')
    assert res_path == '/path/to/test_files'


def test_save_load_resources(tempdir):
    resources = {'test.ext': b'abc'}

    # Should fail without raising exception.
    _save_resources({})
    _save_resources(resources)
    assert not _load_resources(None)
    assert not _load_resources('/does/not/exist')

    _save_resources(resources, res_path=op.join(tempdir, 'res'))
    resources_loaded = _load_resources(op.join(tempdir, 'res'))
    assert resources_loaded == resources


#-------------------------------------------------------------------------------------------------
# Test file I/O
#-------------------------------------------------------------------------------------------------

def test_open_dump_text(tempdir):
    path = op.join(tempdir, 'test.txt')
    dump_text('hello *world*', path)
    assert load_text(path) == 'hello *world*'
    assert _get_file(path, 'r').read() == 'hello *world*'
    with open(path, 'r') as f:
        assert _get_file(f, 'r').read() == 'hello *world*'


def test_pandoc():
    out = pandoc('hello *world*', 'json', format='markdown')
    assert isinstance(json.loads(out), dict)

    sl, tl = get_pandoc_formats()
    assert 'markdown' in sl
    assert 'markdown' in tl
