# -*- coding: utf-8 -*-

"""Test JSON plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from ..json import JSON


#------------------------------------------------------------------------------
# Test JSON plugin
#------------------------------------------------------------------------------

def test_read_json(podoc, hello_pandoc_path, hello_ast):
    """Test JSON pandoc file => podoc AST."""
    podoc.set_plugins(plugins_from=[JSON])
    ast = podoc.convert_file(hello_pandoc_path)
    assert ast == hello_ast


def test_write_json(podoc, hello_ast, hello_pandoc):
    """Test podoc AST => pandoc dict."""
    podoc.set_plugins(plugins_to=[JSON])
    json = podoc.convert_contents(hello_ast)
    assert json == hello_pandoc
