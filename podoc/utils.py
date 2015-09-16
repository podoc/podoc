# -*- coding: utf-8 -*-

"""Utility functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op
import json


#------------------------------------------------------------------------------
# Bunch
#------------------------------------------------------------------------------

class Bunch(dict):
    """A dict with additional dot syntax."""
    def __init__(self, *args, **kwargs):
        super(Bunch, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def copy(self):
        return Bunch(super(Bunch, self).copy())


def _test_file_path(filename):
    curdir = op.realpath(op.dirname(__file__))
    path = op.join(curdir, 'test_files/' + filename)
    return path


def _load_test_file(filename):
    path = _test_file_path(filename)
    ext = op.splitext(filename)[1]
    if ext == '.json':
        with open(path, 'r') as f:
            return json.load(f)
    elif ext == '.md':
        with open(path, 'r') as f:
            return f.read()
    elif ext == '.py':
        assert op.splitext(filename)[0].endswith('_ast')
        with open(path, 'r') as f:
            contents = f.read()
        ns = {}
        exec(contents, {}, ns)
        return ns['ast']
