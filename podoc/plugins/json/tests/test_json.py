# -*- coding: utf-8 -*-

"""Test JSON plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from .._json import JSON


#------------------------------------------------------------------------------
# Test JSON plugin
#------------------------------------------------------------------------------

def test_read_json(podoc, hello_pandoc_path, hello_ast):
    """Test JSON pandoc file => podoc AST."""
    podoc.set_plugins(plugins_from=[JSON])
    ast = podoc.read_file(hello_pandoc_path)
    assert ast == hello_ast


def test_write_json(tempdir, podoc, hello_ast, hello_pandoc):
    """Test podoc AST => pandoc dict."""
    podoc.set_plugins(plugins_to=[JSON])
    json = podoc.write_contents(hello_ast)
    assert json == hello_pandoc
    path = op.join(tempdir, 'test.json')
    with open(path, 'w') as f:
        podoc.save(f, json)
