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

import base64
import logging
from mimetypes import guess_extension
import sys

import nbformat
from nbformat import new_markdown_cell, new_code_cell, new_output

from podoc.markdown import Markdown
from podoc.ast import ASTNode  # , TreeTransformer

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Extract cell outputs
#------------------------------------------------------------------------------

_OUTPUT_FILENAME_TEMPLATE = "{unique_key}_{cell_index}_{index}{extension}"
_EXTRACT_OUTPUT_TYPES = ('image/png',
                         'image/jpeg',
                         'image/svg+xml',
                         'application/pdf')


def output_filename(mime_type=None, unique_key=None,
                    cell_index=None, output_index=None):
    ext = guess_extension(mime_type)
    ext = ".jpeg" if ext == ".jpe" else ext
    ext = '.' + mime_type.rsplit('/')[-1] if ext is None else ext
    args = dict(unique_key=unique_key or 'output',
                cell_index=cell_index or 0,
                index=output_index or 0,
                extension=ext,
                )
    return _OUTPUT_FILENAME_TEMPLATE.format(**args)


def extract_output(output):
    """Return the output mime type and data for the first found mime type.

    https://github.com/jupyter/nbconvert/blob/master/nbconvert/preprocessors/extractoutput.py

    Copyright (c) IPython Development Team.
    Distributed under the terms of the Modified BSD License.

    """
    # Get the output in data formats that the template needs extracted.
    for mime_type in _EXTRACT_OUTPUT_TYPES:
        if mime_type not in output.data:
            continue
        data = output.data[mime_type]

        # Binary files are base64-encoded, SVG is already XML.
        if mime_type in {'image/png', 'image/jpeg', 'application/pdf'}:
            # data is b64-encoded as text (str, unicode)
            # decodestring only accepts bytes

            # data = py3compat.cast_bytes(data)
            if not isinstance(data, bytes):
                data = data.encode('UTF-8', 'replace')

            data = base64.decodestring(data)
        elif sys.platform == 'win32':  # pragma: no cover
            data = data.replace('\n', '\r\n').encode('UTF-8')
        else:  # pragma: no cover
            data = data.encode('UTF-8')

        return mime_type, data


#------------------------------------------------------------------------------
# Notebook reader
#------------------------------------------------------------------------------

_NBFORMAT_VERSION = 4


def open_notebook(path):
    with open(path, 'r') as f:
        return nbformat.read(f, _NBFORMAT_VERSION)


class NotebookReader(object):
    def read(self, notebook):
        self.tree = ASTNode('root')
        self.resources = {}  # Dictionary {filename: data}.
        # Language of the notebook.
        self.language = notebook.metadata.language_info.name
        for cell_index, cell in enumerate(notebook.cells):
            getattr(self, 'read_{}'.format(cell.cell_type))(cell, cell_index)
        return self.tree

    def read_markdown(self, cell, cell_index=None):
        contents = cell.source
        ast = Markdown().read_markdown(contents)
        assert len(ast.children) == 1
        self.tree.children.append(ast.children[0])

    def read_code(self, cell, cell_index=None):
        node = ASTNode('CodeCell')
        # The first child is the source.
        node.add_child(ASTNode('CodeBlock',
                               lang=self.language,
                               children=[cell.source]))
        # Then, we add one extra child per output.
        for output_index, output in enumerate(cell.get('outputs', [])):
            if output.output_type == 'stream':
                child = ASTNode('CodeBlock', lang='output',
                                children=[output.text])
            elif output.output_type in ('display_data', 'execute_result'):
                # Output text node.
                text = output.data.get('text/plain', 'Output')
                # Extract image output, if any.
                out = extract_output(output)
                if out is None:
                    child = ASTNode('CodeBlock', lang='output',
                                    children=[text])
                else:
                    mime_type, data = out
                    fn = output_filename(mime_type=mime_type,
                                         cell_index=cell_index,
                                         output_index=output_index,
                                         unique_key=None,  # TODO
                                         )
                    self.resources[fn] = data
                    child = ASTNode('Image', url=fn, children=[text])
            node.add_child(child)
        self.tree.children.append(node)

    def read_raw(self, cell):
        # TODO
        pass


def wrap_code_cells(ast):
    """Take an AST and wrap top-level CodeBlocks within CodeCells."""
    out = ast.copy()
    out.children = []
    current_cell = None
    for i, child in enumerate(ast.children):
        # Notebook code cell.
        if child.name == 'CodeBlock' and child.lang == 'python':
            current_cell = ASTNode('CodeCell')
            # TODO: parameterizable language
            # Wrap CodeBlocks within CodeCells.
            current_cell.add_child(child)
        else:
            # Decide whether we're part of the current cell.
            name = child.name
            children = child.children
            # Case 1: we're a code block with `output` language.
            is_output = ((name == 'CodeBlock') and
                         (child.lang in (None, '', 'output')))
            # Case 2: we're just an image.
            is_image = ((name == 'Para') and
                        (len(children) == 1) and
                        (isinstance(children[0], ASTNode)) and
                        (children[0].name == 'Image'))
            if current_cell:
                if is_output or is_image:
                    # Add the current block to the cell's outputs.
                    current_cell.add_child(child)
                else:
                    # We're no longer part of the current cell.
                    # First, we add the cell that has just finished.
                    out.add_child(current_cell)
                    # Then, we add the current block.
                    out.add_child(child)
                    current_cell = None
            else:
                out.add_child(child)
    # Add the last current cell (if it had no output).
    if current_cell:
        out.add_child(current_cell)
    return out


class NotebookWriter(object):
    def write(self, ast):
        # Add code cells in the AST.
        ast = wrap_code_cells(ast)
        # Create the notebook.
        # new_output, new_code_cell, new_markdown_cell
        nb = nbformat.new_notebook()
        # Go through all top-level blocks.
        for index, node in enumerate(ast.children):
            # Determine the block type.
            if node.name == 'CodeBlock':
                node_type = 'code'
            else:
                node_type = 'markdown'
            # Create the notebook cell.
            cell = getattr(self, 'new_{}_cell'.format(node_type))(node, index)
            # Add it to the notebook.
            nb.cells.append(cell)
        return nb

    def new_markdown_cell(self, node, index=None):
        return new_markdown_cell(node.children[0])

    def new_code_cell(self, node, index=None):
        # Get the code cell input: the first child of the CodeCell block.
        input_block = node.children[0]
        assert input_block.name == 'CodeBlock'
        cell = new_code_cell(input_block.children[0])
        # Next we need to add the output: the next children in the CodeCell.
        for child in node.children[1:]:
            # TODO: determine the output type and data from the AST node.
            output = new_output(output_type, data=None)
            cell.outputs.append(output)
        return cell

    def new_raw_cell(self, node, index=None):
        # TODO
        pass
