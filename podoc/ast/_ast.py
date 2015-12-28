# -*- coding: utf-8 -*-

"""Markup AST."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging

from podoc.plugin import IPlugin
from podoc.utils import Bunch

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Utils
#------------------------------------------------------------------------------

def ae(a, b):
    if isinstance(a, (list, dict)):
        assert _remove_json_meta(a) == _remove_json_meta(b)
    else:
        assert a == b


#------------------------------------------------------------------------------
# AST
#------------------------------------------------------------------------------

class AST(Bunch):
    def __init__(self, *args, **kwargs):
        super(AST, self).__init__(*args, **kwargs)
        self.blocks = kwargs.pop('blocks', [])

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
# Conversion to JSON
#------------------------------------------------------------------------------

def _remove_json_meta(d):
    if isinstance(d, dict):
        return {k: _remove_json_meta(v) for k, v in d.items() if k != 'm'}
    elif isinstance(d, list):
        return [_remove_json_meta(v) for v in d]
    else:
        return d


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
        'm': block.meta,
    }


def to_json(ast):
    """Convert a podoc AST to a pandoc-compatible JSON dict."""
    return [{'unMeta': {}},
            [_block_to_json(block) for block in ast.blocks]]


#------------------------------------------------------------------------------
# Conversion from JSON
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
    meta = block.get('m', {})
    inlines = [_from_json_inline(i) for i in inlines]
    return Block(name=name, inlines=inlines, meta=meta)


def from_json(json):
    """Convert a JSON pandoc-compatible dict to a podoc AST."""
    assert len(json) == 2
    blocks = json[1]
    blocks = [_from_json_block(b) for b in blocks]
    return AST(blocks=blocks)


#------------------------------------------------------------------------------
# Conversion from JSON
#------------------------------------------------------------------------------

class ASTPlugin(IPlugin):
    def attach(self, podoc):
        # An object in the language 'ast' is an instance of AST.
        podoc.register_lang('ast', file_ext='.json',
                            open_func=self.open, save_func=self.save)

    def open(self, path):
        """Open a .json file and return an AST instance."""
        logger.debug("Open JSON file `%s`.", path)
        with open(path, 'r') as f:
            ast_obj = json.load(f)
        assert isinstance(ast_obj, list)
        ast = from_json(ast_obj)
        assert isinstance(ast, AST)
        return ast

    def save(self, path, ast):
        """Save an AST instance to a JSON file."""
        assert isinstance(ast, AST)
        ast_obj = to_json(ast)
        assert isinstance(ast_obj, list)
        logger.debug("Save JSON file `%s`.", path)
        with open(path, 'w') as f:
            json.dump(ast_obj, f, sort_keys=True, indent=2)
            # Add a new line at the end.
            f.write('\n')
