# -*- coding: utf-8 -*-

"""Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os.path as op

import pypandoc
from six import string_types

from podoc.ast import ASTNode, ASTPlugin
from podoc.markdown.renderer import MarkdownRenderer
from podoc.plugin import IPlugin
from podoc.tree import TreeTransformer
from podoc.utils import PANDOC_MARKDOWN_FORMAT

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Markdown renderer
#------------------------------------------------------------------------------

class ASTToMarkdown(TreeTransformer):
    """Read an AST and render a Markdown string."""

    def __init__(self):
        self.renderer = MarkdownRenderer()
        # Nested lists.
        self._lists = []

    def get_inner_contents(self, node):
        delim = ''
        # What is the delimiter between children? If the children are
        # blocks, we should insert a new line between consecutive blocks.
        # Otherwise we just concatenate the children.
        if node.children:
            child = node.children[0]
            # TODO: improve this.
            if (isinstance(child, ASTNode) and
                (child.is_block() or
                 child.get('_visit_meta', {}).get('is_block', None))):
                delim = '\n\n'
        return delim.join(self.transform_children(node))

    def transform_str(self, text):
        return text

    def transform_Node(self, node):
        return self.get_inner_contents(node)

    # Block nodes
    # -------------------------------------------------------------------------

    def transform_Plain(self, node):
        return self.renderer.text(self.get_inner_contents(node))

    def transform_Para(self, node):
        return self.transform_Plain(node)

    def transform_Header(self, node):
        return self.renderer.heading(self.get_inner_contents(node),
                                     level=node.level)

    def transform_CodeBlock(self, node):
        return self.renderer.code(self.get_inner_contents(node),
                                  lang=node.lang)

    def transform_BlockQuote(self, node):
        return self.renderer.quote(self.get_inner_contents(node))

    def transform_MathBlock(self, node):
        return self.renderer.math_block(self.get_inner_contents(node))

    def _write_list(self, node, list_type):
        assert list_type in ('bullet', 'ordered')
        if list_type == 'bullet':
            bullet = node.bullet_char
            suffix = node.delimiter
        elif list_type == 'ordered':
            bullet = node.start
            # NOTE: CommonMark doesn't appear to support non-decimal bullets
            # node.style is not used
            suffix = ')' if node.delimiter == 'OneParen' else '.'
            if not suffix.endswith(' '):
                suffix += ' '
        # This is a list of processed items.
        items = self.transform_children(node)
        out = []
        for item in items:
            # We indent all lines in the item.
            item_lines = item.splitlines()
            item = '\n'.join((('  ' if i else '') + line)
                             for i, line in enumerate(item_lines))
            # We add the bullet and suffix to the first line in the item.
            out.append(str(bullet) + suffix + item)
            # We increase the current ordered list number.
            if list_type == 'ordered':
                bullet += 1
        return '\n'.join(out)

    def transform_BulletList(self, node):
        return self._write_list(node, 'bullet')

    def transform_OrderedList(self, node):
        return self._write_list(node, 'ordered')

    def transform_ListItem(self, node):
        out = self.get_inner_contents(node)
        return out

    # Inline nodes
    # -------------------------------------------------------------------------

    def transform_Emph(self, node):
        return self.renderer.emph(self.get_inner_contents(node))

    def transform_Strong(self, node):
        return self.renderer.strong(self.get_inner_contents(node))

    def transform_Code(self, node):
        return self.renderer.inline_code(
            self.get_inner_contents(node))

    def transform_LineBreak(self, node):
        return self.renderer.linebreak()

    def transform_Math(self, node):
        return self.renderer.math(self.get_inner_contents(node))

    def transform_Link(self, node):
        return self.renderer.link(self.get_inner_contents(node),
                                  node.url)

    def transform_Image(self, node):
        return self.renderer.image(self.get_inner_contents(node),
                                   node.url)


#------------------------------------------------------------------------------
# Markdown plugin
#------------------------------------------------------------------------------

def _save_resources(resources, res_path=None):
    if not res_path:
        logger.debug("No resource path given.")
        return
    for fn, data in resources.items():
        path = op.join(res_path, fn)
        with open(path, 'wb') as f:
            logger.debug("Writing %d bytes to `%s`.", len(data), path)
            f.write(data)


def _load_resources(ast, res_path=None):
    if res_path is None:
        logger.debug("No resource path given.")
        return
    resources = {}

    class MyTreeTransformer(TreeTransformer):
        def transform_Node(self, node):
            node.children = self.transform_children(node)
            return node

        def transform_Image(self, node):
            # TODO: check this is a relative path.
            path = op.join(res_path, node.path)
            fn = op.basename(node.path)
            with open(path, 'rb') as f:
                data = f.read()
            logger.debug("Read %d bytes from `%s`.", len(data), path)
            resources[fn] = data
            return node

    return resources


class MarkdownPlugin(IPlugin):
    def attach(self, podoc):
        podoc.register_lang('markdown', file_ext='.md')
        podoc.register_func(source='markdown', target='ast',
                            func=self.read)
        podoc.register_func(source='ast', target='markdown',
                            func=self.write)

    def read(self, contents):
        assert isinstance(contents, string_types)
        js = pypandoc.convert_text(contents, 'json', format=PANDOC_MARKDOWN_FORMAT)
        ast = ASTPlugin().loads(js)
        ast.resources = _load_resources(ast, ast.resources_path)
        return ast

    def write(self, ast):
        assert isinstance(ast, (ASTNode, string_types))
        if isinstance(ast, ASTNode):
            _save_resources(ast.resources, ast.resources_path)
        return ASTToMarkdown().transform(ast)
