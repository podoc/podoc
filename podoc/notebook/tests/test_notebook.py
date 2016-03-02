# -*- coding: utf-8 -*-

"""Test Notebook plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from podoc.markdown import Markdown
from podoc.utils import get_test_file_path, open_text, assert_equal
from .._notebook import open_notebook, NotebookReader


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Test Notebook
#------------------------------------------------------------------------------

def test_notebook_reader_hello():
    # Open a test notebook with just 1 Markdown cell.
    path = get_test_file_path('notebook', 'hello.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    ast = NotebookReader().read(notebook)
    ast.show()
    # Check that the AST is equal to the one of a simple Mardown line.
    ast_1 = Markdown().read_markdown('hello *world*')
    assert ast == ast_1


def test_notebook_reader_code():
    # Open a test notebook with a code cell.
    path = get_test_file_path('notebook', 'code.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    ast = NotebookReader().read(notebook)
    ast.show()

    # Compare with the markdown version.
    path = get_test_file_path('markdown', 'code.md')
    markdown = open_text(path)
    assert_equal(Markdown().write_markdown(ast), markdown)
