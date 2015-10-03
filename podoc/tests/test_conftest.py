# -*- coding: utf-8 -*-

"""Test conftest functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from podoc.ast import AST


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

def test_hello_json(hello_json):
    assert len(hello_json) == 2
    assert 'unMeta' in hello_json[0]
    blocks = hello_json[1]
    assert len(blocks) == 1
    assert blocks[0]['t'] == 'Para'


def test_hello_ast(hello_ast):
    assert isinstance(hello_ast, AST)
    assert hello_ast.blocks[0].name == 'Para'
    assert hello_ast.blocks[0].inlines[0] == 'hello'
    assert hello_ast.blocks[0].inlines[2].name == 'Emph'


def test_hello_markdown(hello_markdown):
    assert hello_markdown == 'hello *world*\n'
