# -*- coding: utf-8 -*-

"""Markdown writer."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

# from contextlib import contextmanager

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

    @property
    def contents(self):
        return self._output.getvalue()

    def close(self):
        self._output.close()

    def __del__(self):
        self.close()

    def _write(self, contents):
        self._output.write(contents)
        return contents

    # New line methods
    # -------------------------------------------------------------------------

    def newline(self):
        self._list_number = 0
        return self._write('\n\n')

    def linebreak(self):
        return self._write('\n')

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
        return self.text('```{}\n{}\n```'.format(lang or '', code))

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
