#############
GEGL
#############

Python lithweight wrapper for using GEGL - Generic Graphics Library
(http://www.gegl.org)

Currently working for Python2 and Python3

***********************
Justificative
***********************

In the past, there were custom Python bindings for GEGL
on the library source tree itself. However, that code
bit-rot and was removed, with the introduction of
gobject  introspection, automatic bindings for several
languages - Python included - could be generated.

The problem with the automatic bindings for GEGL is that
although usable, one has to do a lot of typing and copying around
to be able to leverage on the introspection capabilities
of Gobject and of GEGL itself.

This project ains to add some custom Python code that makes
it more "pythonic" to make full use of GEGL.

The file "snippets.py" contains an example of using
GEGL thorugh raw gobject introspection - you don't need
this project installed at all to use code like that.

With this installed, even in this early stage, the following
statements are enough to create and execute the
same GEGL graph used in "snippets.py":

>>> import gegl
>>> x = gegl.Graph("png-load", "invert", "png-save")
>>> x[0].path = "/home/gwidion/bla.png"
>>> x[0]
OpNode('gegl:png-load')
>>> x[2].path = "/home/gwidion/bla2.png"
>>>
>>> x()
>>>

********************
Prerequisites
********************
    You will need a working GEGL with Gobject introspection installed,
    and pygobject. This comes out of the box with proper install of GEGL
    and gobject introspection: works in Fedora 20 (late 2013) and possibly
    other recent distributions as of 2014.
    



   