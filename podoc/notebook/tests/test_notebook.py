# -*- coding: utf-8 -*-

"""Test Notebook plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from podoc.markdown import Markdown
from .._notebook import open_notebook, NotebookReader


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Test Notebook
#------------------------------------------------------------------------------

def test_notebook_reader_1():
    # Open a test notebook with just 1 Markdown cell.
    curdir = op.realpath(op.dirname(__file__))
    dirname = op.realpath(op.join(curdir, '../'))
    path = op.join(dirname, 'test_files', 'hello.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    ast = NotebookReader().read(notebook)
    ast.show()
    # Check that the AST is equal to the one of a simple Mardown line.
    ast_1 = Markdown().read_markdown('hello *world*')
    assert ast == ast_1
