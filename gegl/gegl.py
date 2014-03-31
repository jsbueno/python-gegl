# coding: utf-8
# Author: João S. O. Bueno

import sys
from gi.repository import Gegl as _gegl

DEFAULT_OP_NAMESPACE = "gegl"

_gegl.init(sys.argv[1:])

def list_operations(filter=""):
    ops = _gegl.list_operations()
    return [op for op in ops if filter in op]

class OpNode(object):
    """ Wrapper for a GEGL node with an operation

    You can access OpNode._node attribute for raw access
    to the GEGL node as exposed by pygobject
    """
    def __init__(self, operation, **kw):
        object.__setattr__(self, "_node",  _gegl.Node())
        self.operation = operation
        for key, value in kw.items():
            setattr(self, key, value)

    @classmethod
    def _from_raw_node(cls, _node):
        self = cls.__new__(cls)
        object.__setattr__(self, "_node",  _node)
        return self

    def _set_operation(self, value):
        if self._node.get_property("operation") is not None:
            raise ValueError("Operation in a node can't be "
                              "changed once it is set.")
        if not ":" in value:
            value = "%s:%s" % (DEFAULT_OP_NAMESPACE, value)
        self._node.set_property("operation", value)
        self._reset_properties()

    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            return object.__setattr__(self, attr, value)
        if attr == "operation":
            return self._set_operation(value)

        if self._property_types[attr][0] == "GType GeglColor":
            if not isinstance(value, Color):
                value = Color(value)
            value = value._color
        self._node.set_property(attr, value)

    def __getattr__(self, attr):
        if attr.startswith("_"):
            return object.__getattribute__(self, attr)
        res = self._node.get_property(attr)
        if isinstance(res, _gegl.Color):
            res = Color(res)
        return res

    # Make properties available as items, 
    # because a log of them have "-" in their names 
    # eg. "line-height"
    def __setitem__(self, key, value):
        # too much user nursing?
        if not key in self.properties:
            raise KeyError("%s not a property for this operation")
        return setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    # GEGL-op properties != Python properties
    @property  
    def properties(self):
        if not "_property_names" in self.__dict__:
            self._reset_properties()
        return self._property_names

    def _reset_properties(self):
        # the actual value_type object is not, for now, as usefull as its str
        # so we are keeping both
        properties = {
            prop.name: (repr(prop.value_type).strip("<>").rsplit(None,1)[0],
                        prop.value_type)
            for prop in _gegl.Operation().list_properties(self.operation)
            }
        self._property_names = set(properties.keys())
        self._property_types = properties

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
        props = []
        for prop in self.properties:
            value = getattr(self, prop)
            props.append((prop, value))

        return "OpNode('%s'%s%s)" % (self.operation,
                     ", " if props else "", 
                     ", ".join("%s=%s" % (prop, repr(value)) 
                               for prop, value in sorted(props) ))
                     
    def __dir__(self):
        base =  ['__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattr__', '__getattribute__', '__hash__', '__init__', '__lshift__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__rshift__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_from_raw_node', '_node', 'connect_from', 'connect_to', 'properties']
        return base + sorted(self.properties)


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

    def __str__(self):
        rev_children = {node._node: node for node in self._children}
        last = self._children[-1]._node
        connected_list = []
        while last:
            connected_list.append(rev_children.pop(last).operation)
            last = last.get_producer("input", None)
        output = " -> ".join(reversed(connected_list))
        if rev_children:
            output += "\n unconnected: " + ", ".join(rev_children.values())
        return output

    def __repr__(self):
        return "Graph(%s)" % ", ".join("'%s'" % 
                child.operation
                for child in self._children)

    def __call__(self):
        self._children[-1]._node.process()

    def to_xml(self, path_root="/"):
        return self._children[-1]._node.to_xml(path_root)

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

    def __eq__(self, other):
        try:
            if len(other) != 4:
                return False
        except TypeError:
            return False
        for item in zip(self, other):
            if item[0] != item[1]:
                return False
        return True

# Transparently make available all remaining GEGL calls:

for key in dir(_gegl):
    if key.startswith("_"): continue
    if key in ("LookupFunction", "NodeFunction", "TileCallback"): continue
    if key not in globals():
        globals()[key] = getattr(_gegl, key)

