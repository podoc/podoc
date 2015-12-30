# -*- coding: utf-8 -*-

"""Test Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from .._markdown import Markdown, MarkdownWriter, MarkdownRenderer


#------------------------------------------------------------------------------
# Test Markdown plugin
#------------------------------------------------------------------------------

def test_markdown_1():
    m = Markdown()
    ast = m.read_markdown('hello *world*')
    assert ast


# -----------------------------------------------------------------------------
# Test Markdown writer
# -----------------------------------------------------------------------------

def test_markdown_writer_newline():
    w = MarkdownWriter()
    w.text('Hello.')
    w.ensure_newline(1)
    w.text('Hello.\n')
    w.ensure_newline(1)
    w.text('Hello.\n\n')
    w.ensure_newline(1)
    w.text('Hello.\n\n\n')
    w.ensure_newline(2)
    w.text('End')

    expected = ('Hello.\n' * 4) + '\nEnd\n'

    assert w.contents == expected


def test_markdown_writer():
    w = MarkdownWriter()

    expected = '\n'.join(("# First chapter",
                          "",
                          "**Hello** *world*!",
                          "How are you? Some `code`.",
                          "",
                          "> Good, and you?",
                          "> End of citation.",
                          "",
                          "* Item **1**.",
                          "* Item 2.",
                          "",
                          "1. 1",
                          "  * 1.1",
                          "    * 1.1.1",
                          "2. 2",
                          "",
                          "```",
                          "print(\"Hello world!\")",
                          "```",
                          "",
                          ("Go to [google](http://www.google.com). "
                           "And here is an image for you:"),
                          "",
                          "![Some image](my_image.png)\n"))

    w.heading('First chapter', 1)
    w.newline()

    w.strong('Hello')
    w.text(' ')
    w.emph('world')
    w.text('!')
    w.linebreak()
    w.text('How are you? Some ')
    w.inline_code('code')
    w.text('.')
    w.newline()

    w.quote_start()
    w.text('Good, and you?')
    w.linebreak()
    w.text('End of citation.')
    w.quote_end()
    w.newline()

    w.list_item('Item ')
    w.strong('1')
    w.text('.')
    w.linebreak()
    w.list_item('Item 2.')
    w.newline()

    w.numbered_list_item('1')
    w.linebreak()
    w.list_item('1.1', level=1)
    w.linebreak()
    w.list_item('1.1.1', level=2)
    w.linebreak()
    w.numbered_list_item('2')
    w.newline()

    w.code_start()
    w.text('print("Hello world!")')
    w.code_end()
    w.newline()

    w.text('Go to ')
    w.link('google', 'http://www.google.com')
    w.text('. And here is an image for you:')
    w.newline()

    w.image('Some image', 'my_image.png')

    assert w.contents == expected


def test_markdown_renderer_link():
    s = '[a](b)'
    # Parse the string.
    ast = Markdown().read_markdown(s)
    # Render the AST to Markdown.
    contents = MarkdownRenderer().render(ast)
    assert contents.strip() == s
