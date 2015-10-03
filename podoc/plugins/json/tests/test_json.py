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

def test_read_json(podoc, hello_json_path, hello_ast):
    """Test JSON json file => podoc AST."""
    podoc.attach(JSON, 'from')
    ast = podoc.read_file(hello_json_path)
    assert ast == hello_ast


def test_write_json(tempdir, podoc, hello_ast, hello_json):
    """Test podoc AST => json dict."""
    podoc.attach(JSON, 'to')
    json = podoc.write_contents(hello_ast)
    assert json == hello_json
    path = op.join(tempdir, 'test.json')
    with open(path, 'w') as f:
        podoc.save(f, json)
