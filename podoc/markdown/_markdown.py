# -*- coding: utf-8 -*-

"""Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from CommonMark import Parser
from six import StringIO

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

    @property
    def contents(self):
        return self._output.getvalue().rstrip() + '\n'  # end of file \n

    def close(self):
        self._output.close()

    def __del__(self):
        self.close()

    def _write(self, contents):
        self._output.write(contents.rstrip('\n'))

    # New line methods
    # -------------------------------------------------------------------------

    def newline(self):
        self._output.write('\n\n')
        self._list_number = 0

    def linebreak(self):
        self._output.write('\n')

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
        self.text('[{0}]({1})'.format(text, url))

    def image(self, caption, url):
        self.text('![{0}]({1})'.format(caption, url))

    def inline_code(self, text):
        self.text('`{0}`'.format(text))

    def italic(self, text):
        self.text('*{0}*'.format(text))

    def bold(self, text):
        self.text('**{0}**'.format(text))

    def text(self, text):
        # Add quote '>' at the beginning of each line when quote is activated.
        if self._in_quote:
            if self._output.getvalue()[-1] == '\n':
                text = '> ' + text
        self._write(text)


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
