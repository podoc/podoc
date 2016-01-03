# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from textwrap import dedent

from pytest import fixture

from ..tree import Node, TreeTransformer


#------------------------------------------------------------------------------
# Testing tree
#------------------------------------------------------------------------------

@fixture
def root():
    # Create a tree.
    root = Node('root', hello='world')
    root.add_child(Node('1'))
    root.children[0].add_child('1.1')
    root.children[0].add_child('1.2')
    root.add_child('2')
    return root


def test_transform_1(root):
    assert 'root' in ('%s' % root)

    # Create a tree transformer.
    t = TreeTransformer()

    # The fold function takes the list of transformed children of a node,
    # and returns their concatenation.
    t.set_fold(lambda l: '\n'.join(l))

    @t.register
    def transform_Node(node):
        """This function is called on every node. It generates an ASCII tree.

        `node.inner_contents` contains the concatenated output of all
        of the node's children.

        """
        c = node.inner_contents
        prefix_t = '├─ '
        prefix_l = '└─ '
        prefix_d = '│  '
        out = ''
        l = c.splitlines()
        n = len(l)
        for i, _ in enumerate(l):
            # Choose the prefix.
            prefix = prefix_t if i < n - 1 else prefix_l
            prefix = prefix_d if _.startswith((prefix_t, prefix_l)) else prefix
            out += prefix + _ + '\n'
        return node.name + '\n' + out.strip()

    trans = t.transform(root)
    expected = '''
        root
        ├─ 1
        │  ├─ 1.1
        │  └─ 1.2
        └─ 2
        '''
    assert trans == dedent(expected).strip()


def test_transform_2(root):

    t = TreeTransformer()
    t.set_fold(lambda _: _)

    @t.register
    def transform_Node(node):
        return {'t': node.name, 'c': node.inner_contents}

    assert t.transform(root) == {'t': 'root',
                                 'c': [{'t': '1', 'c': ['1.1', '1.2']}, '2']}
