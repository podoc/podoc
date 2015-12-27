# -*- coding: utf-8 -*-

"""Testing functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging
import os
import os.path as op

import pytest

from .ast import _remove_json_meta
from .core import Podoc, open_file
from .plugin import iter_plugins_dirs, get_plugin

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


def get_test_file_path(filename):
    curdir = op.dirname(op.realpath(__file__))
    path = op.join(curdir, 'test_files/' + filename)
    return path


def open_test_file(filename):
    path = get_test_file_path(filename)
    if not op.exists(path):
        raise ValueError("The test file %s doesn't exist." % filename)
    ext = op.splitext(filename)[1]
    with open(path, 'r') as f:
        if ext == '.json':
            return json.load(f)
        elif ext == '.md':
            return f.read()
        if ext == '.py':
            assert op.splitext(filename)[0].endswith('_ast')
            contents = f.read()
            ns = {}
            exec(contents, {}, ns)
            return ns['ast']
        else:  # pragma: no cover
            raise ValueError("This file extension is unsupported in "
                             "test_files.")


def test_names():
    """Return the names of all test files."""
    curdir = op.dirname(op.realpath(__file__))
    test_files_dir = op.join(curdir, 'test_files')
    names = [f[:-7] for f in os.listdir(test_files_dir)
             if f.endswith('_ast.py')]
    return sorted(names)


def iter_test_files():
    """Iterate over all test files in all plugin directories.

    Yield a tuple `(plugin_name, test_name, path)`.

    """
    names = test_names()
    for plugin_dir in iter_plugins_dirs():
        dir_path = op.join(plugin_dir, 'test_files')
        # Files that match one of the test names.
        for file in os.listdir(dir_path):
            for name in names:
                if file.startswith(name):
                    yield (op.basename(plugin_dir), name,
                           op.join(dir_path, file))


def _test_readers(plugin_name, test_name, path):
    p = get_plugin(plugin_name)()
    logger.debug("Test file %s: reader.", path)
    ast_read = p.attach_pre(Podoc()).read_file(path)
    ast_expected = open_test_file('%s_ast.py' % test_name)
    assert ast_read == ast_expected


def _test_writers(plugin_name, test_name, path):
    p = get_plugin(plugin_name)()
    logger.debug("Test file %s: writer.", path)
    ast = open_test_file('%s_ast.py' % test_name)
    converted = p.attach_post(Podoc()).write_contents(ast)
    ae(converted, open_file(path, plugin_name))


def test():  # pragma: no cover
    """Run the full testing suite of podoc."""
    pytest.main()
