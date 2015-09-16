# -*- coding: utf-8 -*-

"""Test conftest functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from podoc.ast import AST


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

def test_hello_pandoc(hello_pandoc):
    assert len(hello_pandoc) == 2
    assert 'unMeta' in hello_pandoc[0]
    blocks = hello_pandoc[1]
    assert len(blocks) == 1
    assert blocks[0]['t'] == 'Para'


def test_hello_ast(hello_ast):
    assert isinstance(hello_ast, AST)
    assert hello_ast.blocks[0].name == 'Para'
    assert hello_ast.blocks[0].inlines[0] == 'hello'
    assert hello_ast.blocks[0].inlines[2].name == 'Emph'
