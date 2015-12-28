# -*- coding: utf-8 -*-

"""Testing functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

from .ast import _remove_json_meta

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Fixture utility functions
#------------------------------------------------------------------------------

def has_pandoc():  # pragma: no cover
    try:
        import pypandoc
        pypandoc.get_pandoc_version()
        return True
    except ImportError:
        logger.debug("pypandoc is not installed.")
    except FileNotFoundError:
        logger.debug("pandoc is not installed.")
    return False


def ae(a, b):
    if isinstance(a, (list, dict)):
        assert _remove_json_meta(a) == _remove_json_meta(b)
    else:
        assert a == b
