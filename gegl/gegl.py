# coding: utf-8
# Author: João S. O. Bueno

import sys
from gi.repository import Gegl as _gegl

_gegl.init(sys.argv[1:])

def list_operations(filter=""):
    ops = _gegl.list_operations()
    return [op for op in ops if filter in op]

class OpNode(object):
    """ Wrapper for a GEGL node with an operation

    You can access OpNode._node attribute for raw access
    to the GEGL node as exposed by pygobject
7
    """
    def __init__(self, operation, **kw):
        object.__setattr__(self, "_node",  _gegl.Node())
        self.operation = operation

    @classmethod
    def _from_raw_node(cls, _node):
        self = cls.__new__(cls)
        object.__setattr__(self, "_node",  _node)
        return self

    def __setattr__(self, attr, value):
        self._node.set_property(attr, value)

    def __getattr__(self, attr):
        return self._node.get_property(attr)

    def connect_from(self, other, output="output", input="input"):
        # Allow working with both wrapped and raw nodes:
        if hasattr(other, "_node"):
            other = other._node
        return self._node.connect_from(input, other, output)

    def connect_to(self, other, output="output", input="input"):
        if hasattr(other, "_node"):
            other = other._node
        return self._node.connect_to(output, other, input)

    # Keep orginal Yosh's Pygegl ">>" and "<<" overriding for
    # connecting nodes:
    __lshift__ = connect_from
    __rshift__ = connect_to

    def __repr__(self):
        return "OpNode('%s')" % self.operation

class Graph(object):
    """ Wrapper for a GEGL node which parents OP nodes.

    You can access OpNode._node attribute for raw access
    to the GEGL node as exposed by pygobject
    """

    def __init__(self,  *args, **kw):
        self.auto = True
        if "auto" in kw:
            self.auto = kw.pop("auto")
        self._node = _gegl.Node()
        # TODO: maybe specialize self._children so
        # that it cannot be modified, thus becoming
        # inconsistent with the Graph contents;
        self._children = []
        for op in args:
            self.append(op)

    def append(self, op):
        if isinstance(op, OpNode):
            node = op
        elif isinstance(op, _gegl.Node):
            node = OpNode._from_raw_node(op)
        else:
            if not ":" in op:
                op = "gegl:" + op
            node = OpNode(op)
        self._node.add_child(node._node)
        if self.auto and self._children:
            node.connect_from(self._children[-1])
        # Not shure if Gegl's Node.get_children is
        # ordered by inversed insertion order.
        # anyway, just the "inversed" part makes it
        # simpler to have  a Python list holding
        # a reference to all children rather
        # than just fecthing the nodes from Gegl
        self._children.append(node)

    def __getitem__(self, index):
        return self._children[index]

    def __len__(self):
        return len(self._children)

    def __repr__(self):
        return "Graph(%s)" % ", ".join("'%s'" % 
                child.get_property("operation")
                        for child in self._node.get_children())

    def __call__(self):
        self._children[-1]._node.process()

    process = __call__

# Transparently make available all remaining GEGL calls:

for key in dir(_gegl):
    if key.startswith("_"): continue
    if key in ("LookupFunction", "NodeFunction", "TileCallback"): continue
    if key not in globals():
        globals()[key] = getattr(_gegl, key)

