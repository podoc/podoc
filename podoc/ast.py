# -*- coding: utf-8 -*-

"""Markup AST."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from .utils import Bunch

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# AST
#------------------------------------------------------------------------------

class AST(Bunch):
    def __init__(self, *args, **kwargs):
        super(AST, self).__init__(*args, **kwargs)
        self.meta = {}
        self.blocks = []

    def add_metadata(self, key, value):
        self.meta[key] = value

    def add_block(self, block):
        assert isinstance(block, dict)
        self.blocks.append(block)


class Block(Bunch):
    def __init__(self, *args, **kwargs):
        super(Block, self).__init__(*args, **kwargs)
        self.name = kwargs.pop('name', 'Block')
        self.meta = kwargs.pop('meta', {})
        self.inlines = kwargs.pop('inlines', [])

    def add_metadata(self, key, value):
        self.meta[key] = value

    def add_inline(self, inline):
        assert isinstance(inline, (dict, str))
        self.inlines.append(inline)


class Inline(Bunch):
    def __init__(self, *args, **kwargs):
        super(Inline, self).__init__(*args, **kwargs)
        self.name = kwargs.pop('name', 'Inline')
        self.contents = kwargs.pop('contents', [])

    def set_contents(self, contents):
        assert isinstance(contents, (list, str))
        self.contents = contents

    def add_contents(self, contents):
        assert isinstance(contents, (dict, str))
        self.contents.append(contents)


def _inline_to_pandoc(inline):
    if isinstance(inline, str):
        return {
            't': 'Str',
            'c': inline,
        }
    else:
        return {
            't': inline.name,
            'c': [_inline_to_pandoc(i) for i in inline.contents],
        }


def _block_to_pandoc(block):
    return {
        't': block.name,
        'c': [_inline_to_pandoc(inline) for inline in block.inlines],
    }


def to_pandoc(ast):
    return [{'unMeta': ast.meta},
            [_block_to_pandoc(block) for block in ast.blocks]]
