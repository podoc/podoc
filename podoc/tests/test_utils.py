# -*- coding: utf-8 -*-

"""Test utility functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from pytest import raises

from ..ast import AST
from ..utils import Bunch, _test_file_path, _load_test_file


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_bunch():
    obj = Bunch()
    obj['a'] = 1
    assert obj.a == 1
    obj.b = 2
    assert obj['b'] == 2
    assert obj.copy().a == 1


def test_file_path():
    assert op.exists(_test_file_path('hello_ast.py'))


def test_load_test_file():
    assert isinstance(_load_test_file('hello_ast.py'), AST)
    with raises(ValueError):
        _load_test_file('hello.idontexist')
