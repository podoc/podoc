# -*- coding: utf-8 -*-

"""Test Notebook plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from podoc.markdown import Markdown
from podoc.utils import get_test_file_path
from .._notebook import open_notebook, NotebookReader


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Test Notebook
#------------------------------------------------------------------------------

def test_notebook_reader_1():
    # Open a test notebook with just 1 Markdown cell.
    path = get_test_file_path('notebook', 'hello.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    ast = NotebookReader().read(notebook)
    ast.show()
    # Check that the AST is equal to the one of a simple Mardown line.
    ast_1 = Markdown().read_markdown('hello *world*')
    assert ast == ast_1
