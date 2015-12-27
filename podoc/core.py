# -*- coding: utf-8 -*-

"""Core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from functools import wraps
import inspect
import logging

from six import string_types

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Main class
#------------------------------------------------------------------------------

def _get_annotation(func, name):
    return getattr(func, '__annotations__', {}).get(name, None)


def _find_path(edges, source, target):
    """Find a path from source to target in a graph specified as a list
    of edges."""
    out = None
    if (source, target) in edges:
        # Direct conversion exists.
        out = [source, target]
    else:
        # Find an intermediate format.
        inter0 = [t1 for t0, t1 in edges if t0 == source]
        inter1 = [t0 for t0, t1 in edges if t1 == target]
        inter = sorted(set(inter0).intersection(inter1))
        if inter:
            out = [source, inter[0], target]
    return out


def _type_name(t):
    if isinstance(t, string_types):
        return t
    elif inspect.isclass(t):
        return t.__name__


class Podoc(object):
    """Conversion pipeline for markup documents.

    This class implements the core conversion functionality of podoc.

    """
    def __init__(self):
        self._funcs = {}

    @property
    def types(self):
        """List of all types that appear in the registered functions."""
        if not self._funcs:
            return []
        t0, t1 = zip(*self._funcs.keys())
        return list(set(t0).union(t1))

    @property
    def conversion_pairs(self):
        """List of registered conversion pairs."""
        return list(self._funcs.keys())

    def get_func(self, t0, t1):
        """Get the function registered for a pair of types."""
        t0 = self._get_type(t0)
        t1 = self._get_type(t1)
        return self._funcs.get((t0, t1), None)

    def _get_type(self, name):
        """Get a type from its name."""
        if isinstance(name, string_types):
            name = name.lower()
            for t in self.types:
                if _type_name(t).lower() == name:
                    return t
        else:
            assert name in self.types
            return name

    def register(self, func=None, source=None, target=None):
        """Register a conversion function between two types."""
        if func is None:
            return lambda _: self.register(_, source=source, target=target)
        assert func
        source = source or _get_annotation(func, 'source')
        target = target or _get_annotation(func, 'target')
        assert source
        assert target

        # Check the type of the source and target.
        @wraps(func)
        def wrapped(obj, **kwargs):
            if inspect.isclass(source):
                assert isinstance(obj, source)
            out = func(obj)
            if inspect.isclass(target):
                assert isinstance(out, target)
            return out

        self._funcs[(source, target)] = wrapped

    def convert(self, obj, types):
        """Convert an object by passing it through a chain of functions."""
        assert isinstance(types, (tuple, list))
        # Iterate over all successive pairs.
        for t0, t1 in zip(types, types[1:]):
            # Get the function registered for t0, t1.
            f = self.get_func(t0, t1)
            if not f:
                raise ValueError("No function registered for `{}` => `{}`.".
                                 format(_type_name(t0), _type_name(t1)))
            # Perform the conversion.
            obj = f(obj)
        return obj
