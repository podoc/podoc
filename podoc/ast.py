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
# Conversion to json
#------------------------------------------------------------------------------

def _inline_to_json(inline):
    if isinstance(inline, str):
        return {
            't': 'Str',
            'c': inline,
        }
    else:
        return {
            't': inline.name,
            'c': [_inline_to_json(i) for i in inline.contents],
        }


def _block_to_json(block):
    return {
        't': block.name,
        'c': [_inline_to_json(inline) for inline in block.inlines],
    }


def to_json(ast):
    """Convert a podoc AST to a json dict."""
    return [{'unMeta': ast.meta},
            [_block_to_json(block) for block in ast.blocks]]


#------------------------------------------------------------------------------
# Conversion from json
#------------------------------------------------------------------------------

def _from_json_inline(inline):
    name = inline['t']
    contents = inline['c']
    if name == 'Str':
        return contents
    else:
        return Inline(name=name,
                      contents=[_from_json_inline(i) for i in contents])


def _from_json_block(block):
    name = block['t']
    inlines = block['c']
    inlines = [_from_json_inline(i) for i in inlines]
    return Block(name=name, inlines=inlines)


def from_json(json):
    """Convert a json dict to a podoc AST."""
    assert len(json) == 2
    meta = json[0]['unMeta']
    blocks = json[1]
    blocks = [_from_json_block(b) for b in blocks]
    return AST(meta=meta, blocks=blocks)
