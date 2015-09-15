# -*- coding: utf-8 -*-
# flake8: noqa

"""Markup document conversion."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os
import os.path as op
import subprocess


#------------------------------------------------------------------------------
# Global variables and functions
#------------------------------------------------------------------------------

def _git_version():
    curdir = os.getcwd()
    filedir, _ = op.split(__file__)
    os.chdir(filedir)
    try:
        fnull = open(os.devnull, 'w')
        version = ('-git-' + subprocess.check_output(
                   ['git', 'describe', '--abbrev=8', '--dirty',
                    '--always', '--tags'],
                   stderr=fnull).strip().decode('ascii'))
        return version
    except (OSError, subprocess.CalledProcessError):
        return ""
    finally:
        os.chdir(curdir)


__author__ = 'Cyrille Rossant'
__email__ = 'cyrille.rossant at gmail.com'
__version__ = '0.1.0-dev'
__version_git__ = __version__ + _git_version()


# Set a null handler on the root logger
logger = logging.getLogger()
logger.addHandler(logging.NullHandler())


def test():
    """Run the full testing suite of podoc."""
    import pytest
    pytest.main()
