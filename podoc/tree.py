# -*- coding: utf-8 -*-

"""Tree."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from six import string_types

from .utils import Bunch

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Node
#------------------------------------------------------------------------------

class Node(Bunch):
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


#------------------------------------------------------------------------------
# Tree transformer
#------------------------------------------------------------------------------

class TreeTransformer(object):
    def __init__(self):
        self._funcs = {'String': lambda node: node,
                       'Node': lambda node: ''}
        self._fold = lambda l: ''.join(l)

    def set_fold(self, func):
        """The fold function is used in AST -> format transformation.

        It is a function that takes a list of children and returns a single
        object.

        For every node, a conversion function is called on the children, and
        the results are reduced by the fold function. This process is applied
        recursively up to the root. The output is then the converted document.

        By default, this is lambda children: ''.join(children) (only valid on
        text formats).

        """
        self._fold = func

    def register(self, func):
        """Register a transformer function for a given node type.

        The function's name must be `transform_NodeName`.

        The node possess a special attribute `inner_contents` which
        is the concatenation of the transformed children.

        Generally, this method should return a string. The fold function should
        return an object of the same type.

        """
        name = func.__name__
        prefix = 'transform_'
        assert name.startswith(prefix)
        name = name[len(prefix):]
        self._funcs[name] = func

    def transform(self, node):
        """Transform a node and all of its children recursively."""
        if isinstance(node, string_types) and 'String' in self._funcs:
            return self._funcs['String'](node)
        assert isinstance(node, Node)
        # Get the registered function for that name.
        func = self._funcs.get(node.name, self._funcs['Node'])
        # Recursively transform all children.
        l = [self.transform(child) for child in node.children]
        # Set the inner contents.
        node.inner_contents = self._fold(l)
        # Call the function on the node. The function has access
        # to the inner contents (concatenated transformation of the
        # children).
        if func:
            return func(node)
