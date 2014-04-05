# coding: utf-8
import gegl
import gtk

"""
Minimal example of how to use Python-GEGL with
old Python-gtk2 bindings. 

It can be needed for some old apps which can't be ported
to gtk3/gir for some reason. The approach here is to
render to a GEGL Buffer, and pass its pixel
data directly to a gtk2 drawable.
"""

G = gegl.gegl._gegl
SIZE = 640,480

def create_window():
    window = gtk.Window()
    window.show()
    box = gtk.VBox()
    window.add(box)
    box.show()
    canvas = gtk.DrawingArea()
    canvas.set_size_request(*SIZE)
    box.pack_start(canvas)
    canvas.show()
    canvas.set_double_buffered(False)
    drawable = canvas.window
    button = gtk.Button("Ok")
    box.pack_start(button)
    button.show()
    return window, canvas, drawable

def create_graph(bg=(1,.5,0)):
    graph = gegl.Graph("color", "over", "crop", "write-buffer")
    graph[0].value=bg
    graph[2].width=SIZE[0]
    graph[2].height=SIZE[1]
    graph[3].buffer = gegl.Buffer(SIZE)
    return graph


def blit(drawable, buffer):
    gc = drawable.new_gc()
    rect = buffer.get_extent()
    x, y, width, height = rect.as_sequence()
    data = buffer.get()
    drawable.draw_rgb_32_image(gc, x, y, width, height, 0,
                               data, rowstride=-1, xdith=0, ydith=0)


def update(drawable, graph, canvas):
    print "Hola!"
    graph()
    blit(drawable, graph[-1].buffer)
    #canvas.show()

window, canvas, drawable = create_window()
graph = create_graph()

# if trying this in Python interactive mode, just call:
#update(drawable, graph)

canvas.connect("expose-event", lambda *a: update(drawable, graph, canvas))

gtk.mainloop()
