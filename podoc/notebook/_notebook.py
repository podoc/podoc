# -*- coding: utf-8 -*-

"""Notebook plugin.

This plugin implements Notebook <-> AST.

When converting a notebook to an AST, some of the structure of the notebook
is preserved. While the Markdown cells are considered as normal contents,
code cells with their outputs are encapsulated in a special `CodeCell` node
in the AST. The first child is the source, while the next children are the
outputs.

When converting a regular AST to a notebook, we have to choose some conventions
to decide how to organize Markdown cells and code cells, since that
information has no reason to be in the AST.

First, for any given CodeBlock in an AST, we have to decide whether it is
executable (i.e. part of a code cell) or if it is a regular Markdown content.
As a first approach, let's just consider that all Python code blocks are
executable. We'll have to improve that later.

Next, we have to decide, among the blocks following a CodeBlock, which are
part of the cell's outputs. We go with the following convention:

* A CodeBlock with the `output` language (i.e. ```output) is a text output.
* A Para with just an image is an output
* Any other block means the end of the cell's outputs.

This all could (and should) be improved...

"""


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
        node = Node('CodeCell')
        # The first child is the source.
        node.add_child(Node('CodeBlock', children=[cell.source]))
        # Then, we add one extra child per output.
        for output in cell.outputs:
            if output.output_type == 'stream':
                child = output.text
            elif output.output_type in ('display_data', 'execute_result'):
                # Output text node.
                text = output.data.get('text/plain', '')
                # Get the image, if any.
                img_b64 = output.data.get('image/png', None)
                if img_b64:
                    child = Node('Image', children=[text])
                else:
                    child = text
            node.add_child(Node('CodeBlock', children=[child]))
        self.tree.children.append(node)

    def read_raw(self, cell):
        # TODO
        pass
