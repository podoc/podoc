# -*- coding: utf-8 -*-

"""Utility functions."""


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
# pandoc wrapper
#------------------------------------------------------------------------------

def pandoc(from_path, to_path, **kwargs):
    """Convert a document with pandoc."""
    import pypandoc
    return pypandoc.convert(from_path, to_path, **kwargs)
