# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from textwrap import dedent

from pytest import fixture

from ..utils import captured_output
from ..tree import Node, TreeTransformer, show_tree, filter_tree


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


def test_copy(root):
    """Make sure copy is recursive."""
    root_2 = root.copy()
    root_2.children[0].add_child('new')
    assert 'new' in root_2.children[0].children
    assert 'new' not in root.children[0].children
    assert root_2 != root


def test_show_tree_1():
    root = Node('root')
    root.add_child(Node('1'))
    root.add_child(Node('2'))
    with captured_output() as (out, err):
        root.show()
    expected = '''
        root
        ├─ 1
        └─ 2
        '''
    assert out.getvalue().strip() == dedent(expected).strip()


def test_show_tree_2(root):
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


def test_transform_3(root):

    class MyTreeTransformer(TreeTransformer):
        def transform_Node(self, node):
            node = node.copy()
            node.name += ' visited'
            node.children = self.transform_children(node)
            return node

    t = MyTreeTransformer()
    assert t.transform(root).name == 'root visited'
    assert t.transform(root).children[0].name == root.children[0].name + ' visited'


def test_filter(root):
    assert root == root
    assert filter_tree(root, lambda node: node) == root

    def root_only(node):
        if node.name == 'root':
            node.children = []
            return node
    assert filter_tree(root, root_only) == Node('root', hello='world')

    def remove_ones(node):
        if '1' in node.name:
            return
        return node
    root_without_ones = root.copy()
    root_without_ones.children.pop(0)
    assert filter_tree(root, remove_ones) == root_without_ones
