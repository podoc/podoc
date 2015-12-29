# -*- coding: utf-8 -*-

"""Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from CommonMark import Parser

from podoc.ast import AST, Block, Inline
from podoc.plugin import IPlugin

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Markdown to AST
#------------------------------------------------------------------------------

def _from_cm_inline(inline):
    name = inline.t
    contents = inline.c
    if name == 'Str':
        return contents
    else:
        return Inline(name=name,
                      contents=[_from_cm_inline(i) for i in contents])


def _from_cm_block(block):
    name = block.t
    # TODO: what to do with block.c?
    inlines = block.inline_content
    # TODO: support for meta in CommonMark?
    inlines = [_from_cm_inline(i) for i in inlines]
    return Block(name=name, inlines=inlines)


def from_cm(cm):
    """Convert a CommonMark AST to a podoc AST."""
    blocks = cm.children
    blocks = [_from_cm_block(b) for b in blocks]
    return AST(blocks=blocks)


#------------------------------------------------------------------------------
# AST to Markdown
#------------------------------------------------------------------------------

def _inline_to_cm(inline):
    if isinstance(inline, str):
        return {
            't': 'Str',
            'c': inline,
        }
    else:
        return {
            't': inline.name,
            'c': [_inline_to_cm(i) for i in inline.contents],
        }


def _block_to_cm(block):
    return {
        't': block.name,
        'c': [_inline_to_cm(inline) for inline in block.inlines],
        'm': block.meta,
    }


def to_cm(ast):
    """Convert a podoc AST to a CommonMark AST."""
    # TODO: create CommonMark AST
    return [_block_to_cm(block) for block in ast.blocks]


#------------------------------------------------------------------------------
# Markdown plugin
#------------------------------------------------------------------------------

class Markdown(IPlugin):
    def attach(self, podoc):
        podoc.register_lang('markdown', file_ext='.md')

    def read_markdown(self, contents):
        parser = Parser()
        cm = parser.parse(contents)
        ast = from_cm(cm)
        return ast
