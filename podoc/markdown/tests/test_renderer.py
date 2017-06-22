# -*- coding: utf-8 -*-

"""Test Markdown renderer."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from ..renderer import MarkdownRenderer


# -----------------------------------------------------------------------------
# Test Markdown renderer
# -----------------------------------------------------------------------------

def test_markdown_renderer():
    w = MarkdownRenderer()

    assert w.text('Hello') == 'Hello'
    assert w.emph('Hello') == '*Hello*'
    assert w.strong('Hello') == '**Hello**'
    assert w.inline_code('code') == '`code`'

    assert w.linebreak() == '\n'
    assert w.newline() == '\n\n'

    assert w.heading('First chapter', 1) == '# First chapter'
    assert w.quote('a\nb') == '> a\n> b'
    assert w.code('a\n') == '```\na\n```'
    assert w.code('a\n', is_fenced=False) == '    a'

    assert w.link('label', 'link') == '[label](link)'
    assert w.image('label', 'image.png') == '![label](image.png)'
