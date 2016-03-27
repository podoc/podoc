# -*- coding: utf-8 -*-

"""Test CLI."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os.path as op
from traceback import print_exception

from click.testing import CliRunner

from ..cli import podoc
from ..utils import dump_text

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def _podoc(cmd=None, stdin=None):
    runner = CliRunner()
    cmd = cmd.split(' ') if cmd else ''
    result = runner.invoke(podoc, cmd, input=stdin)
    if result.exit_code != 0:  # pragma: no cover
        print_exception(*result.exc_info)
    assert result.exit_code == 0
    return result.output


def test_cli_1():
    """From markdown to AST to markdown again, using stdin."""
    assert 'hello' in _podoc('--no-pandoc', stdin='hello')

    ast_s = _podoc('--no-pandoc', stdin='hello world')
    md = _podoc('--no-pandoc -f ast -t markdown', stdin=ast_s)
    assert md == 'hello world\n'


def test_cli_2(tempdir):
    """From markdown to AST to markdown again, using files."""
    path = op.join(tempdir, 'hello.md')
    path_o = op.join(tempdir, 'hello.json')
    dump_text('hello world', path)
    _podoc('--no-pandoc {} -o {}'.format(path, path_o))
    md = _podoc('--no-pandoc -f json -t markdown {}'.format(path_o))
    assert md == 'hello world\n'
