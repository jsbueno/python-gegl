import gegl


g = gegl.Graph(("rectangle", dict(x=0,y=0,width=480, height=480, color=gegl.Color(1,1,1) )),
    ("grid", {"y":3, "line-height":1, "line-width":0, "line-color": gegl.Color(.7,0.3,.0)}),
    ("rotate", {"degrees":-30}),
    "svg:src-over",
    ("crop", dict(x=0,y=0,width=480, height=480)),
    ("png-save", {"path": "stripes.png"}), auto=False)

g[0] >> g[3]
g[1] >> g[2]
g[2].connect_to(g[3], "aux")
g[3] >> g[4] >> g[5]


g()

