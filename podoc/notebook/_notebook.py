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


#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

import base64
import logging
from mimetypes import guess_extension, guess_type
import os.path as op
import re
import sys

import nbformat
from nbformat.v4 import (new_notebook,
                         new_markdown_cell,
                         new_code_cell,
                         new_output,
                         )

from podoc.markdown import MarkdownPlugin
from podoc.ast import ASTNode  # , TreeTransformer
from podoc.plugin import IPlugin
from podoc.tree import TreeTransformer
from podoc.utils import _get_file, _get_resources_path

logger = logging.getLogger(__name__)


#-------------------------------------------------------------------------------------------------
# Extract cell outputs
#-------------------------------------------------------------------------------------------------

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

            # from IPython.utils import py3compat
            # data = py3compat.cast_bytes(data)
            if not isinstance(data, bytes):
                data = data.encode('UTF-8', 'replace')

            try:
                data = base64.decodestring(data)
            except Exception as e:
                logger.warn("Unable to decode: %s.", str(e))
                data = b''
        elif sys.platform == 'win32':  # pragma: no cover
            data = data.replace('\n', '\r\n').encode('UTF-8')
        else:  # pragma: no cover
            data = data.encode('UTF-8')

        return mime_type, data


#-------------------------------------------------------------------------------------------------
# Notebook reader
#-------------------------------------------------------------------------------------------------

_NBFORMAT_VERSION = 4


def open_notebook(path):
    with open(path, 'r') as f:
        return nbformat.read(f, _NBFORMAT_VERSION)


class NotebookReader(object):
    _NEW_CELL_DELIMITER = '@@@@@ PODOC-NEW-CELL @@@@@'

    def read(self, notebook, context=None):
        assert isinstance(notebook, nbformat.NotebookNode)
        self.resources = {}  # Dictionary {filename: data}.
        context = context or {}
        # Get the unique key for image names: basename of the output file, if it exists.
        self._unique_key = op.basename(context.get('output', None) or '')
        self._unique_key = self._unique_key or op.basename(context.get('path', None) or '')
        self._unique_key = op.splitext(self._unique_key)[0] or None
        # Create the output tree.
        self.tree = ASTNode('root')
        # Language of the notebook.
        m = notebook.metadata
        # NOTE: if no language is available in the metadata, use Python
        # by default.
        self.language = m.get('language_info', {}).get('name', 'python')

        # NOTE: for performance reasons, we parse the Markdown of all cells at once
        # to reduce the overhead of calling pandoc.
        self._markdown_tree = []
        self._read_all_markdown(notebook.cells)

        for cell_index, cell in enumerate(notebook.cells):
            getattr(self, 'read_{}'.format(cell.cell_type))(cell, cell_index)

        return self.tree

    def _read_all_markdown(self, cells):
        sources = [cell.source for cell in cells if cell.cell_type == 'markdown']
        contents = ('\n\n%s\n\n' % self._NEW_CELL_DELIMITER).join(sources)
        ast = MarkdownPlugin().read(contents)
        if not ast.children:
            logger.debug("Skipping empty node.")
            return
        curtree = ASTNode('root')
        for child in ast.children:
            curtree.children.append(child)
            # Create a new tree at every cell delimiter.
            if child.children and child.children[0] == self._NEW_CELL_DELIMITER:
                # Remove the delimiter node.
                curtree.children.pop()
                # Append the current cell tree and create the next one.
                self._markdown_tree.append(curtree)
                curtree = ASTNode('root')
        # Append the last cell tree if not empty.
        if curtree.children:
            self._markdown_tree.append(curtree)

    def read_markdown(self, cell, cell_index=None):
        if self._markdown_tree:
            cell_tree = self._markdown_tree.pop(0)
            self.tree.children.extend(cell_tree.children)
        else:
            logger.warn("Isolated read_markdown() call: slow because of pandoc call overhead.")
            ast = MarkdownPlugin().read(cell.source)
            if not ast.children:
                logger.debug("Skipping empty node.")
                return
            self.tree.children.append(ast)  # pragma: no cover

    def read_code(self, cell, cell_index=None):
        node = ASTNode('CodeCell')
        # TODO: improve this.
        node._visit_meta['is_block'] = True
        # The first child is the source.
        # NOTE: the language of the code block is the notebook's language.
        node.add_child(ASTNode('CodeBlock',
                               lang=self.language,
                               children=[cell.source.rstrip()]))
        # Then, we add one extra child per output.
        for output_index, output in enumerate(cell.get('outputs', [])):
            if output.output_type == 'stream':
                child = ASTNode('CodeBlock',
                                lang='{output:' + output.name + '}',  # stdout/stderr
                                children=[output.text.rstrip()])
            elif output.output_type == 'error':
                child = ASTNode('CodeBlock',
                                lang='{output:error}',
                                children=['\n'.join(output.traceback)])
            elif output.output_type in ('display_data', 'execute_result'):
                # Output text node.
                text = output.data.get('text/plain', 'Output')
                # Extract image output, if any.
                out = extract_output(output)
                if out is None:
                    child = ASTNode('CodeBlock',
                                    lang='{output:result}',
                                    children=[text])
                else:
                    mime_type, data = out
                    fn = output_filename(mime_type=mime_type,
                                         cell_index=cell_index,
                                         output_index=output_index,
                                         unique_key=self._unique_key,
                                         )
                    self.resources[fn] = data
                    # Wrap the Image node in a Para.
                    img_child = ASTNode('Image', url='{resource:%s}' % fn, children=[text])
                    child = ASTNode('Para', children=[img_child])
            else:  # pragma: no cover
                raise ValueError("Unknown output type `%s`." % output.output_type)
            node.add_child(child)
        self.tree.children.append(node)

    def read_raw(self, cell, cell_index=None):
        # TODO
        pass


class CodeCellWrapper(object):
    def wrap(self, ast):
        self.ast = ast.copy()
        self.ast.children = []
        self._code_cell = None
        for i, node in enumerate(ast.children):
            if self._code_cell:
                if self.is_output(node) or self.is_image(node):
                    self.add_output(node)
                else:
                    self.end_code_cell()
            if not self._code_cell:
                if self.is_source(node):
                    self.start_code_cell(node)
                else:
                    self.append(node)
        # Ensure the last cell is appended.
        self.end_code_cell()
        return self.ast

    def is_output(self, node):
        return ((node.name == 'CodeBlock') and
                (node.lang in (None, '') or node.lang.startswith('{output')))

    def is_image(self, node):
        children = node.children
        return ((node.name == 'Para') and
                (len(children) == 1) and
                (isinstance(children[0], ASTNode)) and
                (children[0].name == 'Image'))

    def is_source(self, node):
        # TODO: customizable lang
        return node.name == 'CodeBlock' and node.lang == 'python'

    def start_code_cell(self, node):
        self._code_cell = ASTNode('CodeCell')
        # Source CodeBlock.
        self._code_cell.add_child(node)

    def add_output(self, node):
        self._code_cell.add_child(node)

    def end_code_cell(self):
        if self._code_cell:
            self.append(self._code_cell)
            self._code_cell = None

    def append(self, node):
        self.ast.add_child(node)


def wrap_code_cells(ast, context=None):
    """Take an AST and wrap top-level CodeBlocks within CodeCells."""
    return CodeCellWrapper().wrap(ast)


def replace_resource_paths(ast, context=None):
    """Replace {resource:...} image paths to actual relative paths."""

    # Get the relative path of the directory with the resources.
    path = (context or {}).get('output', None)
    if not path:
        path = (context or {}).get('path', None)
    if path:
        path = op.basename(_get_resources_path(path))
    else:  # pragma: no cover
        logger.debug("No output or path given, not replacing resource paths.")
        return ast

    class ResourceTransformer(TreeTransformer):
        def transform_Image(self, node):
            url = node.url
            if url.startswith('{resource:'):
                node.url = re.sub(r'\{resource:([^\}]+)\}', r'%s/\1' % path, url)
                logger.debug("Replace %s by %s.", url, node.url)
            return node

        def transform_Node(self, node):
            node.children = self.transform_children(node)
            return node

    return ResourceTransformer().transform(ast)


def _append_newlines(s):
    return '\n'.join(s.rstrip().split('\n')) + '\n'


def _get_b64_resource(data):
    if not data:
        return ''
    """Return the base64 of a binary buffer."""
    out = base64.b64encode(data).decode('utf8')
    # NOTE: split the output in multiple lines of 76 characters,
    # to make easier the comparison with actual Jupyter Notebook files.
    N = 76
    out = '\n'.join([out[i:i + N] for i in range(0, len(out), N)]) + '\n'
    return out


class NotebookWriter(object):
    def write(self, ast, context=None):
        self.execution_count = 1
        self._md = MarkdownPlugin()
        # Add code cells in the AST.
        ast = wrap_code_cells(ast)
        # Find the directory containing the notebook file.
        doc_path = (context or {}).get('path', None)
        if doc_path:
            self._dir_path = op.dirname(op.realpath(doc_path))
        else:
            logger.warn("No input path, unable to resolve the image relative paths.")
            self._dir_path = None
        # Create the notebook.
        # new_output, new_code_cell, new_markdown_cell
        nb = new_notebook()
        # Go through all top-level blocks.
        for index, node in enumerate(ast.children):
            # Determine the block type.
            if node.name == 'CodeCell':
                node_type = 'code'
            else:
                node_type = 'markdown'
            # Create the notebook cell.
            cell = getattr(self, 'new_{}_cell'.format(node_type))(node, index)
            # Add it to the notebook.
            nb.cells.append(cell)
        nbformat.validate(nb)
        return nb

    def new_markdown_cell(self, node, index=None):
        return new_markdown_cell(self._md.write(node))

    def new_code_cell(self, node, index=None):
        # Get the code cell input: the first child of the CodeCell block.
        input_block = node.children[0]
        assert input_block.name == 'CodeBlock'
        cell = new_code_cell(input_block.children[0],
                             execution_count=self.execution_count,
                             )
        # Next we need to add the outputs: the next children in the CodeCell.
        for child in node.children[1:]:
            # Outputs can be code blocks or Markdown paragraphs containing
            # an image.
            if child.name == 'CodeBlock':
                # The output is a code block.
                # What is the output's type? It depends on the code block's
                # name. It can be: `stdout`, `stderr`, `result`.
                output_type = child.lang or '{output:result}'
                assert output_type.startswith('{output')
                contents = child.children[0]
                # NOTE: append new lines at the end of every line in stdout
                # and stderr contents, to match with the Jupyter Notebook.
                if output_type != '{output:result}':
                    contents = _append_newlines(contents)
                if output_type == '{output:result}':
                    kwargs = dict(execution_count=self.execution_count,
                                  data={'text/plain': contents})
                    # Output type to pass to nbformat.
                    output_type = 'execute_result'
                elif output_type in ('{output:stdout}', '{output:stderr}'):
                    # Standard output or error.
                    # NOTE: strip {output } and only keep stdout/stderr in name.
                    kwargs = dict(text=contents, name=output_type[8:-1])
                    # Output type to pass to nbformat.
                    output_type = 'stream'
            elif child.name == 'Para':
                img = child.children[0]
                assert img.name == 'Image'
                fn = img.url
                caption = self._md.write(img.children[0])
                output_type = 'display_data'
                data = {}  # Dictionary {mimetype: data_buffer}.
                # Infer the mime type of the file, from its filename and
                # extension.
                mime_type = guess_type(fn)[0]
                assert mime_type  # unknown extension: this shouldn't happen!
                # Get the resource data.
                if self._dir_path:
                    image_path = op.join(self._dir_path, fn)
                    if op.exists(image_path):
                        with open(image_path, 'rb') as f:
                            data[mime_type] = _get_b64_resource(f.read())
                    else:  # pragma: no cover
                        logger.debug("File `%s` doesn't exist.", image_path)
                data['text/plain'] = caption
                kwargs = dict(data=data)
            assert not output_type.startswith('{output')
            output = new_output(output_type, **kwargs)
            cell.outputs.append(output)
        self.execution_count += 1
        return cell

    def new_raw_cell(self, node, index=None):
        # TODO
        pass


class NotebookPlugin(IPlugin):
    def attach(self, podoc):
        podoc.register_lang('notebook',
                            file_ext='.ipynb',
                            load_func=self.load,
                            dump_func=self.dump,
                            loads_func=self.loads,
                            dumps_func=self.dumps,
                            eq_filter=self.eq_filter,
                            )
        podoc.register_func(source='notebook', target='ast',
                            func=self.read,
                            post_filter=replace_resource_paths,
                            )
        podoc.register_func(source='ast', target='notebook',
                            func=self.write,
                            pre_filter=wrap_code_cells,
                            )

    def load(self, file_or_path):
        with _get_file(file_or_path, 'r') as f:
            nb = nbformat.read(f, _NBFORMAT_VERSION)
        return nb

    def dump(self, nb, file_or_path):
        with _get_file(file_or_path, 'w') as f:
            nbformat.write(nb, f, _NBFORMAT_VERSION)

    def loads(self, s):
        return nbformat.reads(s, _NBFORMAT_VERSION)

    def dumps(self, nb):
        return nbformat.writes(nb, _NBFORMAT_VERSION)

    def eq_filter(self, nb):
        if not isinstance(nb, dict):
            return nb
        for k in ('metadata', 'kernel_spec'):
            if k in nb:
                nb[k] = {}
        return nb

    def read(self, nb, context=None):
        nr = NotebookReader()
        ast = nr.read(nb, context=context)
        if context:
            context.resources = nr.resources
        return ast

    def write(self, ast, context=None):
        return NotebookWriter().write(ast, context=context)
