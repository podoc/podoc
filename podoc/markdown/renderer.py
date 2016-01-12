# -*- coding: utf-8 -*-

"""Markdown renderer."""


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
        assert level >= 1
        return self.text(('#' * level) + ' ' + text)

    def code(self, code, lang=None):
        return self.text('```{}\n{}```'.format(lang or '', code))

    def quote(self, text):
        # Add quote '>' at the beginning of each line when quote is activated.
        return self.text('\n'.join('> ' + l for l in text.splitlines()))

    def math_block(self, contents):
        return self.text('$${0}$$'.format(contents))

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

    def math(self, contents):
        return self.text('${0}$'.format(contents))

    def text(self, text):
        return text
