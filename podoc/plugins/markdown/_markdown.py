# -*- coding: utf-8 -*-

"""Markdown plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from podoc.plugin import IPlugin

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# JSON plugin
#------------------------------------------------------------------------------

class Markdown(IPlugin):
    file_extensions = ('.md',)

    def reader(self, contents):
        # TODO
        from podoc.testing import open_test_file
        return open_test_file('hello_ast.py')

    def writer(self, ast):
        # TODO
        from podoc.testing import open_test_file
        return open_test_file('hello.md')
