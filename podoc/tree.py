# -*- coding: utf-8 -*-

"""Tree."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from itertools import zip_longest
import logging

from .utils import Bunch, _shorten_string

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
        if child is not None and not isinstance(child, str):
            child._visit_meta['nxt'] = next_child
        if next_child is not None and not isinstance(next_child, str):
            next_child._visit_meta['prv'] = child

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
        # Remove None children.
        return [_ for _ in out if _ is not None]

    def transform_str(self, contents):
        return contents

    def transform_Node(self, node):
        return node  # pragma: no cover

    def get_transform_func(self, node):
        assert node is not None
        name = ('str' if isinstance(node, str)
                else self.get_node_name(node))
        return getattr(self, 'transform_' + name, self.transform_Node)

    def transform(self, node):
        """Transform a node and the tree below it."""
        return self.get_transform_func(node)(node)


#------------------------------------------------------------------------------
# Node
#------------------------------------------------------------------------------

def _remove_visit_meta(node):
    if '_visit_meta' in node:
        node._visit_meta = {}
    return node


class Node(Bunch):
    """Generic node type, represents a tree."""
    def __init__(self, name='Node', children=None, **kwargs):
        super(Node, self).__init__(**kwargs)
        self._visit_meta = {}
        # Empty names are forbidden.
        assert name
        assert isinstance(name, str)
        self.name = name
        self.children = children or []
        assert isinstance(self.children, list)

    def add_child(self, child):
        """A child is either a Node or a string."""
        assert isinstance(child, (Node, str))
        self.children.append(child)
        return child

    def display(self):
        """Print-friendly representation of a node, used in tree show()."""
        return self.name

    def __eq__(self, other):
        """Ensure that nxt and prv items are discarded when testing
        the equality of two trees."""
        self = filter_tree(self, _remove_visit_meta)
        return super(Node, self).__eq__(filter_tree(other, _remove_visit_meta))

    def copy(self):
        node = super(Node, self).copy()
        node = self.__class__(**node)
        node.children = [child.copy() if hasattr(child, 'copy') else child
                         for child in node.children]
        return node

    def show(self):
        print(show_tree(self, lambda node: node.name,
                        lambda node: node.children))

    def __repr__(self):
        """Display the pandoc JSON representation of the tree."""
        return show_tree(self, lambda node: node.name,
                         lambda node: node.children)


def filter_tree(tree, func):
    class FilterTransformer(TreeTransformer):
        def transform_Node(self, node):
            node = func(node.copy())
            if node:
                node.children = self.transform_children(node)
            return node
    return FilterTransformer().transform(tree)


#------------------------------------------------------------------------------
# Show tree
#------------------------------------------------------------------------------

class TreePrinter(TreeTransformer):
    prefix_t = '├─ '
    prefix_l = '└─ '
    prefix_d = '│  '

    def __init__(self, get_node_name=None, get_node_children=None):
        self._get_node_name = get_node_name or (lambda n: n.name)
        self._get_node_children = get_node_children or (lambda n: n.children)

    def get_node_name(self, node):
        return self._get_node_name(node)

    def get_node_children(self, node):
        return self._get_node_children(node)

    def transform_str(self, contents):
        # Escape new lines in strings.
        return contents.replace('\n', '\\n')

    def transform_Node(self, node):
        pt, pl, pd = self.prefix_t, self.prefix_l, self.prefix_d
        out = ''
        l = '\n'.join(self.transform_children(node))
        l = l.splitlines()
        # Split long strings in the tree representation.
        if len(l) == 1:
            l = [_shorten_string(l[0])]
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
        # NOTE: the print-friendly representation of a node is available
        # in node.display() if available, otherwise str(node).
        # Overriding __repr__() leads to hard-to-debug equality assertions
        # with py.test.
        return getattr(node, 'display', lambda: str(node))() + out


def show_tree(node, get_node_name=None, get_children_name=None):
    tp = TreePrinter(get_node_name, get_children_name)
    return tp.transform(node)
