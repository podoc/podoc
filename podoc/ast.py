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
        self.meta = kwargs.pop('meta', {})
        self.blocks = kwargs.pop('blocks', [])

    def add_metadata(self, **kwargs):
        self.meta.update(**kwargs)

    def add_block(self, block):
        assert isinstance(block, dict)
        self.blocks.append(block)


class Block(Bunch):
    def __init__(self, *args, **kwargs):
        super(Block, self).__init__(*args, **kwargs)
        self.name = kwargs.pop('name', 'Block')
        self.meta = kwargs.pop('meta', {})
        self.inlines = kwargs.pop('inlines', [])

    def add_metadata(self, **kwargs):
        self.meta.update(**kwargs)

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


#------------------------------------------------------------------------------
# Conversion to pandoc
#------------------------------------------------------------------------------

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
    """Convert a podoc AST to a pandoc dict."""
    return [{'unMeta': ast.meta},
            [_block_to_pandoc(block) for block in ast.blocks]]


#------------------------------------------------------------------------------
# Conversion from pandoc
#------------------------------------------------------------------------------

def _from_pandoc_inline(inline):
    name = inline['t']
    contents = inline['c']
    if name == 'Str':
        return contents
    else:
        return Inline(name=name,
                      contents=[_from_pandoc_inline(i) for i in contents])


def _from_pandoc_block(block):
    name = block['t']
    inlines = block['c']
    inlines = [_from_pandoc_inline(i) for i in inlines]
    return Block(name=name, inlines=inlines)


def from_pandoc(pandoc):
    """Convert a pandoc dict to a podoc AST."""
    assert len(pandoc) == 2
    meta = pandoc[0]['unMeta']
    blocks = pandoc[1]
    blocks = [_from_pandoc_block(b) for b in blocks]
    return AST(meta=meta, blocks=blocks)
