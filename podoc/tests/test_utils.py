# -*- coding: utf-8 -*-

"""Test utility functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging
import os.path as op

from pytest import mark

from ..testing import ae, has_pandoc
from ..utils import Bunch, pandoc, Path, open_text, save_text

logger = logging.getLogger(__name__)

require_pandoc = mark.skipif(not(has_pandoc()),
                             reason='pypandoc is not available')


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_bunch():
    obj = Bunch()
    obj['a'] = 1
    assert obj.a == 1
    obj.b = 2
    assert obj['b'] == 2
    assert obj.copy().a == 1


def test_path():
    print(Path(__file__))
    assert Path(__file__).exists()


#------------------------------------------------------------------------------
# Test file I/O
#------------------------------------------------------------------------------

def test_open_save_text(tempdir, hello_markdown):
    path = op.join(tempdir, 'test.txt')
    save_text(path, hello_markdown)
    assert open_text(path) == hello_markdown


#------------------------------------------------------------------------------
# Test pandoc wrapper
#------------------------------------------------------------------------------

@require_pandoc
def test_pandoc(tempdir, hello_markdown, hello_json):
    from_path = op.join(tempdir, 'hello.md')
    with open(from_path, 'w') as f:
        f.write(hello_markdown)
    output = pandoc(from_path, 'json')
    converted = json.loads(output)
    ae(converted, hello_json)


@require_pandoc
def test_pandoc_meta(tempdir, hello_markdown):
    pandoc_json = [{'unMeta': {}}, [
                   {'c': [{'c': 'hello', 't': 'Str'}],
                    't': 'Para',
                    'm': {'zero': 0},
                    },
                   ]]
    path = op.join(tempdir, 'hello.json')
    with open(path, 'w') as f:
        json.dump(pandoc_json, f)
    output = pandoc(path, 'markdown')
    assert output == 'hello\n'
