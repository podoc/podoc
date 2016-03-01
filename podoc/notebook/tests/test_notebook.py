# -*- coding: utf-8 -*-

"""Test Notebook plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

# from podoc.markdown import Markdown
from .._notebook import open_notebook, NotebookReader


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Test Notebook
#------------------------------------------------------------------------------

def test_notebook_reader():
    curdir = op.realpath(op.dirname(__file__))
    dirname = op.realpath(op.join(curdir, '../'))
    path = op.join(dirname, 'test_files', 'hello.ipynb')
    notebook = open_notebook(path)
    ast = NotebookReader().read(notebook)
    ast.show()
    # Markdown().read_markdown('hello *world*').show()
    # TODO: assert node == fails because of nxt/prv
