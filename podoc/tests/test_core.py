# -*- coding: utf-8 -*-

"""Test core functionality."""


#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

import logging
import os
import os.path as op

from pytest import raises

from ..core import Podoc, _find_path, _get_annotation, _connected_component
from ..utils import get_test_file_path, load_text, dump_text

logger = logging.getLogger(__name__)


#-------------------------------------------------------------------------------------------------
# Tests utils
#-------------------------------------------------------------------------------------------------

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


#-------------------------------------------------------------------------------------------------
# Tests podoc
#-------------------------------------------------------------------------------------------------

def test_podoc_1():
    podoc = Podoc(with_pandoc=False)
    assert 'ast' in podoc.languages

    assert '.json' in podoc.file_extensions
    assert '.md' in podoc.file_extensions

    assert 'markdown' in podoc.get_target_languages('ast')


def test_podoc_fail():
    p = Podoc(with_pandoc=False)
    with raises(ValueError):
        p.convert_text('hello', lang_chain=['a', 'b'])
    with raises(ValueError):
        p.convert_file('/does/not/exist', lang_chain=['a', 'b'])


def test_podoc_convert_1(tempdir):
    p = Podoc(plugins=[], with_pandoc=False)

    p.register_lang('lower', file_ext='.low')
    p.register_lang('upper', file_ext='.up')

    @p.register_func(source='lower', target='upper')
    def toupper(text, context=None):
        return text.upper()

    @p.register_func(source='upper', target='lower')
    def tolower(text, context=None):
        return text.lower()

    # Conversion with explicit path.
    assert p.conversion_pairs == [('lower', 'upper'), ('upper', 'lower')]
    assert p.convert_text('Hello', lang_chain=['lower', 'upper', 'lower']) == 'hello'

    # Conversion with shortest path between source and target.
    assert p.convert_text('hello', source='lower', target='upper') == 'HELLO'

    with raises(ValueError):
        p.convert_text('hello', source='lower', target='unknown')

    # Convert a file.
    path = op.join(tempdir, 'test.up')
    path2 = op.join(tempdir, 'test.low')
    with open(path, 'w') as f:
        f.write('HELLO')
    assert p.convert_file(path, output=path2) == 'hello'
    with open(path2, 'r') as f:
        assert f.read() == 'hello'


def test_podoc_2(tempdir):
    p = Podoc(with_pandoc=False)

    assert p.get_file_ext('markdown') == '.md'
    assert p.get_file_ext('notebook') == '.ipynb'
    assert p.get_lang_for_file_ext('.md') == 'markdown'
    assert p.get_lang_for_file_ext('.ipynb') == 'notebook'

    md_path = op.join(tempdir, 'test.md')
    ipynb_path = op.join(tempdir, 'test.ipynb')

    dump_text('hello world', md_path)

    _, context = p.convert_file(md_path, output=ipynb_path, return_context=True)

    assert context.source == 'markdown'
    assert context.target == 'notebook'
    assert context.lang_chain == ['markdown', 'ast', 'notebook']

    assert '"cell_type": "markdown"' in load_text(ipynb_path)

    md_path2 = op.join(tempdir, 'test2.md')
    md, context = p.convert_file(ipynb_path, output=md_path2, return_context=True)
    assert md == 'hello world'


def test_podoc_pandoc(tempdir):
    p = Podoc()
    with raises(ValueError):
        p.convert_text('hello world', source='markdown', target='docx')
    path = op.join(tempdir, 'test.docx')
    p.convert_text('hello world', source='markdown', target='docx', output=path)
    assert 'test.docx' in os.listdir(tempdir)


def test_podoc_file(tempdir):
    p = Podoc(plugins=[], with_pandoc=False)

    p.register_lang('a', file_ext='.a', load_func=lambda path: 'a',
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


#-------------------------------------------------------------------------------------------------
# Tests all languages
#-------------------------------------------------------------------------------------------------

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
    podoc.assert_equal(load_text(to_path).rstrip(), podoc.dumps(contents, lang).rstrip(), lang)


def test_all_convert(tempdir, podoc, source_target, test_file):
    """Check all conversion paths on all test files."""
    source, target = source_target
    source_filename = test_file + podoc.get_file_ext(source)
    target_filename = test_file + podoc.get_file_ext(target)

    # Get the source and target file names.
    source_path = get_test_file_path(source, source_filename)
    target_path = get_test_file_path(target, target_filename)

    # Convert with podoc.
    converted = podoc.convert_file(source_path, target=target)

    expected = podoc.load(target_path)
    # Apply the eventual pre-filter on the target.
    # This is notably used when testing notebook -> AST, where the
    # expected AST needs to be decorated with CodeCells before being
    # compared to the converted AST.
    expected = podoc.pre_filter(expected, target, source)

    # Remove the trailing new lines.
    if isinstance(converted, str):
        converted = converted.rstrip()
    if isinstance(expected, str):
        expected = expected.rstrip()
    podoc.assert_equal(converted, expected, target)

    # Test converting and saving the file to disk.
    output = op.join(tempdir, 'output', target_filename)
    _, context = podoc.convert_file(source_path, output=output, return_context=True)
    files = os.listdir(op.join(tempdir, 'output'))
    # Check that all files are there
    assert target_filename in files
    if context.get('resources', {}):
        # Check that resources are there.
        res_path = op.splitext(target_filename)[0] + '_files'
        assert res_path in files
        assert len(os.listdir(op.join(tempdir, 'output', res_path))) > 0
