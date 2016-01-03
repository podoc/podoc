# -*- coding: utf-8 -*-

"""Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from contextlib import contextmanager
import logging

from CommonMark import Parser
from six import StringIO, string_types

# from podoc.ast import AST, Block, Inline
from podoc.plugin import IPlugin

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Markdown to AST through CommonMark-py
#------------------------------------------------------------------------------

_COMMONMARK_PANDOC_MAPPING = {
    'Paragraph': 'Para',
    'ATXHeader': 'Header',
    'FencedCode': 'CodeBlock',
    'List': 'OrderedList',
    'Softbreak': 'LineBreak',
}


def _from_cm_inline(inline):
    name = inline.t
    children = inline.c
    if isinstance(children, list):
        children = [_from_cm_inline(_) for _ in children]
    if name in ('Link', 'Image'):
        url = inline.destination
        children = [_from_cm_inline(_) for _ in inline.label]
        return Inline(name=name, children=children, url=url)
    else:
        return Inline(name=name, children=children)


def _from_cm_block(block):
    name = block.t
    # Find children.
    children = block.inline_content
    children = [_from_cm_inline(i) for i in children]
    # Optionally convert the CommonMark-py name to the Pandoc name.
    name = _COMMONMARK_PANDOC_MAPPING.get(name, name)
    if name == 'CodeBlock':
        lang = block.info
        children = [block.string_content]
        return Block(name=name, children=children, lang=lang)
    elif name == 'Header':
        level = block.level
        return Block(name=name, children=children, level=level)
    return Block(name=name, children=children)


def from_cm(cm):
    """Convert a CommonMark AST to a podoc AST."""
    blocks = cm.children
    blocks = [_from_cm_block(b) for b in blocks]
    return AST(blocks=blocks)


#------------------------------------------------------------------------------
# Markdown writer
#------------------------------------------------------------------------------

class MarkdownWriter(object):
    """A class for writing Markdown documents."""
    def __init__(self):
        self._output = StringIO()
        self._list_number = 0
        self._in_quote = False

    # Buffer methods
    # -------------------------------------------------------------------------

    @contextmanager
    def capture(self):
        """Temporarily capture all written contents."""
        output = self._output
        self._output = StringIO()
        yield
        self._output.close()
        del self._output
        self._output = output

    @property
    def contents(self):
        return self._output.getvalue().rstrip() + '\n'  # end of file \n

    def close(self):
        self._output.close()

    def __del__(self):
        self.close()

    def _write(self, contents):
        contents = contents.rstrip('\n')
        self._output.write(contents)
        return contents

    # New line methods
    # -------------------------------------------------------------------------

    def newline(self):
        self._output.write('\n\n')
        self._list_number = 0

    def linebreak(self):
        self._output.write('\n')
        return '\n'

    def ensure_newline(self, n):
        """Make sure there are 'n' line breaks at the end."""
        assert n >= 0
        text = self._output.getvalue().rstrip('\n')
        if not text:
            return
        self._output = StringIO()
        self._output.write(text)
        self._output.write('\n' * n)
        text = self._output.getvalue()
        assert text[-n - 1] != '\n'
        assert text[-n:] == '\n' * n

    # Block methods
    # -------------------------------------------------------------------------

    def heading(self, text, level=None):
        assert 1 <= level <= 6
        self.ensure_newline(2)
        self.text(('#' * level) + ' ' + text)

    def numbered_list_item(self, text='', level=0):
        if level == 0:
            self._list_number += 1
        self.list_item(text, level=level, bullet=str(self._list_number),
                       suffix='. ')

    def list_item(self, text='', level=0, bullet='*', suffix=' '):
        assert level >= 0
        self.text(('  ' * level) + bullet + suffix + text)

    def code_start(self, lang=None):
        if lang is None:
            lang = ''
        self.text('```{0}'.format(lang))
        self.ensure_newline(1)

    def code_end(self):
        self.ensure_newline(1)
        self.text('```')

    def quote_start(self):
        self._in_quote = True

    def quote_end(self):
        self._in_quote = False

    # Inline methods
    # -------------------------------------------------------------------------

    def link(self, text, url):
        return self.text('[{0}]({1})'.format(text, url))

    def image(self, caption, url):
        return self.text('![{0}]({1})'.format(caption, url))

    def inline_code(self, text):
        return self.text('`{0}`'.format(text))

    def emph(self, text):
        return self.text('*{0}*'.format(text))

    def strong(self, text):
        return self.text('**{0}**'.format(text))

    def text(self, text):
        # Add quote '>' at the beginning of each line when quote is activated.
        if self._in_quote:
            s = self._output.getvalue()
            if not s or s[-1] == '\n':
                text = '> ' + text
        return self._write(text)

    # def strikeout(self, text):
    #     return self.text('~~{0}~'.format(text))


class MarkdownRenderer(MarkdownWriter):
    """Read an AST and render a Markdown string."""
    def render_block(self, block):
        """Render a block and write it."""
        n = block.name
        # Ensure that we don't write the children to the document yet.
        with self.capture():
            contents = self.render_inline(block.children)
        # Write the block with the already-rendered inline contents.
        if n in ('Plain', 'Para'):
            self.text(contents)
        elif n == 'Header':
            self.heading(contents, level=block.level)
        elif n == 'CodeBlock':
            self.code_start(block.lang)
            self.text(contents)
            self.code_end()
        elif n == 'BlockQuote':
            self.quote_start()
            self.text(contents)
            self.quote_end()
        elif n == 'OrderedList':
            # TODO
            pass
        elif n == 'BulletList':
            pass
        self.newline()

    def render_inline(self, inline):
        """Return the Markdown of an inline (without writing anything to
        the Markdown document)."""
        if isinstance(inline, list):
            return ''.join(map(self.render_inline, inline))
        if isinstance(inline, string_types):
            return inline
        assert isinstance(inline, dict)
        # Recursive inline contents.
        contents = ''.join(map(self.render_inline, inline.children))
        n = inline.name
        if n == 'Emph':
            return self.emph(contents)
        elif n == 'Strong':
            return self.strong(contents)
        elif n == 'Code':
            return self.inline_code(contents)
        elif n == 'Link':
            return self.link(contents, inline.url)
        elif n == 'Image':
            return self.image(contents, inline.url)
        if n == 'Str':
            return contents
        # elif n == 'Strikeout':
        #     return self.strikout(contents)
        # elif n == 'Space':
        #     return self.text(' ')
        # elif n == 'LineBreak':
        #     return self.linebreak()
        raise ValueError()  # pragma: no cover

    def render(self, ast):
        for block in ast.blocks:
            self.render_block(block)
        return self.contents


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
        ast = from_cm(cm)
        return ast

    def write_markdown(self, ast):
        # w = MarkdownWriter()
        # TODO
        pass
