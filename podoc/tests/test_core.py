# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os.path as op

from pytest import raises

from ..core import Podoc, _find_path, _get_annotation, _connected_component
from ..utils import get_test_file_path, load_text, _test_file_resources

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Tests utils
#------------------------------------------------------------------------------

def test_get_annotation():
    assert _get_annotation(lambda: None, 'a') is None


def test_find_path():
    assert _find_path([(1, 2), (2, 3)], 1, 2) == [1, 2]
    assert _find_path([(1, 2), (2, 3)], 1, 3) == [1, 2, 3]
    assert _find_path([(1, 2), (2, 3)], 2, 3) == [2, 3]
    assert _find_path([(1, 2), (2, 3)], 3, 2) is None
    assert _find_path([(1, 2), (2, 3)], 1, 4) is None
    assert _find_path([(1, 2), (2, 3), (3, 4), (4, 5)], 1, 5) == \
        [1, 2, 3, 4, 5]
    assert _find_path([(1, 2), (2, 3), (1, 4), (4, 5)], 1, 5) == [1, 4, 5]


def test_connected_component():
    assert _connected_component([(1, 2), (2, 3)], 1) == [2, 3]
    assert _connected_component([(1, 2), (2, 3)], 2) == [3]
    assert _connected_component([(1, 2), (2, 3)], 3) == []
    assert _connected_component([(1, 2), (2, 3)], 4) == []
    assert _connected_component([(1, 2), (2, 3), (3, 4), (4, 5)], 1) == \
        [2, 3, 4, 5]
    assert _connected_component([(1, 2), (2, 3), (1, 4), (4, 5)], 1) == \
        [2, 3, 4, 5]


#------------------------------------------------------------------------------
# Tests podoc
#------------------------------------------------------------------------------

def test_podoc_1():
    podoc = Podoc(with_pandoc=False)
    assert 'ast' in podoc.languages

    assert '.json' in podoc.file_extensions
    assert '.md' in podoc.file_extensions

    assert 'markdown' in podoc.get_target_languages('ast')


def test_podoc_fail():
    p = Podoc(with_pandoc=False)
    with raises(ValueError):
        p.convert('hello', lang_list=['a', 'b'])


def test_podoc_convert_1(tempdir):
    p = Podoc(plugins=[], with_pandoc=False)

    p.register_lang('lower', file_ext='.low')
    p.register_lang('upper', file_ext='.up')

    @p.register_func(source='lower', target='upper')
    def toupper(text):
        return text.upper()

    @p.register_func(source='upper', target='lower')
    def tolower(text):
        return text.lower()

    # Conversion with explicit path.
    assert p.conversion_pairs == [('lower', 'upper'), ('upper', 'lower')]
    assert p.convert('Hello', lang_list=['lower', 'upper', 'lower']) == 'hello'

    # Conversion with shortest path between source and target.
    assert p.convert('hello', source='lower', target='upper') == 'HELLO'

    with raises(ValueError):
        p.convert('hello', source='lower', target='unknown')

    # Convert a file.
    path = op.join(tempdir, 'test.up')
    path2 = op.join(tempdir, 'test.low')
    with open(path, 'w') as f:
        f.write('HELLO')
    assert p.convert(path, output=path2) == 'hello'
    with open(path2, 'r') as f:
        assert f.read() == 'hello'


def test_podoc_file(tempdir):
    p = Podoc(plugins=[], with_pandoc=False)

    p.register_lang('a', file_ext='.a',
                    load_func=lambda path: 'a',
                    dump_func=lambda contents, path: None,
                    )
    assert p.languages == ['a']

    assert p.get_lang_for_file_ext('.a') == 'a'
    with raises(ValueError):
        p.get_lang_for_file_ext('.b')

    fn = op.join(tempdir, 'aa.a')
    open(fn, 'w').close()
    open(op.join(tempdir, 'bb.b'), 'w').close()

    with raises(AssertionError):
        p.get_files_in_dir('')
    files = p.get_files_in_dir(tempdir, lang='a')
    assert len(files) == 1
    assert fn in files[0]


def test_podoc_load_dump(tempdir):
    p = Podoc(with_pandoc=False)
    p.register_lang('txt', file_ext='.txt')
    filename = 'test.txt'
    path = op.join(tempdir, filename)
    p.dump('hello world', path)
    assert p.load(path) == 'hello world'

    assert p.dumps('hello world', 'txt') == 'hello world'
    assert p.loads('hello world', 'txt') == 'hello world'


#------------------------------------------------------------------------------
# Tests all languages
#------------------------------------------------------------------------------

def test_all_load_dump(tempdir, podoc, lang, test_file):
    """For all languages and test files, check round-tripping of load
    and dump."""

    # Test file.
    filename = test_file + podoc.get_file_ext(lang)
    path = get_test_file_path(lang, filename)

    # Load the example file.
    contents = podoc.load(path)
    to_path = op.join(tempdir, filename)
    # Save it again to a temporary file.
    podoc.dump(contents, to_path)

    # Assert equality.
    podoc.assert_equal(contents, podoc.loads(load_text(path), lang), lang)
    podoc.assert_equal(load_text(to_path), podoc.dumps(contents, lang), lang)


def test_all_convert(tempdir, podoc, source_target, test_file):
    """Check all conversion paths on all test files."""
    source, target = source_target
    source_filename = test_file + podoc.get_file_ext(source)
    target_filename = test_file + podoc.get_file_ext(target)

    # Get the source and target file names.
    source_path = get_test_file_path(source, source_filename)
    target_path = get_test_file_path(target, target_filename)

    # Load the test file resources.
    resources = _test_file_resources()

    # Convert with pandoc.
    converted = podoc.convert(source_path, target=target, resources=resources)
    # print('****** CONVERTED ******')
    # converted.show()

    expected = podoc.load(target_path)
    # Apply the eventual pre-filter on the target.
    # This is notably used when testing notebook -> AST, where the
    # expected AST needs to be decorated with CodeCells before being
    # compared to the converted AST.
    expected = podoc.pre_filter(expected, target, source)
    # print('****** EXPECTED ******')
    # expected.show()

    podoc.assert_equal(converted, expected, target)
