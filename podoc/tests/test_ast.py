# -*- coding: utf-8 -*-

"""Test AST functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import yield_fixture

from ..ast import AST, Block, Inline, to_json, from_json


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@yield_fixture
def json():
    json = [{'unMeta': {'k': 'v'}}, [
            {'c': [{'c': 'hello', 't': 'Str'},
                   {'c': [], 't': 'Space'},
                   {'c': [{'c': 'world', 't': 'Str'}], 't': 'Emph'}],
             't': 'Para'},
            {'c': [{'c': 'hi!', 't': 'Str'}],
             't': 'Para'}]
            ]
    yield json


@yield_fixture
def ast():
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
    yield ast


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_to_json(json, ast):
    json_converted = to_json(ast)
    assert json_converted == json


def test_from_json(json, ast):
    ast_converted = from_json(json)
    # NOTE: block metadata is lost by json.
    ast.blocks[0].meta = {}
    assert ast_converted == ast
