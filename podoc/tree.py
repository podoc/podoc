# -*- coding: utf-8 -*-

"""Tree."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from itertools import zip_longest
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

    @property
    def ascii_tree(self):
        """Return an ASCII representation of the tree under the current node.
        """
        t = TreeTransformer()
        t.set_fold(lambda l, node=None: '\n'.join(l))

        @t.register
        def transform_Node(node):
            """This function is called on every node. It generates an ASCII
            tree.
            """
            prefix_t = '├─ '
            prefix_l = '└─ '
            prefix_d = '│  '
            out = ''
            l = t.get_inner_contents(node).splitlines()
            n = len(l)
            for i, _ in enumerate(l):
                # Choose the prefix.
                prefix = prefix_t if i < n - 1 else prefix_l
                prefix = (prefix_d if (prefix_t in _ or prefix_l in _)
                          else prefix)
                out += prefix + _ + '\n'
            out = out.strip()
            if out:
                out = '\n' + out
            return node.name + out

        s = t.transform(self)
        return s

    def show(self):
        print(self.ascii_tree)


#------------------------------------------------------------------------------
# Tree transformer
#------------------------------------------------------------------------------

class TreeTransformer(object):
    def __init__(self):
        self._funcs = {'str': self.transform_str,
                       'Node': self.transform_Node}
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
        It arguments must be `node`.
        The function can call `self.get_inner_contents(node)` to get the
        transformed output of all of the node's children.

        Generally, this method should return a string. The fold function should
        return an object of the same type.

        """
        name = func.__name__
        prefix = 'transform_'
        assert name.startswith(prefix)
        name = name[len(prefix):]
        self._funcs[name] = func

    def transform_children(self, node):
        out = []
        for child, next_child in zip_longest(node.children, node.children[1:]):
            # Double-linked list for children.
            # TODO: do this when creating the tree, in setattr children maybe?
            if isinstance(child, Node):
                child.nxt = next_child
            if isinstance(next_child, Node):
                next_child.prv = child
            out.append(self.transform(child))
        return out

    def get_inner_contents(self, node):
        return self._fold(self.transform_children(node), node=node)

    def transform_str(self, contents):
        return contents

    def transform_Node(self, node):
        """Fallback transform functions when no function is registered
        for the given node."""
        return ''

    def transform(self, node):
        """Transform a node and the tree below it."""
        if isinstance(node, string_types) and 'str' in self._funcs:
            return self._funcs['str'](node)
        assert isinstance(node, Node)
        # Get the registered function for that name.
        func = self._funcs.get(node.name, self._funcs['Node'])
        # Call the function.
        assert func
        # Pass the node and the inner contents.
        return func(node)
