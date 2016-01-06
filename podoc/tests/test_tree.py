# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from textwrap import dedent

from pytest import fixture

from ..utils import captured_output
from ..tree import Node, TreeTransformer


#------------------------------------------------------------------------------
# Testing tree
#------------------------------------------------------------------------------

@fixture
def root():
    # Create a tree.
    root = Node('root', hello='world')
    root.add_child(Node('1'))
    root.children[0].add_child(Node('1.1'))
    root.children[0].children[0].add_child('1.1.1')
    root.children[0].children[0].add_child('1.1.2')
    root.children[0].add_child('1.2')
    root.add_child('2')
    return root


def test_show_tree(root):
    assert 'root' in ('%s' % root)
    with captured_output() as (out, err):
        root.show()
    expected = '''
        root
        ├─ 1
        │  ├─ 1.1
        │  │  ├─ 1.1.1
        │  │  └─ 1.1.2
        │  └─ 1.2
        └─ 2
        '''
    assert out.getvalue().strip() == dedent(expected).strip()


def test_transform_1(root):

    t = TreeTransformer()
    t.set_fold(lambda l: '\n'.join(l))

    @t.register
    def transform_Node(node):
        return node.name + '\n' + t.get_inner_contents(node)

    expected = '''
        root
        1
        1.1
        1.1.1
        1.1.2
        1.2
        2
        '''
    assert t.transform(root) == dedent(expected).strip()


def test_transform_2(root):

    t = TreeTransformer()
    t.set_fold(lambda _: _)

    @t.register
    def transform_Node(node):
        return {'t': node.name, 'c': t.get_inner_contents(node)}

    assert t.transform(root) == {'t': 'root',
                                 'c': [{'t': '1',
                                        'c': [{'t': '1.1',
                                               'c': ['1.1.1', '1.1.2']},
                                              '1.2']}, '2']}
