# coding: utf-8
# Author: João S. O. Bueno

import sys
from gi.repository import Gegl as _gegl
from .path import Path

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
        # cyclic - TODO: replace with weakref
        self._node._wrapper = self
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
        elif attr in {"aux", "input", "output"}:
            return self._set_pad(attr, value)
        if "_" in attr:
            attr = attr.replace("_", "-")
        try:
            self.__setitem__(attr, value)
        except KeyError:
            raise ValueError("%s not a property for this operation" % attr)


    def __getattr__(self, attr):
        if attr.startswith("_"):
            return object.__getattribute__(self, attr)
        elif attr in {"aux", "input", "output"}:
            return self._get_pad(attr)
        if "_" in attr:
            attr = attr.replace("_", "-")
        return self.__getitem__(attr)

    # Make properties available as items, 
    # because a log of them have "-" in their names 
    # eg. "line-height"
    def __setitem__(self, attr, value):
        # too much user nursing?
        if not attr in self.properties:
            raise KeyError("%s not a property for this operation" % attr)

        if self._property_types[attr][0] == "GType GeglColor":
            if not isinstance(value, Color):
                value = Color(value)
            value = value._color
        elif self._property_types[attr][2].name == "buffer":
            if not isinstance(value, Buffer):
                value = Buffer(value)
            value = value.buffer
        elif self._property_types[attr][0] == 'GType GeglPath':
            if not isinstance(value, Path):
                value = Path(value)
            value = value._path
        #Currently there are no ops that use Rectangle as an input parameter 
        #  
        # TODO: write tests for this parameter wrapping stuff
        # TODO: check for other special attribute types
        self._node.set_property(attr, value)

    def __getitem__(self, attr):
        res = self._node.get_property(attr)
        if isinstance(res, _gegl.Color):
            res = Color(res)
        elif isinstance(res, _gegl.Buffer):
            # TODO: figure out  a way of retrieving the Buffer data format.
            res = Buffer(res)
        elif isinstance(res, _gegl.Rectangle):
            res = Rectangle(res)
        elif isinstance(res, _gegl.Path):
            res = Path(res)
        return res

    # GEGL-op properties != Python properties
    @property  
    def properties(self):
        if not "_property_names" in self.__dict__:
            self._reset_properties()
        return self._property_names

    def _reset_properties(self):
        #Caches in Python the property names and descriptions
        #for the GEGL operation.

        #Sets up some required attributes for the object, since
        #__init__ may not be called, depending on the 
        #factory function called.
        self._pads = {"output":[]}
        # the actual value_type object is not, for now, as usefull as its str
        # so we are keeping both
        properties = {
            prop.name: (repr(prop.value_type).strip("<>").rsplit(None,1)[0],
                        prop.value_type,
                        prop)
            for prop in _gegl.Operation().list_properties(self.operation)
            }
        self._property_names = set(properties.keys())
        self._property_types = properties

    def connect_from(self, other, output="output", input="input"):
        connect_wrapper = None
        self._pads[input] = other
        if isinstance(other, Graph):
            other = other._children[-1]

        # Allow working with both wrapped and raw nodes:
        if isinstance(other, OpNode):
            connected_wrapper = other
            other = other._node
        else:
            connected_wrapper = other._wrapper
        # syncronize the references in the other node High
        # level data structures:
        if connected_wrapper:
            connected_wrapper._pads.get(output, []).append(self)
        return self._node.connect_from(input, other, output)

    def connect_to(self, other, input="input", output="output"):
        connect_wrapper = None
        if not output in self._pads:
            self._pads[output] = []
        self._pads[output].append(other)

        if isinstance(other, Graph):
            other = other._children[0]
        if isinstance(other, OpNode):
            connect_wrapper = other
            other = other._node
        elif hasattr(other, "_wrapper"):
            connect_wrapper = other._wrapper
        # syncronize the references in the other node High
        # level data structures:
        if connect_wrapper:
            connect_wrapper._pads[input] = self
        return self._node.connect_to(output, other, input)

    def _set_pad(self, pad, node):
        if pad in {"aux", "input"}:
            self.connect_from(node, input=pad)
        else: # output
            self.connect_to(node)

    def _get_pad(self, pad):
        return self._pads[pad]

    def has_pad(self, pad="output"):
        return self._node.has_pad(pad)

    def get_producer(self, pad="input", extra=None):
        return self._node.get_producer(pad, extra)
    
    def set(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # And an alias to the same name used in 
    # C GEGL Nodes:
    set_properties = set

    # call to _gegl.node_get_consumers(...)
    # is broken at the moment and there is no known workaround
    # TODO
    #def get_consumers(self, pad="output"):
    #    pass

    # Keep original Yosh's Pygegl ">>" and "<<" overriding for
    # connecting nodes:
    # NB: these are untested and likely not working. Wait
    # for a proper implementation at the Graph object instead.
    
    def __eq__(self, other):
        # Only compares instances of this class  - 
        # lower levels should be wrapped.
        if self.operation != other.operation:
            return False
        return ({prop: self[prop] for prop in self.properties} == 
                {prop: other[prop] for prop in other.properties})

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

    keys = lambda s: s.properties

    def disconnect(self, pad="input"):
        # TODO: missing tests
        producer = self._pads.get(pad, None)
        self._pads[pad] = None
        result = self._node.disconnect(pad)
        if isinstance(producer, Graph):
            producer = producer[-1]
        if pad in ("input", "aux"):
            for i, item in enumerate(producer.output):
                if item is self or item is self._parent_graph:
                    del producer.output[i]
                    break
        elif pad == "output" and self.output:
            for consumer in self.output:
                if isinstance(consumer, Graph):
                    consumer = consumer[0]
                consumer.input = None
        return result


    def __dir__(self):
        base = sorted(
                ['__class__', '__delattr__', '__dict__', '__doc__', 
                 '__format__', '__getattr__', '__getattribute__',
                 '__hash__', '__init__', '__lshift__', '__module__', 
                 '__new__', '__reduce__', '__reduce_ex__', '__repr__', 
                 '__rshift__', '__setattr__', '__sizeof__', '__str__',
                 '__subclasshook__', '__weakref__', '_from_raw_node', 
                 '_node', 'connect_from', 'connect_to', 'has_pad', 'keys',
                 'properties', 'aux', 'input', 'output', 
                 'operation','disconnect', 'set'])
        return base + sorted(self.properties)


class Graph(object):
    """ Wrapper for a GEGL node which parents OP nodes.

    You can access OpNode._node attribute for raw access
    to the GEGL node as exposed by pygobject

    When instantiated, a list of operators
    can be passed: these nodes will be instantiated
    and "append"ed into the graph

    """

    operation = "meta"

    def __init__(self,  *args, **kw):
        self.auto = True
        if "auto" in kw:
            # disabling "auto" actually has undefined behaviors.
            # all nodes in a graph should be connected in the
            # order of insertion. Subgraphs should be created
            # as another instance of this class.
            self.auto = kw.pop("auto")
        self._node = _gegl.Node()

        # Anotating this python class in the GIR object, in a circular
        # reference.
        # pay attention in object cycles:
        self._node.container = self

        # ._children is mostly a "bag of nodes" 
        # so that we have an easy reference on the Python side
        # the important thing is the last node on a list -
        # which is the one actually processed, or which
        # output is connectes as a subgraph
        self._children = []
        for op in args:
            self.append(op)

    def _add_child(self, op):
        if isinstance(op, tuple):
            op, params = op
            params = dict(params)
        else:
            params = {}
        if isinstance(op, (OpNode, Graph)):
            node = op
        elif isinstance(op, _gegl.Node):
            node = OpNode._from_raw_node(op)
        else:
            node = OpNode(op, **params)
        self._node.add_child(node._node)
        # attention: creating cyclic reference:
        # TODO: use weakrefs
        node._node._parent_graph = self
        return node
        if self.auto and self._children:
            source_node = self
            # Allows to properly connect to subgraphs inside the current graph
            while isinstance(source_node, Graph):
                source_node = source_node._children[-1]
            node.connect_from(source_node)

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
        node = self._add_child(op)
        if self.auto and self._children:
            source_node = self
            # Allows to properly connect to subgraphs inside the current graph
            while isinstance(source_node, Graph):
                source_node = source_node._children[-1]
            node.connect_from(source_node)
        self._children.append(node)

    def insert(self, index, op):
        self[index].disconnect("input")
        node = self._add_child(op)
        first_node = last_node = node
        while isinstance(first_node, Graph):
            first_node = first_node[0]
        while isinstance(last_node, Graph):
            last_node = last_node[-1]
        self._children.insert(index, node)
        if index > 0:
            first_node.input = self[index - 1]
        if index < len(self) - 1:
            last_node.output = self[index + 1]


    def connect_to(self, other, input="input", output="output"):
        # This is the same as connecting the current last node
        # of the graph to another node/graph
        if isinstance(other, Graph):
            other = other._children[0]
        self._children[-1].connect_to(other, input, output)

    def connect_from(self, other, output="output", input="input"):
        if isinstance(other, Graph):
            other = other._children[-1]
        self._children[0].connect_from(other, output, input)

    def plug_as_aux(self, other):
        """Helper function to plug this
        subgraph in the "aux" pad of some other
        graph - 
        eg.:
        >>> g1 = gegl.Graph("color", "over", "crop", "sdl-display")
        >>> g2 = gegl.Graph("grid", "rotate")
        >>> g2.plug_as_aux(g1[1])  # "over"  node
        >>> g1[0].value=(1,1,1)
        >>> g1[2].width = g1[2].height = 320
        >>> g2[1].degrees = 30
        >>> g1()
        """
        self.connect_to(other, input="aux")

    def __getitem__(self, index):
        return self._children[index]
    
    def __setitem__(self, index, op):
        del self[index]
        self.insert(index, op)

    def __delitem__(self, index):
        morituri = self._children[index]
        def disconnect_all(node, pads):
            for pad in pads:
                if pad in node._pads:
                    node.disconnect(pad)
        if isinstance(morituri, Graph):
            disconnect_all(morituri[0], ("input", "aux"))
            disconnect_all(morituri[-1], ("output",))
        else:
            disconnect_all(morituri, ("input", "aux", "output"))
        del self._children[index]
        # Reconnect the remaining nodes:
        if index > 0:
            self[index].input = self[index - 1]


    def __len__(self):
        return len(self._children)

    def __repr__(self):
        return self._recursive_repr()

    def _recursive_repr(self, starting_index=0):
        index = starting_index
        parts = []
        aux_graphs = []
        for child in self._children:
            op = child.operation
            if op == "meta": # it is a sub-graph
                op = repr(child)
            elif child.has_pad("aux"):
                producer = child.get_producer("aux")
                if producer is None:
                    op += "[*]"
                else:
                    op += "[@%d]" % index
                    index += 1
                    if hasattr(producer, "_parent_graph"):
                        aux_graphs.append(producer._parent_graph)
                    else:
                        aux_graphs.append(producer)
            parts.append(op)
        result = "Graph(%s)" % ", ".join("%d:%s" % (j, part) 
                    for j, part in enumerate(parts))
        for i, aux_graph in enumerate(aux_graphs, starting_index):
            if isinstance(aux_graph, Graph):
                result += "\n\t%d - %s" % (i, "\n\t".join(
                    line for line in 
                        aux_graph._recursive_repr(index).split("\n"))
                    )
            else:
                result += "\n\t%d - [Low level]" % i

        return result

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
        if isinstance(r, str):
            self._color = _gegl.Color.new(r)
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

class Buffer(object):
    """
    High level interface to gegl's Buffer objects
    
    The current gir bindings make the raw buffer
    a bit tricky to use - in
    particular, the "get" method here allows
    access to the buffer's binary's contents.
    
    The low level object can be acessed in buffer.buffer.
    These buffers are ok to be on used with the 
    "gegl:write-buffer" operation
    """
    def __init__(self, rect, format="RGBA u8"):
        if isinstance(rect, _gegl.Buffer):
            self.buffer = rect
            # gegl's gegl_buffer_{get,set}_format 
            # are not showing up under gir instrspection. :-/
            self.format = format
            return
        self.rect = Rectangle(rect)
        self.format = format
        # the standard Buffer constructor in gegl
        # is currently unusable - this alternative constructor
        # is a nice work-around
        self.buffer = _gegl.Buffer.new(format, *self.rect.as_sequence())

    def get(self, scale=1, format=None):
        if format is None:
            format = self.format
        return self.buffer.get(self.buffer.get_extent(),
                               scale, format, _gegl.AUTO_ROWSTRIDE)

    def set(self, rect=None, format=None, src=""):
        if rect is None:
            rect = self.get_extent()
        elif not isinstance(rect, Rectangle):
            rect = Rectangle(rect)
        if format is None:
            format = self.format
        # retrieve the lowlevel _gegl.Rectangle:
        rect = rect.rect
        # this call is seen in introspection heavily
        # modified from what is described in the C API.
        # in particular, there is no access to the scale or
        # row-stride parameters.
        self.buffer.set (rect, format, src)

    def get_extent(self):
        return Rectangle(self.buffer.get_extent())


class Rectangle(object):
    def __init__(self, multi=0, y=0, width=640, height=480):
        """
        Creates a gegl Rectangle Object 
        
        The first argument can be a Buffer - its extents will be used
        as the rectangle bounds - 
        The first argument can also be a 4-tuple or other sequence,
        which will be interpreted as (x,y, width, height). If
        a 2-tuple or sequnece, the numbers are used as width and height,
        with x = y = 0.
        
        The native gir gegl.Rectangle is public at the .rect attribute
        """
        #self.rect = _gegl.Rect()
        if isinstance(multi, Buffer):
            multi = multi.buffer
        if isinstance(multi, _gegl.Buffer):
            self.rect = multi.get_extent()
            return
        elif isinstance(multi, _gegl.Rectangle):
            # just wrap it:
            self.rect = multi
            return
        elif isinstance(multi, Rectangle):
            x, y, width, height = multi.as_sequence()
        else:
            try:
                # if two tuple, use as with and height
                width, height = multi
            except ValueError:
                try:
                    x, y, width, height = multi
                except ValueError:
                    x = multi
            except TypeError:
                x = multi
            else:
                x = y = 0
        self.rect = _gegl.Rectangle()
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    x = property(lambda s: s.rect.x,
                 lambda s,v: setattr(s.rect, "x", v))
    y = property(lambda s: s.rect.y,
                 lambda s,v: setattr(s.rect, "y", v))
    width = property(lambda s: s.rect.width,
                     lambda s,v: setattr(s.rect, "width", v))
    height = property(lambda s: s.rect.height,
                      lambda s,v: setattr(s.rect, "height", v))

    def as_sequence(self):
        return self.x, self.y, self.width, self.height

    def __repr__(self):
        return "Rectangle%s" % self.as_sequence()


# Transparently make available all remaining GEGL calls:

for key in dir(_gegl):
    if key.startswith("_"): continue
    if key in ("LookupFunction", "NodeFunction", "TileCallback"): continue
    if key not in globals():
        globals()[key] = getattr(_gegl, key)

