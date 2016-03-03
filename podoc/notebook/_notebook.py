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

from podoc.markdown import Markdown
from podoc.ast import ASTNode  # , TreeTransformer

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Extract cell outputs
#------------------------------------------------------------------------------

_OUTPUT_FILENAME_TEMPLATE = "{unique_key}_{cell_index}_{index}{extension}"
_EXTRACT_OUTPUT_TYPES = {'image/png',
                         'image/jpeg',
                         'image/svg+xml',
                         'application/pdf'}


def extract_outputs(outputs, cell_index=None, unique_key=None):
    """Yield (filename, data).

    https://github.com/jupyter/nbconvert/blob/master/nbconvert/preprocessors/extractoutput.py

    Copyright (c) IPython Development Team.
    Distributed under the terms of the Modified BSD License.

    """
    for index, out in enumerate(outputs):
        if out.output_type not in {'display_data', 'execute_result'}:
            continue

        # Get the output in data formats that the template needs extracted.
        for mime_type in _EXTRACT_OUTPUT_TYPES:
            if mime_type not in out.data:
                continue
            data = out.data[mime_type]

            # Binary files are base64-encoded, SVG is already XML.
            if mime_type in {'image/png', 'image/jpeg', 'application/pdf'}:
                # data is b64-encoded as text (str, unicode)
                # decodestring only accepts bytes

                # data = py3compat.cast_bytes(data)
                if not isinstance(data, bytes):
                    data = data.encode('UTF-8', 'replace')

                data = base64.decodestring(data)
            elif sys.platform == 'win32':
                data = data.replace('\n', '\r\n').encode('UTF-8')
            else:
                data = data.encode('UTF-8')

            ext = guess_extension(mime_type)
            if ext == ".jpe":
                ext = ".jpeg"
            if ext is None:
                ext = '.' + mime_type.rsplit('/')[-1]

            args = dict(unique_key=unique_key or 'output',
                        cell_index=cell_index or 0,
                        index=index,
                        extension=ext,
                        )
            filename = _OUTPUT_FILENAME_TEMPLATE.format(**args)

            yield filename, data


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
        # Language of the notebook.
        self.language = notebook.metadata.language_info.name
        for cell in notebook.cells:
            getattr(self, 'read_{}'.format(cell.cell_type))(cell)
        return self.tree

    def read_markdown(self, cell):
        contents = cell.source
        ast = Markdown().read_markdown(contents)
        assert len(ast.children) == 1
        self.tree.children.append(ast.children[0])

    def read_code(self, cell):
        node = ASTNode('CodeCell')
        # The first child is the source.
        node.add_child(ASTNode('CodeBlock',
                               lang=self.language,
                               children=[cell.source]))
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
                    child = ASTNode('Image', children=[text])
                else:
                    child = text
            node.add_child(ASTNode('CodeBlock',
                                   lang='output',
                                   children=[child]))
        self.tree.children.append(node)

    def read_raw(self, cell):
        # TODO
        pass
