# -*- coding: utf-8 -*-

"""Test AST functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json

from pytest import yield_fixture, raises

from .._ast import (AST, Block, Inline, _remove_meta, ae,)
from podoc.utils import has_pandoc, pandoc


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@yield_fixture
def ast_dict():
    ast_dict = [{'unMeta': {}}, [
                {'c': [{'c': 'hello', 't': 'Str'},
                       {'c': [], 't': 'Space'},
                       {'c': [{'c': 'world', 't': 'Str'}], 't': 'Emph'}],
                 't': 'Para',
                 'm': {'zero': 0},
                 },
                {'c': [{'c': 'hi!', 't': 'Str'}],
                 't': 'Para',
                 'm': {},
                 }]
                ]
    yield ast_dict


@yield_fixture
def ast():
    ast = AST()

    # First block
    block = Block(name='Para',
                  children=[Inline(name='Str', children='hello'),
                            Inline(name='Space'),
                            ])
    block.add_metadata(zero=0)
    inline = Inline(name='Emph')
    inline.add_child(Inline(name='Str', children='world'))
    block.add_child(inline)
    ast.add_block(block)

    assert block.t == 'Para'
    assert block.c == block.children

    assert inline.t == inline.name
    assert inline.c == inline.children

    # Second block
    block = Block(name='Para',
                  children=[Inline(name='Str', children='hi!')])
    ast.add_block(block)
    yield ast


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_ae():
    ae(1, 1)
    ae(1., 1)

    ae({'a': 1, 'm': {}}, {'a': 1})
    with raises(AssertionError):
        ae({'a': 1, 'b': {}}, {'a': 1})

    ae('abc\n', 'abc\n')
    with raises(AssertionError):
        ae('abc\n', 'abc')


def test_remove_meta(ast_dict):
    ast_dict = _remove_meta(ast_dict)
    expected = [{'unMeta': {}}, [
                {'c': [{'c': 'hello', 't': 'Str'},
                       {'c': [], 't': 'Space'},
                       {'c': [{'c': 'world', 't': 'Str'}], 't': 'Emph'}],
                 't': 'Para',
                 },
                {'c': [{'c': 'hi!', 't': 'Str'}],
                 't': 'Para',
                 }]
                ]
    assert ast_dict == expected


def test_to_dict(ast_dict, ast):
    ast_dict_converted = ast.to_dict()
    assert ast_dict_converted == ast_dict


def test_from_dict(ast_dict, ast):
    ast_converted = AST.from_dict(ast_dict)
    assert ast_converted == ast


#------------------------------------------------------------------------------
# Tests with pandoc
#------------------------------------------------------------------------------

# We use strict Markdown, but we allow fancy lists.
MARKDOWN_FORMAT = ('markdown_strict+'
                   'fancy_lists+'
                   'startnum+'
                   'backtick_code_blocks'
                   )


def _test_pandoc_ast(s):
    """Check the compatibility of the podoc AST with pandoc.

    * Perform Markdown -> pandoc AST dict -> podoc AST -> podoc AST dict
    * Check that pandoc AST dict = podoc AST dict

    """
    if not has_pandoc():  # pragma: no cover
        raise ImportError("pypandoc is not available")
    # NOTE: we disable pandoc Markdown extensions.
    ast_dict = json.loads(pandoc(s, 'json',
                                 format=MARKDOWN_FORMAT))
    ast = AST.from_dict(ast_dict)
    ae(ast.to_dict(), ast_dict)


def test_pandoc_ast_inline_1():
    _test_pandoc_ast('hello')
    _test_pandoc_ast('hello world')
    _test_pandoc_ast('hello *world*')
    _test_pandoc_ast('hello **world**')
    _test_pandoc_ast('hello `world`')
    _test_pandoc_ast('[hello](world)')
    _test_pandoc_ast('![hello](world)')


def test_pandoc_ast_inline_2():
    _test_pandoc_ast('*hello* `world` ** !*(?)* **')
    _test_pandoc_ast('[*hello* **world `!`**](world)')
    _test_pandoc_ast('![*hello* **world `!`**](world)')


def test_pandoc_ast_block_1():
    _test_pandoc_ast('# T1')
    _test_pandoc_ast('## T2')
    _test_pandoc_ast('# T1\n\n## T2')
    # _test_pandoc_ast('```python\nhello world\n```')
    _test_pandoc_ast('> hello world')
    _test_pandoc_ast('> hello\n> world')


def test_pandoc_ast_bullet_list():
    _test_pandoc_ast('* a')
    _test_pandoc_ast('* a b')
    _test_pandoc_ast('* a\n* b')
    _test_pandoc_ast('* a\n    * b')
    _test_pandoc_ast('* a b\n* c *d*\n    * e f\n    * g\n* h')


def test_pandoc_ast_ordered_list():
    _test_pandoc_ast('1. a')
    _test_pandoc_ast('2. a')
    _test_pandoc_ast('1. a b')
    _test_pandoc_ast('1. a\n2. b')
    _test_pandoc_ast('1. a\n    2. b')
    _test_pandoc_ast('1. a b\n2. c *d*\n    3. e f\n    4. g\n* h')


def test_pandoc_ast_ordered_list_style():
    _test_pandoc_ast('(i) a')
    _test_pandoc_ast('(ii) a\n1. b\n    (A)  c')
