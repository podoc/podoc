# -*- coding: utf-8 -*-

"""Test AST functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json

from pytest import fixture

from .._ast import (ASTNode, ast_from_pandoc,
                    _merge_str, _split_spaces)
from podoc.core import Podoc
from podoc.utils import has_pandoc, pandoc, PANDOC_MARKDOWN_FORMAT


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@fixture
def ast_pandoc():
    ast_dict = [{'unMeta': {}}, [
                {'c': [{'c': 'hello', 't': 'Str'},
                       {'c': [], 't': 'Space'},
                       {'c': [{'c': 'world', 't': 'Str'}], 't': 'Emph'}],
                 't': 'Para',
                 },
                {'c': [{'c': 'hi!', 't': 'Str'}],
                 't': 'Para',
                 }]
                ]
    return ast_dict


@fixture
def ast():
    ast = ASTNode('root')

    # First block
    block = ASTNode(name='Para',
                    children=['hello ',
                              ])
    inline = ASTNode(name='Emph')
    inline.add_child('world')
    block.add_child(inline)
    ast.add_child(block)

    assert block.is_block()
    assert not block.is_inline()
    inline.validate()

    assert not inline.is_block()
    assert inline.is_inline()
    inline.validate()

    # Second block
    block = ASTNode(name='Para',
                    children=['hi!'])
    ast.add_child(block)
    return ast


#------------------------------------------------------------------------------
# Tests AST <-> pandoc
#------------------------------------------------------------------------------

def test_repr_ast():
    assert str(ASTNode('Para')) == '[{"unMeta":{}},[]]'


def test_merge_str():
    assert _merge_str(['a', 'b', None, 'c']) == ['ab', None, 'c']


def test_split_spaces():
    assert _split_spaces('a  b') == ['a', '', 'b']
    assert _split_spaces('a b  \tc,d ') == ['a', '', 'b', '', 'c,d', '']


def test_to_pandoc(ast, ast_pandoc):
    assert ast.to_pandoc() == ast_pandoc


def test_from_pandoc(ast, ast_pandoc):
    assert ast_from_pandoc(ast_pandoc) == ast


def test_unknown_node():
    ast = ASTNode('root')
    ast.add_child(ASTNode('Para'))
    ast.add_child(ASTNode('Unknown', children=[ASTNode('Para')]))

    # AST -> pandoc -> AST should remove the Unknown node.
    ast_trim = ast_from_pandoc(ast.to_pandoc())

    ast_expected = ASTNode('root', children=[ASTNode('Para'), ASTNode('Para')])
    assert ast_trim == ast_expected


#------------------------------------------------------------------------------
# Tests with pandoc
#------------------------------------------------------------------------------

def test_pandoc_conv():
    podoc = Podoc()
    html = '<p><a href="b">a</a></p>'
    assert podoc.convert(html,
                         lang_list=['html', 'ast', 'markdown']) == '[a](b)'
    assert podoc.convert('[a](b)',
                         lang_list=['markdown', 'ast', 'rst']) == '`a <b>`__\n'


# We use strict Markdown, but we allow fancy lists.

def _test_pandoc_ast(s):
    """Check the compatibility of the podoc AST with pandoc.

    * Perform Markdown -> pandoc AST dict -> podoc AST -> podoc AST dict
    * Check that pandoc AST dict = podoc AST dict

    """
    if not has_pandoc():  # pragma: no cover
        raise ImportError("pypandoc is not available")
    ast_dict = json.loads(pandoc(s, 'json', format=PANDOC_MARKDOWN_FORMAT))
    ast = ast_from_pandoc(ast_dict)
    ast.show()
    assert ast.to_pandoc() == ast_dict


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
    _test_pandoc_ast('```python\nhello world\n```')
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
    _test_pandoc_ast('1) a b\n2) c d')
    _test_pandoc_ast('1. a\n    2. b')
    _test_pandoc_ast('1. a b\n2. c *d*\n    3. e f\n    4. g\n* h')


def test_pandoc_math():
    _test_pandoc_ast('$x$')
    _test_pandoc_ast('$x$=y')
    _test_pandoc_ast('$x=y$')
    _test_pandoc_ast('$$x=y$$')
    _test_pandoc_ast(r'$$\begin{eqnarray}\nx &= y\n\end{eqnarray}$$')
