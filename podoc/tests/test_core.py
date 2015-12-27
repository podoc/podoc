# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from pytest import raises

from ..core import Podoc, _find_path, _get_annotation


#------------------------------------------------------------------------------
# Tests utils
#------------------------------------------------------------------------------

def test_get_annotation():
    assert _get_annotation(lambda: None, 'a') is None


def test_find_path():
    assert _find_path([(1, 2), (2, 3)], 1, 2) == [1, 2]
    assert _find_path([(1, 2), (2, 3)], 1, 3) == [1, 2, 3]
    assert _find_path([(1, 2), (2, 3), (1, 4), (4, 5)], 1, 5) == [1, 4, 5]


#------------------------------------------------------------------------------
# Tests podoc
#------------------------------------------------------------------------------

def test_podoc_fail():
    p = Podoc()
    with raises(ValueError):
        p.convert('hello', ['a', 'b'])


def test_podoc_1():
    p = Podoc()

    @p.register(source='lower', target='upper')
    def toupper(text):
        return text.upper()

    assert p.conversion_pairs == [('lower', 'upper')]
    assert p.get_func('lower', 'upper')
    assert p.convert('hello', ['lower', 'upper']) == 'HELLO'

    @p.register(source='upper', target='lower')
    def tolower(text):
        return text.lower()

    assert p.convert('Hello', ['lower', 'upper', 'lower']) == 'hello'


def test_podoc_2():
    p = Podoc()

    class A(object):
        pass

    class B(object):
        def __init__(self, obj):
            self.obj = obj

    @p.register(source=A, target=B)
    def a2b(obj):
        return B(obj)

    a = A()
    assert isinstance(p.convert(a, [A, B]), B)
    assert isinstance(p.convert(a, ['a', 'b']), B)
