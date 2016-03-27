# -*- coding: utf-8 -*-

"""Test CLI."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from click.testing import CliRunner

from ..cli import podoc

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def _podoc(cmd=None, stdin=None):
    runner = CliRunner()
    cmd = cmd.split(' ') if cmd else ''
    result = runner.invoke(podoc, cmd, input=stdin)
    if result.exit_code != 0:
        print(result.exception)
    assert result.exit_code == 0
    return result.output


def test_cli():
    assert 'hello' in _podoc('--no-pandoc', stdin='hello')
