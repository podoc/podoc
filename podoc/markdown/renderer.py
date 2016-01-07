# -*- coding: utf-8 -*-

"""Markdown renderer."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import re

from six import StringIO


#------------------------------------------------------------------------------
# Markdown renderer
#------------------------------------------------------------------------------

class MarkdownRenderer(object):
    """A class for rendering Markdown documents."""
    def __init__(self):
        self._list_number = 0

    # New line methods
    # -------------------------------------------------------------------------

    def newline(self):
        self._list_number = 0
        return self.text('\n\n')

    def linebreak(self):
        return self.text('\n')

    # Block methods
    # -------------------------------------------------------------------------

    def heading(self, text, level=None):
        assert 1 <= level <= 6
        return self.text(('#' * level) + ' ' + text)

    def numbered_list_item(self, text='', level=0):
        if level == 0:
            self._list_number += 1
        return self.list_item(text,
                              level=level,
                              bullet=str(self._list_number),
                              suffix='. ')

    def list_item(self, text='', level=0, bullet='*', suffix=' '):
        assert level >= 0
        return self.text(('  ' * level) + bullet + suffix + text)

    def code(self, code, lang=None):
        return self.text('```{}\n{}```'.format(lang or '', code))

    def quote(self, text):
        # Add quote '>' at the beginning of each line when quote is activated.
        return self.text('\n'.join('> ' + l for l in text.splitlines()))

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
        return text
