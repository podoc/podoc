# -*- coding: utf-8 -*-

"""Tree."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from six import string_types, u
from six.moves import zip_longest

from .utils import Bunch

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Tree transformer
#------------------------------------------------------------------------------

class TreeTransformer(object):
    """Transform any kind of tree.

    By default, this object acts on Node instances. However, derived
    classes can act on other types of trees, for example nested dictionaries.

    """

    # To override
    # -------------------------------------------------------------------------

    def get_node_name(self, node):
        """Return the name of a node.

        Must be overriden.

        """
        return node.name

    def get_node_children(self, node):
        """Return the list of children of a node.

        Must be overriden.

        """
        return node.children

    def set_next_child(self, child, next_child):
        """To be overriden. Set the next and previous children."""
        if child is not None and not isinstance(child, string_types):
            child.nxt = next_child
        if next_child is not None and not isinstance(next_child, string_types):
            next_child.prv = child

    # Transformation methods
    # -------------------------------------------------------------------------

    def transform_children(self, node):
        out = []
        children = self.get_node_children(node)
        for child, next_child in zip_longest(children, children[1:]):
            # Double-linked list for children.
            self.set_next_child(child, next_child)
            transformed_children = self.transform(child)
            if isinstance(transformed_children, list):
                out.extend(transformed_children)
            else:
                out.append(transformed_children)
        return out

    def transform_str(self, contents):
        return contents

    def transform_Node(self, node):
        return node

    def get_transform_func(self, node):
        assert node is not None
        name = ('str' if isinstance(node, string_types)
                else self.get_node_name(node))
        return getattr(self, 'transform_' + name, self.transform_Node)

    def transform(self, node):
        """Transform a node and the tree below it."""
        return self.get_transform_func(node)(node)


#------------------------------------------------------------------------------
# Node
#------------------------------------------------------------------------------

class Node(Bunch):
    """Generic node type, represents a tree."""
    def __init__(self, name='Node', children=None, **kwargs):
        super(Node, self).__init__(**kwargs)
        assert isinstance(name, string_types)
        self.name = name
        self.children = children or []
        assert isinstance(self.children, list)

    def add_child(self, child):
        """A child is either a Node or a string."""
        assert isinstance(child, (Node, string_types))
        self.children.append(child)
        return child

    def __repr__(self):
        return '<Node %s with %d children>' % (self.name, len(self.children))

    def show(self):
        print(show_tree(self, lambda node: node.name,
                        lambda node: node.children))


#------------------------------------------------------------------------------
# Show tree
#------------------------------------------------------------------------------

class TreePrinter(TreeTransformer):
    prefix_t = u('├─ ')
    prefix_l = u('└─ ')
    prefix_d = u('│  ')

    def __init__(self, get_node_name, get_node_children):
        self._get_node_name = get_node_name
        self._get_node_children = get_node_children

    def get_node_name(self, node):
        return self._get_node_name(node)

    def get_node_children(self, node):
        return self._get_node_children(node)

    def transform_Node(self, node):
        pt, pl, pd = self.prefix_t, self.prefix_l, self.prefix_d
        out = ''
        l = '\n'.join(self.transform_children(node)).splitlines()
        n = len(l)
        for i, _ in enumerate(l):
            # Choose the prefix.
            prefix = pt if i < n - 1 else pl
            prefix = (pd if (pt in _ or pl in _)
                      else prefix)
            out += prefix + _ + '\n'
        out = out.strip()
        if out:
            out = '\n' + out
        return node.name + out


def show_tree(node, get_node_name, get_children_name):
    tp = TreePrinter(get_node_name, get_children_name)
    return tp.transform(node)
