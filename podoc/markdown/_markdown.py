# -*- coding: utf-8 -*-

"""Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from CommonMark import Parser
from six import string_types

# from podoc.utils import Bunch
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
        'Softbreak': 'LineBreak',
        'Item': 'ListItem',
    }

    def transform_root(self, cm):
        # TODO: should be def transform() for consistency with the other way
        children = [self.transform(block) for block in _iter_child(cm)]
        return ASTNode('root', children=children)

    def transform(self, obj):
        if isinstance(obj, string_types):
            return obj
        # obj is a CommonMark.Node instance.
        name = obj.t
        # Convert from CommonMark name to Pandoc
        name = self._name_mapping.get(name, name)
        # The transform_* functions take the 'c' attribute and the newly-
        # created node, and return the list of children objects to process.
        if name == 'List':
            # Special treatment for lists. In CommonMark, there is a single
            # node type, List, and the type (Bullet or Ordered) is found
            # in list_data['type']
            func = (self.transform_BulletList
                    if obj.list_data['type'] == 'Bullet'
                    else self.transform_OrderedList)
        else:
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

    def transform_BulletList(self, obj, node):
        node.bullet_char = obj.list_data['bullet_char']
        return list(_iter_child(obj))

    def transform_OrderedList(self, obj, node):
        node.start = obj.list_data['start']
        node.delimiter = obj.list_data['delimiter']
        return list(_iter_child(obj))


#------------------------------------------------------------------------------
# Markdown renderer
#------------------------------------------------------------------------------

class ASTToMarkdown(object):
    """Read an AST and render a Markdown string."""

    def __init__(self):
        self.transformer = TreeTransformer()
        self.writer = MarkdownWriter()
        # Nested lists.
        self._lists = []
        for m in dir(self):
            if m.startswith('transform_'):
                self.transformer.register(getattr(self, m))

    def transform(self, ast):
        return self.transformer.transform(ast)

    def transform_str(self, text):
        return text

    def transform_Node(self, node, inner_contents):
        return inner_contents

    def transform_Plain(self, node, inner_contents):
        return self.writer.text(inner_contents)

    def transform_Para(self, node, inner_contents):
        return self.transform_Plain(node, inner_contents)

    def transform_Space(self, node, inner_contents):
        return self.writer._write(' ')

    def transform_Header(self, node, inner_contents):
        return self.writer.heading(inner_contents, level=node.level)

    def transform_CodeBlock(self, node, inner_contents):
        return self.writer.code(inner_contents, lang=node.lang)

    def transform_BlockQuote(self, node, inner_contents):
        return self.writer.quote(inner_contents)

    # def _push_list(self, **kwargs):
    #     data = Bunch(kwargs)
    #     # Determine the level of the list: the number of nested lists.
    #     data.level = len(self._lists)
    #     if data.type == 'ordered':
    #         data.number = data.start
    #     self._lists.append(data)
    #     l = self._lists[-1]
    #     if l.type == 'bullet':
    #         bullet_char = node.bullet_char
    #     else:
    #         bullet_char = str(node.number)
    #         node.number += 1
    #     return self.writer.list_item(inner_contents,
    #                                  bullet=bullet_char,
    #                                  level=node.level,
    #                                  suffix=node.delimiter,
    #                                  )

    # def transform_BulletList(self, node, inner_contents):
    #     self._write_list(type='bullet',
    #                      bullet=node.bullet_char,
    #                      delimiter=node.delimiter,
    #                      )

    # def transform_OrderedList(self, node, inner_contents):
    #     self._write_list(type='ordered',
    #                      start=node.start,
    #                      delimiter=node.delimiter,
    #                      contents
    #                      )

    # def transform_ListItem(self, node, inner_contents):
    #     return inner_contents

    def transform_Emph(self, node, inner_contents):
        return self.writer.emph(inner_contents)

    def transform_Strong(self, node, inner_contents):
        return self.writer.strong(inner_contents)

    def transform_Code(self, node, inner_contents):
        return self.writer.inline_code(inner_contents)

    def transform_LineBreak(self, node, inner_contents):
        return self.writer.linebreak()

    def transform_Link(self, node, inner_contents):
        return self.writer.link(inner_contents, node.url)

    def transform_Image(self, node, inner_contents):
        return self.writer.image(inner_contents, node.url)


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
