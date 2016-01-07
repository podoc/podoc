# -*- coding: utf-8 -*-

"""Test Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import fixture
from CommonMark import Parser

from podoc.ast import ASTNode
from .._markdown import (CommonMarkToAST, ASTToMarkdown, Markdown)


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@fixture
def commonmark():
    contents = 'hello *world*'
    parser = Parser()
    cm = parser.parse(contents)
    return cm


@fixture
def ast():
    # TODO: move this to conftest
    ast = ASTNode('root')

    # First block
    block = ASTNode(name='Para',
                    children=['hello '])
    inline = ASTNode(name='Emph')
    inline.add_child('world')
    block.add_child(inline)
    ast.add_child(block)
    return ast


@fixture
def markdown():
    return 'hello *world*'


#------------------------------------------------------------------------------
# Test CommonMark to AST
#------------------------------------------------------------------------------

def test_cm_to_ast(commonmark, ast):
    ast_t = CommonMarkToAST().transform_root(commonmark)
    ast.show()
    ast_t.show()
    assert ast == ast_t


#------------------------------------------------------------------------------
# Test AST to Markdown
#------------------------------------------------------------------------------

def test_ast_to_markdown(ast, markdown):
    md = ASTToMarkdown().transform(ast)
    assert md == markdown


#------------------------------------------------------------------------------
# Test Markdown plugin
#------------------------------------------------------------------------------

def test_markdown_read(ast, markdown):
    assert Markdown().read_markdown(markdown) == ast


def test_markdown_write(ast, markdown):
    assert Markdown().write_markdown(ast) == markdown


# -----------------------------------------------------------------------------
# Test Markdown renderer inline
# Check safe round-tripping on CommonMark -> AST -> CommonMark
# -----------------------------------------------------------------------------

def _test_renderer(s):
    """Test the renderer on a string."""
    # Parse the string with CommonMark-py.
    ast = Markdown().read_markdown(s)
    ast.show()
    # Render the AST to Markdown.
    contents = ASTToMarkdown().transform(ast)
    assert contents.strip() == s


def test_markdown_renderer_simple():
    _test_renderer('hello')
    _test_renderer('hello world')
    _test_renderer('hello *world*')
    _test_renderer('hello **world**')


def test_markdown_renderer_link():
    _test_renderer('[hello](world)')
    _test_renderer('![hello](world)')


def test_markdown_renderer_codeinline():
    _test_renderer('hello `world`')


# -----------------------------------------------------------------------------
# Test Markdown renderer block
# -----------------------------------------------------------------------------

def test_markdown_renderer_header():
    _test_renderer('# Hello')
    _test_renderer('## Hello world')


def test_markdown_renderer_codeblock():
    _test_renderer('```\nhello world\n```')
    _test_renderer('```python\nhello world\n```')


def test_markdown_renderer_blockquote():
    _test_renderer('> hello world')
    _test_renderer('> hello world\n> end')


def test_markdown_renderer_bullet_list():
    _test_renderer('* Item 1')
    _test_renderer('* Item 1\n* Item 2')
    # _test_renderer('* Item 1\n  * Item 1.2')


def test_markdown_renderer_ordered_list():
    _test_renderer('1. Item 1')
    _test_renderer('1. Item 1\n2. Item 2')
    _test_renderer('2. Item 1\n3. Item 2')


# -----------------------------------------------------------------------------
# Test Markdown renderer multiple blocks
# -----------------------------------------------------------------------------

def test_markdown_renderer_paras():
    _test_renderer('hello\nworld')
    _test_renderer('hello\n\nworld')


def test_markdown_renderer_ordered_bullet():
    _test_renderer('1. Item 1\n\n* Bullet')
    _test_renderer('* Bullet\n\n1. Item 1')
    # _test_renderer('1. Item 1\n2. Item 2\n\n* Bullet')
    # _test_renderer('1. Item 1\n2. Item 2\n\n* Bullet\n\n3. Item 3\n')


# TODO: compare Markdown -> AST with Markdown -> pandoc -> AST
