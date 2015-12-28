# -*- coding: utf-8 -*-

"""Test AST functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import yield_fixture, raises

from .._ast import (AST, Block, Inline, to_json, from_json,
                    _remove_json_meta, ae,)


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@yield_fixture
def json():
    json = [{'unMeta': {}}, [
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
    yield json


@yield_fixture
def ast():
    ast = AST()

    # First block
    block = Block(name='Para',
                  inlines=['hello',
                           Inline(name='Space'),
                           ])
    block.add_metadata(zero=0)
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

def test_ae():
    ae(1, 1)
    ae(1., 1)

    ae({'a': 1, 'm': {}}, {'a': 1})
    with raises(AssertionError):
        ae({'a': 1, 'b': {}}, {'a': 1})

    ae('abc\n', 'abc\n')
    with raises(AssertionError):
        ae('abc\n', 'abc')


def test_remove_json_meta(json):
    json = _remove_json_meta(json)
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
    assert json == expected


def test_to_json(json, ast):
    json_converted = to_json(ast)
    assert json_converted == json


def test_from_json(json, ast):
    ast_converted = from_json(json)
    assert ast_converted == ast
