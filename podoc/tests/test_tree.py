# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from textwrap import dedent

from six import u
from pytest import fixture

from ..utils import captured_output
from ..tree import Node, TreeTransformer, show_tree


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


def test_show_tree_1():
    root = Node('root')
    root.add_child(Node('1'))
    root.add_child(Node('2'))
    with captured_output() as (out, err):
        root.show()
    expected = u('''
        root
        ├─ 1
        └─ 2
        ''')
    assert out.getvalue().strip() == dedent(expected).strip()


def test_show_tree_2(root):
    assert 'root' in ('%s' % root)
    with captured_output() as (out, err):
        root.show()
    expected = u('''
        root
        ├─ 1
        │  ├─ 1.1
        │  │  ├─ 1.1.1
        │  │  └─ 1.1.2
        │  └─ 1.2
        └─ 2
        ''')
    assert out.getvalue().strip() == dedent(expected).strip()


def test_show_tree_3():
    tree = Node('root')
    tree.add_child('-' * 50)
    assert '(...)' in show_tree(tree)


def test_transform_1(root):

    class MyTreeTransformer(TreeTransformer):
        def transform_Node(self, node):
            return node.name + '\n' + '\n'.join(self.transform_children(node))

    expected = '''
        root
        1
        1.1
        1.1.1
        1.1.2
        1.2
        2
        '''
    assert MyTreeTransformer().transform(root) == dedent(expected).strip()


def test_transform_2(root):

    class MyTreeTransformer(TreeTransformer):
        def transform_Node(self, node):
            return {'t': node.name, 'c': self.transform_children(node)}

    t = MyTreeTransformer()
    assert t.transform(root) == {'t': 'root',
                                 'c': [{'t': '1',
                                        'c': [{'t': '1.1',
                                               'c': ['1.1.1', '1.1.2']},
                                              '1.2']}, '2']}
