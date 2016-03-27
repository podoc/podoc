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

def test_cli():
    runner = CliRunner()
    result = runner.invoke(podoc, [])
    assert result.exit_code == 0
    assert result.output == '\n'
