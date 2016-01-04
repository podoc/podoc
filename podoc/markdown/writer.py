# -*- coding: utf-8 -*-

"""Markdown writer."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from contextlib import contextmanager

from six import StringIO


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
        # TODO: clean \n mess in this module
        contents = contents.rstrip('\n')
        self._output.write(contents)
        return contents

    # New line methods
    # -------------------------------------------------------------------------

    def newline(self):
        self._output.write('\n\n')
        self._list_number = 0
        return '\n\n'

    def linebreak(self):
        self._output.write('\n')
        return '\n'

    def ensure_newline(self, n):
        # TODO: remove this
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
        return self.text(('#' * level) + ' ' + text)

    def numbered_list_item(self, text='', level=0):
        if level == 0:
            self._list_number += 1
        return self.list_item(text, level=level, bullet=str(self._list_number),
                              suffix='. ')

    def list_item(self, text='', level=0, bullet='*', suffix=' '):
        assert level >= 0
        return self.text(('  ' * level) + bullet + suffix + text)

    def code_start(self, lang=None):
        if lang is None:
            lang = ''
        out = self.text('```{0}'.format(lang))
        self.ensure_newline(1)
        return out

    def code_end(self):
        self.ensure_newline(1)
        return self.text('```')

    def code(self, code, lang=None):
        out = self.code_start(lang)
        out += self._write(code)
        out += self.code_end()
        return out

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
