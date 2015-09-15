# -*- coding: utf-8 -*-

"""Test AST functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from ..ast import AST, Block, Inline, to_pandoc


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_ast():
    pandoc_json = [{'unMeta': {'k': 'v'}}, [
                   {'c': [{'c': 'hello', 't': 'Str'},
                          {'c': [], 't': 'Space'},
                          {'c': [{'c': 'world', 't': 'Str'}], 't': 'Emph'}],
                    't': 'Para'},
                   {'c': [{'c': 'hi!', 't': 'Str'}],
                    't': 'Para'}]
                   ]

    ast = AST()
    ast.add_metadata(k='v')

    # First block
    block = Block(name='Para',
                  inlines=['hello',
                           Inline(name='Space'),
                           ])
    block.add_metadata(kb='vb')
    inline = Inline(name='Emph')
    inline.set_contents([])
    inline.add_contents('world')
    block.add_inline(inline)
    ast.add_block(block)

    # Second block
    block = Block(name='Para',
                  inlines=['hi!'])
    ast.add_block(block)

    assert to_pandoc(ast) == pandoc_json
