# -*- coding: utf-8 -*-

"""Markup AST."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from itertools import chain
import json
import logging
import os.path as op
import re

from six import string_types

from podoc.tree import Node, TreeTransformer
from podoc.plugin import IPlugin
from podoc.utils import (has_pandoc, pandoc, get_pandoc_formats,
                         PANDOC_API_VERSION,
                         _save_resources, _get_resources_path,
                         _merge_str, _get_file, assert_equal,
                         )

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# AST
#------------------------------------------------------------------------------

# TODO: ensure there are no Spaces or Str in the AST (exclude list)

# List of allowed block names.
BLOCK_NAMES = (
    # The following are pandoc block names:
    'Plain',
    'Para',
    'Header',
    'CodeBlock',
    'BlockQuote',
    'BulletList',
    'OrderedList',

    # Special podoc names:
    'MathBlock',

    # The following pandoc block names are not supported yet in podoc:
    # 'RawBlock',
    # 'DefinitionList',
    # 'HorizontalRule',
    # 'Table',
    # 'Div',
)


DEFAULT_BULLET_SYMBOL = '*'


# List of allowed inline names.
INLINE_NAMES = (
    # The following are pandoc inline names:
    'Emph',
    'Strong',
    'Code',
    'Link',
    'Image',
    'LineBreak',
    'Math',

    # The following are not supported yet in podoc:
    # 'Strikeout',

    # The following are forbidden in podoc:
    # 'Str',
    # 'Space',
)


NATIVE_NAMES = BLOCK_NAMES + INLINE_NAMES + (
    'root',
    'ListItem',
    'Strikeout',
    'RawBlock',
    'DefinitionList',
    'HorizontalRule',
    'Table',
    'Div',
)


class ASTNode(Node):
    def is_block(self):
        return self.name in BLOCK_NAMES

    def is_inline(self):
        return self.name in INLINE_NAMES

    def is_native(self):
        """Return whether the node type is one of the native AST types"""
        return self.name in NATIVE_NAMES

    def validate(self):
        """Check that the tree is valid."""
        # Excluded list.
        assert self.name not in ('Str', 'String', 'Space', 'str')
        if self.is_inline():
            # The children of an Inline node cannot be blocks.
            for child in self.children:
                if hasattr(child, 'is_block'):
                    assert not child.is_block()  # pragma: no cover

    def to_pandoc(self):
        return PodocToPandoc().transform_main(self)

    def display(self):
        """Print-friendly representation of a node, used in tree show()."""
        if self.name == 'Header':
            return '{} {}'.format(self.name, self.level)
        elif hasattr(self, 'url'):
            return '{} <{}>'.format(self.name, self.url)
        elif self.name == 'OrderedList':
            return '{} ({})'.format(self.name, self.start)
        elif self.name == 'CodeBlock':
            return '{} {}'.format(self.name, self.lang)
        elif self.name == 'BulletList':
            return '{} ({})'.format(self.name, self.bullet_char)
        return self.name

    def __repr__(self):
        """Display the pandoc JSON representation of the tree."""
        return self.display()


#------------------------------------------------------------------------------
# AST -> pandoc
#------------------------------------------------------------------------------

def _node_dict(node, children=None):
        return {'t': node.name,
                'c': children or []}


def _split_spaces(text):
    """Split a string by spaces."""
    tokens = re.split(r'[^\S\n]+', text)
    n = len(tokens)
    spaces = [''] * n
    tokens = list(chain.from_iterable(zip(tokens, spaces)))[:-1]
    # Remove consecutive ''.
    out = []
    for el in tokens:
        if out and not el and not out[-1]:
            continue
        out.append(el)
    return out


class PodocToPandocPreProcessor(TreeTransformer):
    def transform_Node(self, node):
        """Call the transformation methods recursively."""
        children = self.transform_children(node)
        node.children = children
        return node


class PodocToPandoc(TreeTransformer):
    def transform_Node(self, node):
        if node.is_native():
            return _node_dict(node,
                              self.transform_children(node))
        else:
            # Skip the current unknown node and use the list of children
            # instead.
            # logger.debug("Unknown node `%s`.", node)
            return self.transform_children(node)

    def transform_str(self, text):
        """Split on spaces and insert Space elements for pandoc."""
        tokens = _split_spaces(text)
        return [{'t': 'Str', 'c': s} if s else {'t': 'Space'}
                for s in tokens]

    def transform_LineBreak(self, node):
        return {'t': 'LineBreak'}

    def transform_Header(self, node):
        children = [node.level, ['', [], []],
                    self.transform_children(node)]
        return _node_dict(node, children)

    def transform_MathBlock(self, node):
        contents = node.children[0]
        return {'t': 'Math', 'c': [{'t': 'DisplayMath'}, contents]}

    def transform_CodeBlock(self, node):
        # NOTE: node.children contains a single element, which is the code.
        code = node.children[0]
        children = [['', [node.lang], []], code]
        return _node_dict(node, children)

    def transform_OrderedList(self, node):
        # NOTE: we remove the ListItem node for pandoc
        items = [_['c'] for _ in self.transform_children(node)]
        # NOTE: we only support OneParen and Period delimiter for now,
        # following the CommonMark spec.
        style = node.get('style', 'Decimal')
        delimiter = node.get('delimiter', ')')
        children = [[node.start,
                    {"t": style},
                    {"t": 'OneParen' if delimiter == ')' else 'Period'}], items]
        return _node_dict(node, children)

    def transform_BulletList(self, node):
        # NOTE: we remove the ListItem node for pandoc
        items = [_['c'] for _ in self.transform_children(node)]
        return _node_dict(node, items)

    def transform_Link(self, node):
        children = [['', [], []],
                    self.transform_children(node),
                    [node.url, '']]
        return _node_dict(node, children)

    def transform_Image(self, node):
        children = [['', [], []],
                    self.transform_children(node),
                    [node.url, '']]
        return _node_dict(node, children)

    def transform_Code(self, node):
        # NOTE: node.children contains a single element, which is the code.
        children = [['', [], []], node.children[0]]
        return _node_dict(node, children)

    def transform_Math(self, node):
        contents = node.children[0]
        return {'t': 'Math', 'c': [{'t': 'InlineMath'}, contents]}

    def transform_main(self, ast):
        ast = PodocToPandocPreProcessor().transform(ast)
        blocks = self.transform(ast)['c']
        # Save podoc metadata in the pandoc JSON.
        m = ast.get('metadata', {})
        # NOTE: do not save resources in the JSON.
        m = {k: v for k, v in m.items() if v and k != 'resources'}
        if m:
            meta = {
                'podoc': {
                    't': 'MetaMap',
                    'c': {
                        key: {
                            't': 'MetaInlines',
                            'c': [{'t': 'Str', 'c': value or []}],
                        } for key, value in m.items()
                    }
                }
            }
        else:
            meta = {}
        return {'meta': meta, 'blocks': blocks,
                'pandoc-api-version': PANDOC_API_VERSION}


#------------------------------------------------------------------------------
# pandoc -> AST
#------------------------------------------------------------------------------

def ast_from_pandoc(d, **kwargs):
    return PandocToPodoc(**kwargs).transform_main(d)


class PandocToPodocPostProcessor(TreeTransformer):
    def transform_Node(self, node):
        """Call the transformation methods recursively."""
        children = self.transform_children(node)
        node.children = children
        return node


class PandocToPodoc(TreeTransformer):
    def __init__(self, bullet_char=None):
        super(TreeTransformer, self).__init__()
        self.bullet_char = bullet_char or DEFAULT_BULLET_SYMBOL

    def get_node_name(self, node):
        return node['t']

    def get_node_children(self, node):
        return node.get('c', None)

    def set_next_child(self, child, next_child):
        pass

    def transform(self, d):
        if isinstance(d, string_types):
            return d
        c = self.get_node_children(d)
        node = ASTNode(self.get_node_name(d))
        children = self.get_transform_func(d)(c, node)
        if isinstance(children, string_types):
            return children
        children = children or []
        assert isinstance(children, list)
        # Recursively transform all children and assign them to the node.
        node.children = [self.transform(child) for child in children]
        # Merge consecutive strings in the list of children.
        node.children = _merge_str(node.children)
        return node

    def transform_Node(self, c, node):
        # By default, obj['c'] is the list of children to process.
        return c

    def transform_Space(self, c, node):
        """Replace Space elements by space Strings."""
        return ' '

    def transform_Header(self, c, node):
        node.level, _, children = c
        return children

    def transform_CodeBlock(self, c, node):
        d = c[0][1]
        node.lang = d[0] if d else ''
        # NOTE: code has one child: a string with the code.
        code = c[1]
        return [code]

    def transform_OrderedList(self, c, node):
        (node.start, style, delimiter), children = c
        # NOTE: CommonMark doesn't support bullet styles
        node.style = style['t']
        # NOTE: we only support OneParen and Period for now, following
        # the CommonMark spec.
        node.delimiter = ')' if delimiter['t'] == 'OneParen' else '.'
        # NOTE: create a ListItem node that contains the elements under
        # the list item.
        children = [{'t': 'ListItem', 'c': child} for child in children]
        return children

    def transform_BulletList(self, c, node):
        # NOTE: pandoc doesn't appear to support bullet styles
        node.bullet_char = self.bullet_char
        node.delimiter = ' '
        # NOTE: create a ListItem node that contains the elements under
        # the list item.
        children = [{'t': 'ListItem', 'c': child} for child in c]
        return children

    def transform_Math(self, c, node):
        math_type = c[0]['t']
        contents = c[1]
        if math_type == 'InlineMath':
            node.name = 'Math'
        elif math_type == 'DisplayMath':
            node.name = 'MathBlock'
        return [contents]

    def transform_Code(self, c, node):
        code = c[1]
        assert isinstance(code, string_types)
        # NOTE: code has one child: a string with the code.
        return [code]

    def transform_Image(self, c, node):
        return self.transform_Link(c, node)

    def transform_Link(self, c, node):
        node.url = c[-1][0]
        children = c[-2]
        return children

    def transform_main(self, obj):
        assert isinstance(obj, dict)
        # Check that this is really the root.
        assert 'blocks' in obj
        # Special case: the root.
        # Process the root: obj is a list, and the second item
        # is a list of blocks to process.
        children = [self.transform(block) for block in obj['blocks']]
        out = ASTNode('root', children=children)
        out = PandocToPodocPostProcessor().transform(out)
        # Load metadata.
        m = obj.get('meta', {}).get('podoc', {})
        if m:
            out['metadata'] = m
        return out


#------------------------------------------------------------------------------
# pandoc plugin
#------------------------------------------------------------------------------

class PandocPlugin(IPlugin):
    def attach(self, podoc):
        if not has_pandoc():  # pragma: no cover
            logger.debug("pandoc is not available.")
            return

        source_langs, target_langs = get_pandoc_formats()

        # From pandoc source formats to AST.
        def _make_source_func(lang):
            def conv(doc, context=None):
                """Convert a document from `lang` to the podoc AST, via
                pandoc."""
                d = pandoc(doc, 'json', format=lang)
                # Convert the
                ast = ast_from_pandoc(json.loads(d))
                return ast
            return conv

        # podoc_langs = podoc.languages
        for source in source_langs:
            # if source in podoc_langs:
            #     continue
            func = _make_source_func(source)
            podoc.register_lang(source, pandoc=True)
            podoc.register_func(source=source, target='ast', func=func)

        # From AST to pandoc target formats.
        def _make_target_func(lang):
            def conv(ast, context=None):
                """Convert a document from the podoc AST to `lang`, via
                pandoc."""
                d = json.dumps(ast.to_pandoc())
                out = pandoc(d, lang, format='json')
                return out
            return conv

        # podoc_langs = podoc.languages
        for target in target_langs:
            # if target in podoc_langs:
            #     continue
            func = _make_target_func(target)
            podoc.register_lang(target, pandoc=True)
            podoc.register_func(source='ast', target=target, func=func)


#------------------------------------------------------------------------------
# AST plugin
#------------------------------------------------------------------------------

class ASTPlugin(IPlugin):
    """The file format is JSON, same as the pandoc json format."""
    def attach(self, podoc):
        # An object in the language 'ast' is an instance of AST.
        podoc.register_lang('ast', file_ext='.json',
                            load_func=self.load, dump_func=self.dump,
                            loads_func=self.loads, dumps_func=self.dumps,
                            assert_equal_func=self.assert_equal,
                            )

    def load(self, file_or_path):
        """Load a JSON file and return an AST instance."""
        # logger.debug("Load JSON file `%s`.", path)
        with _get_file(file_or_path, 'r') as f:
            # Get the path to the JSON file.
            # path = op.realpath(f.name)
            d = json.load(f)
        assert isinstance(d, dict)
        ast = ast_from_pandoc(d)
        assert isinstance(ast, ASTNode)
        return ast

    def dump(self, ast, file_or_path):
        """Dump an AST instance to a JSON file."""
        assert isinstance(ast, ASTNode)
        d = ast.to_pandoc()
        assert isinstance(d, dict)
        # logger.debug("Save JSON file `%s`.", path)
        with _get_file(file_or_path, 'w') as f:
            path = op.realpath(f.name)
            json.dump(d, f, sort_keys=True, indent=2,
                      separators=(',', ': '))  # avoid trailing whitespaces
            # Add a new line at the end.
            f.write('\n')
        # Save the resources.
        _save_resources(ast.get('resources', {}), _get_resources_path(path))

    def loads(self, s):
        """Load a JSON string and return an AST instance."""
        d = json.loads(s)
        assert isinstance(d, dict)
        ast = ast_from_pandoc(d)
        assert isinstance(ast, ASTNode)
        return ast

    def dumps(self, ast):
        """Dump an AST instance to a JSON string."""
        assert isinstance(ast, ASTNode)
        d = ast.to_pandoc()
        assert isinstance(d, dict)
        return json.dumps(d, sort_keys=True, indent=2,
                          separators=(',', ': ')) + '\n'

    def assert_equal(self, ast0, ast1):
        return assert_equal(ast0, ast1, to_remove=('_visit_meta'))
