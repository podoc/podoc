# -*- coding: utf-8 -*-

"""Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from CommonMark import Parser
from six import string_types

from podoc.plugin import IPlugin
from podoc.tree import TreeTransformer
from podoc.ast import ASTNode
from podoc.markdown.writer import MarkdownWriter

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Markdown reader (using CommonMark-py)
#------------------------------------------------------------------------------

def _iter_child(cm):
    child = cm.first_child
    while child is not None:
        yield child
        child = child.nxt


class CommonMarkToAST(object):
    _name_mapping = {
        'Paragraph': 'Para',
        'Heading': 'Header',
        'List': 'BulletList',
        'Softbreak': 'LineBreak',
    }

    def transform_root(self, cm):
        # TODO: should be def transform() for consistency with the other way
        children = [self.transform(block) for block in _iter_child(cm)]
        return ASTNode('root', children=children)

    def transform(self, obj):
        if isinstance(obj, string_types):
            return obj
        # For normal nodes, obj is a dict.
        name = obj.t
        # Convert from CommonMark name to Pandoc
        name = self._name_mapping.get(name, name)
        # The transform_* functions take the 'c' attribute and the newly-
        # created node, and return the list of children objects to process.
        func = getattr(self, 'transform_%s' % name, self.transform_Node)
        node = ASTNode(name)
        # Create the node and return the list of children that have yet
        # to be processed.
        children = func(obj, node)
        # Handle string nodes.
        if isinstance(children, string_types):
            return children
        assert isinstance(children, list)
        # Recursively transform all children and assign them to the node.
        node.children = [self.transform(child) for child in children]
        return node

    def transform_Node(self, obj, node):
        return list(_iter_child(obj))

    def transform_Code(self, obj, node):
        return [obj.literal]

    def transform_Text(self, obj, node):
        return obj.literal

    def transform_Link(self, obj, node):
        node.url = obj.destination
        return list(_iter_child(obj))

    def transform_Image(self, obj, node):
        node.url = obj.destination
        return list(_iter_child(obj))

    def transform_CodeBlock(self, obj, node):
        node.lang = obj.info
        return [obj.literal]

    def transform_BlockQuote(self, obj, node):
        return list(_iter_child(obj))

    def transform_Header(self, obj, node):
        node.level = obj.level
        return list(_iter_child(obj))


#------------------------------------------------------------------------------
# Markdown renderer
#------------------------------------------------------------------------------

class ASTToMarkdown(object):
    """Read an AST and render a Markdown string."""

    def __init__(self):
        self.transformer = TreeTransformer()
        self.writer = MarkdownWriter()
        for m in dir(self):
            if m.startswith('transform_'):
                self.transformer.register(getattr(self, m))

    def transform(self, ast):
        return self.transformer.transform(ast)

    def transform_str(self, text):
        return text

    def transform_Node(self, node):
        return node.inner_contents

    def transform_Plain(self, node):
        return self.writer.text(node.inner_contents)

    def transform_Para(self, node):
        return self.transform_Plain(node)

    def transform_Space(self, node):
        return self.writer._write(' ')

    def transform_Header(self, node):
        return self.writer.heading(node.inner_contents, level=node.level)

    def transform_CodeBlock(self, node):
        return self.writer.code(node.inner_contents, lang=node.lang)

    def transform_BlockQuote(self, node):
        return self.writer.quote(node.inner_contents)

    def transform_OrderedList(self, node):
        # TODO
        return ''

    def transform_BulletList(self, node):
        # TODO
        return ''

    def transform_Emph(self, node):
        return self.writer.emph(node.inner_contents)

    def transform_Strong(self, node):
        return self.writer.strong(node.inner_contents)

    def transform_Code(self, node):
        return self.writer.inline_code(node.inner_contents)

    def transform_LineBreak(self, node):
        return self.writer.linebreak()

    def transform_Link(self, node):
        return self.writer.link(node.inner_contents, node.url)

    def transform_Image(self, node):
        return self.writer.image(node.inner_contents, node.url)


#------------------------------------------------------------------------------
# Markdown plugin
#------------------------------------------------------------------------------

class Markdown(IPlugin):
    def attach(self, podoc):
        podoc.register_lang('markdown', file_ext='.md')
        podoc.register_func(source='markdown', target='ast',
                            func=self.read_markdown)
        podoc.register_func(source='ast', target='markdown',
                            func=self.write_markdown)

    def read_markdown(self, contents):
        parser = Parser()
        cm = parser.parse(contents)
        ast = CommonMarkToAST().transform_root(cm)
        return ast

    def write_markdown(self, ast):
        return ASTToMarkdown().transform(ast)
