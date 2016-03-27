# -*- coding: utf-8 -*-

"""Test Notebook plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from podoc.markdown import MarkdownPlugin
from podoc.utils import get_test_file_path, open_text, assert_equal
from podoc.ast import ASTPlugin, ASTNode
from .._notebook import (extract_output,
                         output_filename,
                         open_notebook,
                         NotebookReader,
                         NotebookWriter,
                         wrap_code_cells,
                         )


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Test Notebook utils
#------------------------------------------------------------------------------

def test_extract_output():
    # Open a test notebook with a code cell containing an image.
    path = get_test_file_path('notebook', 'notebook.ipynb')
    notebook = open_notebook(path)
    cell = notebook.cells[4]
    mime_type, data = list(extract_output(cell.outputs[1]))
    filename = output_filename(mime_type, cell_index=4, output_index=1)
    assert filename == 'output_4_1.png'

    # Open the image file in the markdown directory.
    image_path = get_test_file_path('markdown', filename)
    with open(image_path, 'rb') as f:
        data_expected = f.read()

    # The two image contents should be identical.
    assert data == data_expected


def test_wrap_code_cells():
    # Test wrap_code_cells() with a single code cell.
    ast = ASTNode('root')
    ast.add_child(ASTNode('CodeBlock', lang='python', children=['']))

    ast_wrapped = wrap_code_cells(ast)
    ast_wrapped.show()

    ast_expected = ASTNode('root')
    ast_expected.add_child(ASTNode('CodeCell', children=[ast.children[0]]))

    assert_equal(ast_wrapped, ast_expected)


#------------------------------------------------------------------------------
# Test NotebookReader
#------------------------------------------------------------------------------

def test_notebook_reader_hello():
    # Open a test notebook with just 1 Markdown cell.
    path = get_test_file_path('notebook', 'hello.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    ast = NotebookReader().read(notebook)
    ast.show()
    # Check that the AST is equal to the one of a simple Mardown line.
    ast_1 = MarkdownPlugin().read('hello *world*')
    assert ast == ast_1


def test_notebook_reader_notebook():
    # Open a test notebook with a code cell.
    path = get_test_file_path('notebook', 'notebook.ipynb')
    notebook = open_notebook(path)
    # Convert it to an AST.
    reader = NotebookReader()
    ast = reader.read(notebook)
    ast.show()

    # Compare with the markdown version.
    path = get_test_file_path('markdown', 'notebook.md')
    markdown = open_text(path)
    assert_equal(MarkdownPlugin().write(ast), markdown)

    assert 'output_4_1.png' in reader.resources


#------------------------------------------------------------------------------
# Test NotebookWriter
#------------------------------------------------------------------------------

def test_notebook_writer_hello():
    path = get_test_file_path('ast', 'hello.json')
    ast = ASTPlugin().load(path)
    nb = NotebookWriter().write(ast)

    # Compare the notebooks.
    nb_expected = open_notebook(get_test_file_path('notebook', 'hello.ipynb'))
    # Ignore some fields when comparing the notebooks.
    assert_equal(nb, nb_expected, ('metadata', 'kernelspec'))


def test_notebook_writer_notebook():
    path = get_test_file_path('ast', 'notebook.json')
    ast = ASTPlugin().load(path)

    # Load the image.
    fn = get_test_file_path('markdown', 'output_4_1.png')
    with open(fn, 'rb') as f:
        img = f.read()
    resources = {op.basename(fn): img}
    # Convert the AST to a notebook.
    nb = NotebookWriter().write(ast, resources=resources)

    # Compare the notebooks.
    nb_expected = open_notebook(get_test_file_path('notebook',
                                                   'notebook.ipynb'))
    # Ignore some fields when comparing the notebooks.
    assert_equal(nb, nb_expected, ('metadata', 'kernelspec'))
