# -*- coding: utf-8 -*-

"""Notebook plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

import nbformat

from podoc.markdown import Markdown
from podoc.tree import Node  # , TreeTransformer

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Notebook reader
#------------------------------------------------------------------------------

_NBFORMAT_VERSION = 4


def open_notebook(path):
    with open(path, 'r') as f:
        return nbformat.read(f, _NBFORMAT_VERSION)


class NotebookReader(object):
    def read(self, notebook):
        self.tree = Node('root')
        for cell in notebook.cells:
            getattr(self, 'read_{}'.format(cell.cell_type))(cell)
        return self.tree

    def read_markdown(self, cell):
        contents = cell.source
        ast = Markdown().read_markdown(contents)
        assert len(ast.children) == 1
        self.tree.children.append(ast.children[0])

    def read_code(self, cell):
        node = Node('CodeBlock')
        # The first child is the source.
        node.add_child(cell.source)
        # Then, we add one extra child per output.
        for output in cell.outputs:
            if output.output_type == 'stream':
                child = Node('Text', children=[output.text])
            elif output.output_type in ('display_data', 'execute_result'):
                # Output text node.
                text = output.data.get('text/plain', '')
                text_node = Node('Text', children=[text])
                # Get the image, if any.
                img_b64 = output.data.get('image/png', None)
                if img_b64:
                    child = Node('Image', children=[text_node])
                else:
                    child = text_node
            node.add_child(Node('Para', children=[child]))
        self.tree.children.append(node)

    def read_raw(self, cell):
        # TODO
        pass
