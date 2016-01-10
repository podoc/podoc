# -*- coding: utf-8 -*-

"""Markup AST."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from itertools import chain
import json
import logging
import re

from six import string_types

from podoc.tree import Node, TreeTransformer
from podoc.plugin import IPlugin
from podoc.utils import has_pandoc, pandoc, get_pandoc_formats

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# AST
#------------------------------------------------------------------------------

# TODO: ensure there are no Spaces or Str in the AST (exclude list)

# List of allowed Pandoc block names.
PANDOC_BLOCK_NAMES = (
    'Plain',
    'Para',
    'Header',
    'CodeBlock',
    'BlockQuote',
    'BulletList',
    'OrderedList',
    # The following are not supported yet in podoc.
    # 'RawBlock',
    # 'DefinitionList',
    # 'HorizontalRule',
    # 'Table',
    # 'Div',
)


# List of allowed Pandoc inline names.
PANDOC_INLINE_NAMES = (
    # 'Str',
    'Emph',
    'Strong',
    'Code',
    'Link',
    'Image',
    'LineBreak',
    # The following are not supported yet in podoc.
    # 'Math',
    # 'Strikeout',
    # 'Space',
)


class ASTNode(Node):
    # TODO: uncomment this: there are no Str elements in the podoc AST
    # def __init__(self, name, *args, **kwargs):
    #     super(ASTNode, self).__init__(name, *args, **kwargs)
    #     # NOTE: there is no such things as String Nodes in podoc AST:
    #     # children of a node can be non-string nodes or actual Python
    #     # strings.
    #     assert name not in ('Str', 'String', 'str')

    def is_block(self):
        return self.name in PANDOC_BLOCK_NAMES

    def is_inline(self):
        return self.name in PANDOC_INLINE_NAMES

    def validate(self):
        if self.is_inline():
            # The children of an Inline node cannot be blocks.
            for child in self.children:
                if hasattr(child, 'is_block'):
                    assert not child.is_block()  # pragma: no cover

    def to_pandoc(self):
        return PodocToPandoc().transform_main(self)


#------------------------------------------------------------------------------
# AST <-> pandoc
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


class PodocToPandoc(TreeTransformer):
    def transform_Node(self, node):
        return _node_dict(node,
                          self.transform_children(node))

    def transform_str(self, text):
        """Split on spaces and insert Space elements for pandoc."""
        tokens = _split_spaces(text)
        return [{'t': 'Str', 'c': s} if s else {'t': 'Space', 'c': []}
                for s in tokens]

    def transform_Header(self, node):
        children = [node.level, ['', [], []],
                    self.transform_children(node)]
        return _node_dict(node, children)

    def transform_CodeBlock(self, node):
        # NOTE: node.children contains a single element, which is the code.
        children = [['', [node.lang], []], node.children[0]]
        return _node_dict(node, children)

    def transform_OrderedList(self, node):
        # NOTE: we remove the ListItem node for pandoc
        items = [_['c'] for _ in self.transform_children(node)]
        children = [[node.start,
                    {"t": node.style, "c": []},
                    {"t": node.delim, "c": []}], items]
        return _node_dict(node, children)

    def transform_BulletList(self, node):
        # NOTE: we remove the ListItem node for pandoc
        items = [_['c'] for _ in self.transform_children(node)]
        return _node_dict(node, items)

    def transform_Link(self, node):
        children = [self.transform_children(node),
                    [node.url, '']]
        return _node_dict(node, children)

    def transform_Image(self, node):
        children = [self.transform_children(node),
                    [node.url, '']]
        return _node_dict(node, children)

    def transform_Code(self, node):
        # NOTE: node.children contains a single element, which is the code.
        children = [['', [], []], node.children[0]]
        return _node_dict(node, children)

    def transform_main(self, ast):
        blocks = self.transform(ast)['c']
        return [{'unMeta': {}}, blocks]


def ast_from_pandoc(d):
    return PandocToPodoc().transform_main(d)


def _merge_str(l):
    """Concatenate consecutive strings in a list of nodes."""
    out = []
    for node in l:
        if (out and isinstance(out[-1], string_types) and
                isinstance(node, string_types)):
            out[-1] += node
        else:
            out.append(node)
    return out


class PandocToPodoc(TreeTransformer):
    def get_node_name(self, node):
        return node['t']

    def get_node_children(self, node):
        return node['c']

    def set_next_child(self, child, next_child):
        pass

    def transform_main(self, obj):
        assert isinstance(obj, list)
        # Check that this is really the root.
        assert len(obj) == 2
        assert 'unMeta' in obj[0]
        # Special case: the root.
        # Process the root: obj is a list, and the second item
        # is a list of blocks to process.
        children = [self.transform(block) for block in obj[1]]
        return ASTNode('root', children=children)

    def transform(self, d):
        if isinstance(d, string_types):
            return d
        c = self.get_node_children(d)
        node = ASTNode(self.get_node_name(d))
        children = self.get_transform_func(d)(c, node)
        if isinstance(children, string_types):
            return children
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
        node.lang = c[0][1][0]
        # NOTE: code has one child: a string with the code.
        return [c[1]]

    def transform_OrderedList(self, c, node):
        (node.start, style, delim), children = c
        # NOTE: create a ListItem node that contains the elements under
        # the list item.
        children = [{'t': 'ListItem', 'c': child} for child in children]
        node.style = style['t']
        node.delim = delim['t']
        return children

    def transform_BulletList(self, c, node):
        children = c
        # NOTE: create a ListItem node that contains the elements under
        # the list item.
        children = [{'t': 'ListItem', 'c': child} for child in children]
        return children

    def transform_Code(self, c, node):
        code = c[1]
        assert isinstance(code, string_types)
        # NOTE: code has one child: a string with the code.
        return [code]

    def transform_Image(self, c, node):
        return self.transform_Link(c, node)

    def transform_Link(self, c, node):
        assert len(c) == 2
        node.url = c[1][0]
        children = c[0]
        return children


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
            def conv(doc):
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
            def conv(ast):
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
                            open_func=self.open, save_func=self.save)

    def open(self, path):
        """Open a .json file and return an AST instance."""
        logger.debug("Open JSON file `%s`.", path)
        with open(path, 'r') as f:
            d = json.load(f)
        assert isinstance(d, list)
        ast = ast_from_pandoc(d)
        assert isinstance(ast, ASTNode)
        return ast

    def save(self, path, ast):
        """Save an AST instance to a JSON file."""
        # assert isinstance(ast, AST)
        d = ast.to_pandoc()
        assert isinstance(d, list)
        logger.debug("Save JSON file `%s`.", path)
        with open(path, 'w') as f:
            json.dump(d, f, sort_keys=True, indent=2,
                      separators=(',', ': '))  # avoid trailing whitespaces
            # Add a new line at the end.
            f.write('\n')
