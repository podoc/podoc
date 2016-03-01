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
        contents = cell.source
        self.tree.children.append(Node('CodeBlock', children=[contents]))

    def read_raw(self, cell):
        # TODO
        pass
