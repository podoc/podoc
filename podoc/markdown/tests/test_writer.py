# -*- coding: utf-8 -*-

"""Test Markdown writer."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from ..writer import MarkdownWriter


# -----------------------------------------------------------------------------
# Test Markdown writer
# -----------------------------------------------------------------------------

def test_markdown_writer_newline():
    w = MarkdownWriter()
    w.text('Hello.')
    w.linebreak()
    w.text('Hello.\n')
    expected = ('Hello.\n' * 2)
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
                          "![Some image](my_image.png)"))

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

    w.quote('Good, and you?\nEnd of citation.')
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

    w.code('print("Hello world!")\n')
    w.newline()

    w.text('Go to ')
    w.link('google', 'http://www.google.com')
    w.text('. And here is an image for you:')
    w.newline()

    w.image('Some image', 'my_image.png')

    assert w.contents == expected
