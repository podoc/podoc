# -*- coding: utf-8 -*-

"""Test AST functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import yield_fixture, raises

from .._ast import (AST, Block, Inline, _remove_json_meta, ae,)


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


def test_remove_json_meta(ast_dict):
    ast_dict = _remove_json_meta(ast_dict)
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
