# coding: utf-8
# Author: João S. O. Bueno

import sys
from gi.repository import Gegl as _gegl


"""
Creates facilities to use GEGL's Paths (Vectors)
and the operations that use then for stroking,
filling and other things.


"""
class Path(object):
    """
    Wrapper for a GEGL Path object. The string passed
    to create paths is a simple string with a  
    command (M - move, L - line, or C - curve) with
    coordinates separated by spaces - ex.: "M 0 0 L 100 100"
    """
    def __init__(self, path=None, *args):
        if path is None:
            self._path = _gegl.Path()
        elif isinstance(path, _gegl.Path):
            self._path = path
        elif isinstance(path, str):
            path_str = path
            if args:
                path_str += " " + " ".join(args)
            self._path = _gegl.Path.new_from_string(path_str)
        else:
            raise ValueError("Unrecognized parameters for Path")
        # FIXME: use weakrefs instead:
        self._path._wrapper = self
    # TODO: maintain path subcommands as components so they can
    # be edited as items
