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

from .core import Podoc
from .plugin import IPlugin, discover_plugins, get_plugin


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
__version__ = '0.1.0.dev0'
__version_git__ = __version__ + _git_version()


# Set a null handler on the root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


_logger_fmt = '%(asctime)s  [%(levelname)s]  %(caller)s %(message)s'
_logger_date_fmt = '%H:%M:%S'


class _Formatter(logging.Formatter):
    def format(self, record):
        # Only keep the first character in the level name.
        record.levelname = record.levelname[0]
        filename = op.splitext(op.basename(record.pathname))[0]
        record.caller = '{:s}:{:d}'.format(filename, record.lineno).ljust(16)
        return super(_Formatter, self).format(record)


def add_default_handler(level='INFO'):
    handler = logging.StreamHandler()
    handler.setLevel(level)

    formatter = _Formatter(fmt=_logger_fmt,
                           datefmt=_logger_date_fmt)
    handler.setFormatter(formatter)

    logger.addHandler(handler)


def test():
    """Run the full testing suite of podoc."""
    import pytest
    pytest.main()


def _load_all_native_plugins():
    """Load all native plugins when importing the library."""
    curdir = op.dirname(op.realpath(__file__))
    plugins_dir = op.join(curdir, 'plugins')
    discover_plugins([plugins_dir])


# Load all native plugins when importing the library.
_load_all_native_plugins()
