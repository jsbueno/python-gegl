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
        for key, value in kw.iteritems():
            setattr(self, key, value)

    @classmethod
    def _from_raw_node(cls, _node):
        self = cls.__new__(cls)
        object.__setattr__(self, "_node",  _node)
        return self

    def __setattr__(self, attr, value):
        if isinstance(value, Color):
            value = value._color
        self._node.set_property(attr, value)

    def __getattr__(self, attr):
        res = self._node.get_property(attr)
        if isinstance(res, _gegl.Color):
            res = Color(res)
        return self._node.get_property(attr)

    def connect_from(self, other, output="output", input="input"):
        # Allow working with both wrapped and raw nodes:
        if hasattr(other, "_node"):
            other = other._node
        return self._node.connect_from(input, other, output)

    def connect_to(self, other, input="input", output="output"):
        if hasattr(other, "_node"):
            other = other._node
        return self._node.connect_to(output, other, input)

    # Keep original Yosh's Pygegl ">>" and "<<" overriding for
    # connecting nodes:
    def __lshift__(self, other):
        if self.connect_from(other):
            return self
        return None

    def __rshift__(self, other):
        if self.connect_to(other):
            return other
        return None

    def __repr__(self):
        return "OpNode('%s')" % self.operation

class Graph(object):
    """ Wrapper for a GEGL node which parents OP nodes.

    You can access OpNode._node attribute for raw access
    to the GEGL node as exposed by pygobject

    When instantiated, a list of operators
    can be passed: these nodes will be instantiated
    and "append"ed into the graph

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
        """Creates a new OpNode instance and appends it to the graph

        if self.auto is True, the new node is automatically connected
        with the preceeding node.

        Each operator may be a string with the operator name:
        if the operator prefix is "gegl:" it can be omitted.
        It can also be a gegl.OpNode instance or a raw
        gobject _gegl.Node instance

        And each such operator can be packed as a 2-tuple
        where the second element is a mapping (or 2-tuple sequence)
        with the properties for this operator.

        """
        if isinstance(op, tuple):
            op, params = op
            params = dict(params)
        else:
            params = {}
        if isinstance(op, OpNode):
            node = op
        elif isinstance(op, _gegl.Node):
            node = OpNode._from_raw_node(op)
        else:
            if not ":" in op:
                op = "gegl:" + op
            node = OpNode(op, **params)
        self._node.add_child(node._node)
        if self.auto and self._children:
            node.connect_from(self._children[-1])
        # Not shure if Gegl's Node.get_children is
        # ordered by reversed insertion order.
        # anyway, just the "reversed" part makes it
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
                        for child in self._children)

    def __call__(self):
        self._children[-1]._node.process()

    process = __call__

class Color(object):
    def __init__(self, r=1, g=1, b=1, a=1):
        if isinstance(r, _gegl.Color):
            self._color = r
            return
        self._color = _gegl.Color()
        if hasattr(r, "__len__"):
            if len(r) == 3:
                r,g,b = r
                a = 1.0
            elif len(r) == 4:
              r, g, b, a = r  
        self.set_rgba(r, g, b, a)

    def set_rgba(self,r ,g ,b ,a):
        self._color.set_rgba(r,g,b,a)

    def get_rgba(self):
        return self._color.get_rgba()

    def __getitem__(self, index):
        return self.get_rgba()[index]

    def __setitem__(self, index, value):
        color = list(self.get_rgba())
        color[index] = value
        self.set_rgba(*color)

    __len__ = lambda s: 4

    def set_rgb(self, r,g,b):
        self.set_rgba(r,g,b,self.a)

    r = red = property(lambda s:s.get_rgba()[0], lambda s,v: s.__setitem__(0,v))
    g = green = property(lambda s:s.get_rgba()[1], lambda s,v: s.__setitem__(1,v))
    b = blue = property(lambda s:s.get_rgba()[2], lambda s,v: s.__setitem__(2,v))
    a = alpha = property(lambda s:s.get_rgba()[3], lambda s,v: s.__setitem__(3,v))

    def __repr__(self):
        return "Color%s" % str(tuple(self))
    
    
# Transparently make available all remaining GEGL calls:

for key in dir(_gegl):
    if key.startswith("_"): continue
    if key in ("LookupFunction", "NodeFunction", "TileCallback"): continue
    if key not in globals():
        globals()[key] = getattr(_gegl, key)

