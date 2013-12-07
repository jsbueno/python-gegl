import gegl


g = gegl.Graph(("rectangle", dict(x=0,y=0,width=480, height=480)),
    ("grid", {"y":3, "line-height":1, "line-width":0}),
    ("rotate", {"degrees":30}),
    "svg:src-over",
    ("crop", dict(x=0,y=0,width=480, height=480)),
    ("png-save", {"path": "stripes.png"}), auto=False)

g[2].connect_to(g[3], input="aux")
g[1] >> g[2]
g[0] >> g[3]
g[3] >> g[4]
g[4] >> g[5]

c = gegl.Color()
c.set_rgba(1,1,1,1)
g[0].color = c

c2 = gegl.Color()
c2.set_rgba(0,1,0,1)
setattr(g[1], "line-color", c2)

g()

