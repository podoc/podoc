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
from ..core import Podoc
from ..utils import dump_text, load_text

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def _podoc(cmd=None, stdin=None):
    runner = CliRunner()
    cmd = cmd.split(' ') if cmd else ''
    result = runner.invoke(podoc, cmd, input=stdin)
    if result.exit_code != 0:  # pragma: no cover
        print(result.output)
        print_exception(*result.exc_info)
    assert result.exit_code == 0
    return result.output


def test_cli_1():
    """From markdown to AST to markdown again, using stdin."""
    ast_s = _podoc('--no-pandoc -f markdown -t ast', stdin='hello world')
    assert 'hello' in ast_s
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


def test_cli_3(tempdir):
    """From notebook to markdown."""
    path = op.join(tempdir, 'hello.md')
    path_o = op.join(tempdir, 'hello.ipynb')
    dump_text('hello world', path)
    _podoc('{} -o {}'.format(path, path_o))
    assert '"cell_type": "markdown"' in load_text(path_o)


def test_cli_md_nb():
    """From Markdown sto notebook with the CLI."""
    nb_s = _podoc('--no-pandoc -f markdown -t notebook',
                  stdin='hello *world*')
    # From dict string to notebook.
    nb = Podoc(with_pandoc=False).loads(nb_s, 'notebook')
    assert nb.cells[0].cell_type == 'markdown'
    assert nb.cells[0].source == 'hello *world*'
