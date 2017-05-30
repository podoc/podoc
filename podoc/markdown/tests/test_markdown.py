# -*- coding: utf-8 -*-

"""Test Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import fixture
from six import string_types

from podoc.ast import ASTNode
from .._markdown import MarkdownPlugin


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

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
# Test Markdown plugin
#------------------------------------------------------------------------------

def test_markdown_read(ast, markdown):
    assert MarkdownPlugin().read(markdown) == ast


def test_markdown_write(ast, markdown):
    assert MarkdownPlugin().write(ast) == markdown


# -----------------------------------------------------------------------------
# Test Markdown renderer inline
# Check safe round-tripping on CommonMark -> AST -> CommonMark
# -----------------------------------------------------------------------------

def _tree_contains_nodes(ast, names):
    if isinstance(ast, string_types):
        return False
    if ast.name in names:
        return True
    return all(any(_tree_contains_nodes(child, (name,))
                   for child in ast.children)
               for name in names)


def _test_renderer(s, *contains_nodes):
    """Test the renderer on a string."""
    # Parse the string with CommonMark-py.
    mp = MarkdownPlugin()
    ast = mp.read(s)
    ast.show()
    # Check that the tree contains a node.
    if contains_nodes:
        assert _tree_contains_nodes(ast, contains_nodes)
    assert mp.write(ast) == s


def test_markdown_renderer_simple():
    _test_renderer('hello')
    _test_renderer('hello world')
    _test_renderer('hello *world*', 'Emph')
    _test_renderer('hello **world**', 'Strong')


def test_markdown_renderer_link():
    _test_renderer('[hello](world)', 'Link')
    _test_renderer('![hello](world)', 'Image')


def test_markdown_renderer_codeinline():
    _test_renderer('hello `world`', 'Code')


# -----------------------------------------------------------------------------
# Test Markdown renderer block
# -----------------------------------------------------------------------------

def test_markdown_renderer_header():
    _test_renderer('# Hello', 'Header')
    _test_renderer('## Hello world', 'Header')


def test_markdown_renderer_codeblock():
    _test_renderer('```\nhello world\n```', 'CodeBlock')
    _test_renderer('```python\nhello world\n```', 'CodeBlock')


def test_markdown_renderer_blockquote():
    _test_renderer('> hello world', 'BlockQuote')
    _test_renderer('> hello world\n> end', 'BlockQuote')


def test_markdown_renderer_bullet_list():
    _test_renderer('* Item 1')
    _test_renderer('* Item 1\n* Item 2')
    # TODO: fix the following test
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


def test_markdown_renderer_headers():
    _test_renderer('# 1\n\n# 2')
    _test_renderer('# 1\n\n## 2')
    _test_renderer('## 2\n\n# 1')


def test_markdown_renderer_codeblocks():
    _test_renderer('```python\nhello world\n```\n\n```\nother\n```')


def test_markdown_renderer_ordered_bullet():
    _test_renderer('1. Item 1\n\n* Bullet',
                   'BulletList', 'OrderedList')
    _test_renderer('* Bullet\n\n1. Item 1',
                   'BulletList', 'OrderedList')
    _test_renderer('1. Item 1\n2. Item 2\n\n* Bullet',
                   'BulletList', 'OrderedList')
    _test_renderer('1. Item 1\n2. Item 2\n\n* Bullet\n\n3. Item 3',
                   'BulletList', 'OrderedList')


def test_markdown_math_inline():
    _test_renderer('a $x*x=y*y$ b', 'Math')


def test_markdown_math_block():
    _test_renderer(r'$$\int_a^b f_0(x) dx$$', 'MathBlock')
    _test_renderer(r'$$\begin{eqnarray}\nx &= y\n\end{eqnarray}$$',
                   'MathBlock')
