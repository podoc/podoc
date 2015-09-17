# -*- coding: utf-8 -*-

"""Utility functions."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import os.path as op


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


#------------------------------------------------------------------------------
# Fixture utility functions
#------------------------------------------------------------------------------

def _test_file_path(filename):
    curdir = op.dirname(op.realpath(__file__))
    path = op.join(curdir, 'test_files/' + filename)
    return path


def _open_test_file(filename):
    path = _test_file_path(filename)
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
        else:
            raise ValueError("This file extension is unsupported in "
                             "test_files.")
