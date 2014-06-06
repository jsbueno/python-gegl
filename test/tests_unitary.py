import random
import unittest
import gegl


class TestNodes(unittest.TestCase):
    def test_is_available(self):
        self.assertTrue (gegl.gegl._gegl, "GEGL GIR not loaded")

    def test_can_instantiate_from_string(self):
        node = gegl.OpNode("gegl:nop")
        self.assertIsInstance(node, gegl.OpNode)

    def test_can_instantiate_from_gegl_native_node(self):
        raw_node = gegl.gegl._gegl.Node()
        raw_node.set_property("operation", "gegl:nop")
        node = gegl.OpNode._from_raw_node(raw_node)
        self.assertIsInstance(node, gegl.OpNode)
        self.assertEqual(node.operation, "gegl:nop")

    def test_default_namespace(self):
        node = gegl.OpNode("nop")
        self.assertIsInstance(node, gegl.OpNode)
        self.assertEqual(node.operation, "gegl:nop")

    def test_pass_properties_as_parameters(self):
        node = gegl.OpNode("png-load", path="here.png")
        self.assertEqual(node.path, "here.png")

    def test_properties_as_attributes(self):
        node = gegl.OpNode("png-load")
        self.assertEqual(node.properties, {"path"})
        self.assertEqual(node.path, "")
        self.assertRaises(ValueError, node.__setattr__, "fnord", "blah")

    def test_properties_as_items(self):
        node = gegl.OpNode("png-load")
        self.assertEqual(node["path"], "")
        node["path"] = "testing.png"
        self.assertEqual(node["path"], "testing.png")
        self.assertRaises(KeyError, node.__setitem__, "fnord", "blah")

    def test_set_color_property_from_Color(self):
        node = gegl.OpNode("color")
        color = gegl.Color(1, 0.5, 1, 1)
        node.value = color
        self.assertEqual(node.value, color)

    def test_set_color_property_from_tuple(self):
        node = gegl.OpNode("color")
        node.value = (1, 0.5, 1, 1)
        self.assertEqual(node.value,gegl.Color(1, 0.5, 1, 1))

    def test_property_list_exists(self):
        node = gegl.OpNode("color")
        self.assertTrue(hasattr(node, "_property_names"))
        self.assertTrue(hasattr(node, "_property_types"))
        self.assertTrue("value" in node._property_types)

    def test_change_operation_change_properties(self):
        node = gegl.OpNode("color")
        self.assertTrue("value" in node._property_types)
        self.assertRaises(ValueError, setattr,   node, 
                          "operation",  "gegl:png-save")

    def test_keys_equal_gegl_properties(self):
        node = gegl.OpNode("color")
        self.assertEqual(sorted(node.keys()), ["format", "value"])

    def test_node_has_pad(self):
        node = gegl.OpNode("over")
        self.assertTrue(node.has_pad("input"))
        self.assertTrue(node.has_pad("output"))
        self.assertTrue(node.has_pad("aux"))
        node = gegl.OpNode("color")
        self.assertFalse(node.has_pad("input"))

    def test_attribute_dash_replacement(self):
        node = gegl.OpNode("grid")
        node.line_width = 0
        self.assertEqual(node["line-width"], 0)

    def test_connect_graph_to_aux_pad_as_property(self):
        g1 = gegl.Graph("color", "over", "crop", "sdl-display")
        g2 = gegl.Graph("grid", "nop")
        g1[1].aux = g2
        self.assertEqual(g1[1].aux, g2)
        self.assertEqual(g1[1]._node.get_producer("aux", None), g2[-1]._node)
        # if this works, "input" also works

    def test_connect_graph_to_output_pad_as_property(self):
        g1 = gegl.Graph("color", "crop")
        g2 = gegl.Graph("nop", "sdl-display")
        g1[1].output = g2
        self.assertEqual(g1[1].output[0], g2)
        self.assertEqual(g2[0]._node.get_producer("input", None), g1[1]._node)
        # get_consumers is broken

    def test_disconnect(self):
        g1 = gegl.Graph("color", "sdl-display")
        g1[1].disconnect()
        self.assertIs(g1[1]._node.get_producer("input", None), None)
        self.assertEqual(g1[1].input, None)
        self.assertEqual(g1[0].output, [])

    def test_disconnect_across_graphs(self):
        g1 = gegl.Graph("color", "crop")
        g2 = gegl.Graph("sdl-display")
        g2[0].input = g1
        self.assertTrue(g2[0]._node.get_producer("input", None))
        g2[0].disconnect()
        self.assertIs(g2[0]._node.get_producer("input", None), None)
        self.assertEqual(g2[0].input, None)
        self.assertEqual(g1[1].output, [])
        
    def test_set_method(self):
        node = gegl.OpNode("crop")
        node.set(width=640, height=480)
        self.assertEqual(node.width, 640)
        self.assertEqual(node.height, 480)

    def test_set_properties_method(self):
        # this is actually aliased to ".set"
        node = gegl.OpNode("crop")
        node.set_properties(width=640, height=480)
        self.assertEqual(node.width, 640)
        self.assertEqual(node.height, 480)

    def test_node_equality(self):
        n1 = gegl.OpNode("grid")
        n2 = gegl.OpNode("grid")
        self.assertIsNot(n1, n2)
        self.assertIsNot(n1._node, n2._node)
        self.assertEqual(n1, n2)
        n1.x = 2
        n2.x = 5
        self.assertNotEqual(n1, n2)


class TestGraph(unittest.TestCase):

    def test_can_instantiate_from_string(self):
        graph = gegl.Graph()
        self.assertIsInstance(graph, gegl.Graph)
        self.assertTrue(graph._node) 

    def test_instantiate_with_nodes_from_string(self):
        graph = gegl.Graph("png-load", "invert-linear")
        self.assertEqual(graph[0].operation, "gegl:png-load")
        self.assertEqual(graph[1].operation, "gegl:invert-linear") 

    def test_instantiate_with_nodes_and_properties(self):
        graph = gegl.Graph(("color", {"value": (0,1,0,1)}),
                                ("crop", [("width", 640), ("height", 480)]),
                                 "sdl-display"
                          )
        self.assertEqual(len(graph), 3)
        self.assertEqual(graph[0].value, (0,1,0,1))
        self.assertEqual(graph[1].width, 640)

    def test_add_nodes(self):
        graph = gegl.Graph()
        graph.append("png-load")
        self.assertIsInstance(graph[0], gegl.OpNode)

    def test_add_nodes_from_nodes(self):
        graph = gegl.Graph()
        node = gegl.OpNode("gegl:png-load")
        graph.append(node)
        self.assertIsInstance(graph[0], gegl.OpNode)

    def test_to_xml(self):
        # the "split" calls are meant to strip all whitespace at once
        expected = """\
        <?xml version='1.0' encoding='UTF-8'?>
        <gegl>
        <node operation='gegl:png-save'>
            <params>
                <param name='path'></param>
                <param name='compression'>1</param>
                <param name='bitdepth'>16</param>
            </params>
        </node>
        <node operation='gegl:invert-linear'>
        </node>
        <node operation='gegl:png-load'>
            <params>
                <param name='path'></param>
            </params>
        </node>
        </gegl>
        """.split()
        graph = gegl.Graph("png-load", "invert", "png-save")
        graph[2].compression = 1
        self.assertEqual(graph.to_xml().split(), expected)

    def test_recursive_representation(self):
        result = "Graph(0:gegl:color, 1:svg:src-over[@0], 2:gegl:crop, " \
        "3:gegl:sdl-display)\n\t0 - Graph(0:gegl:grid, 1:svg:src-over[@1], " \
        "2:svg:src-over[@2])\n\t\t1 - Graph(0:gegl:rectangle, " \
        "1:gegl:rotate)\n\t\t2 - Graph(0:gegl:rectangle)"
        g1 = gegl.Graph("color", "over", "crop", "sdl-display")
        g2 = gegl.Graph("grid", "over", "over")
        g2.plug_as_aux(g1[1])
        g3 = gegl.Graph("rectangle", "rotate")
        g3.plug_as_aux(g2[1])
        g4 = gegl.Graph("rectangle")
        g4.plug_as_aux(g2[2])
        self.assertEqual(repr(g1), result)

    def test_embeded_representation(self):
        g2 = gegl.Graph("crop")
        g1 = gegl.Graph("color", g2, "sdl-display")
        self.assertEqual(repr(g1), 
            "Graph(0:gegl:color, 1:Graph(0:gegl:crop), 2:gegl:sdl-display)")
        

class TestColor(unittest.TestCase):

    def test_default(self):
        color = gegl.Color()
        self.assertEqual(tuple(color), (1.0,1.0,1.0,1.0))

    def test_components_by_name(self):
        color = gegl.Color(0.1, 0.2, 0.3, 0.4)
        self.assertAlmostEqual(color.r, 0.1, delta=1e-5)
        self.assertAlmostEqual(color.g, 0.2, delta=1e-5)
        self.assertAlmostEqual(color.b, 0.3, delta=1e-5)
        self.assertAlmostEqual(color.a, 0.4, delta=1e-5)
    
    def test_creates_from_string(self):
        color = gegl.Color("#00ff00")
        self.assertEqual(color, (0, 1, 0, 1))

    def test_components_by_index(self):
        color = gegl.Color(0.1, 0.2, 0.3, 0.4)
        self.assertAlmostEqual(color[0], 0.1, delta=1e-5)
        self.assertAlmostEqual(color[1], 0.2, delta=1e-5)
        self.assertAlmostEqual(color[2], 0.3, delta=1e-5)
        self.assertAlmostEqual(color[3], 0.4, delta=1e-5)

    def test_build_from_3_tuple(self):
        color = gegl.Color((0, 0, 0))
        self.assertEqual(tuple(color), (0, 0, 0, 1.0))

    def test_build_from_4_tuple(self):
        color = gegl.Color((0, 0, 0, 0))
        self.assertEqual(tuple(color), (0, 0, 0, 0))

    def test_build_from_4_values(self):
        color = gegl.Color(0, 0, 0, 0)
        self.assertEqual(tuple(color), (0, 0, 0, 0))

    def test_compare_equal(self):
        color1 = gegl.Color()
        color2 = gegl.Color()
        self.assertEqual(color1, color2)

    def test_compare_not_equal(self):
        color1 = gegl.Color()
        color2 = gegl.Color(0, .5, 0)
        self.assertNotEqual(color1, color2)

    def test_compare_to_tuple(self):
        color = gegl.Color(0, 0, 0, 1)
        self.assertEqual(color, (0,0,0,1))


class TestRectangle(unittest.TestCase):
    def test_default_parameters(self):
        r = gegl.Rectangle()
        self.assertIsInstance(r, gegl.Rectangle)
        self.assertIsInstance(r.rect, gegl.gegl._gegl.Rectangle)

    def test_explicit_parameters(self):
        r = gegl.Rectangle(10, 10, 30, 30)
        self.assertEqual(r.as_sequence(), (10, 10, 30, 30))

    def test_4_tuple_parameters(self):
        r = gegl.Rectangle((10, 10, 30, 30))
        self.assertEqual(r.as_sequence(), (10, 10, 30, 30))

    def test_2_tuple_parameters(self):
        r = gegl.Rectangle((30, 30))
        self.assertEqual(r.as_sequence(), (0, 0, 30, 30))

    def test_rectangle(self):
        r1 = gegl.Rectangle()
        r2 = gegl.Rectangle(r1)
        self.assertIsNot(r1.rect, r2.rect)
        self.assertEqual(r1.as_sequence(), r2.as_sequence())

    def test_low_level_buffer(self):
        buffer = gegl.Buffer((0,0,320,240))
        r = gegl.Rectangle(buffer.buffer)
        self.assertEqual(r.as_sequence(), (0,0,320,240))

    def test_high_level_buffer(self):
        buffer = gegl.Buffer((0,0,320,240))
        r = gegl.Rectangle(buffer)
        self.assertEqual(r.as_sequence(), (0,0,320,240))

    def test_rectangle_wrap(self):
        low_rect = gegl.gegl._gegl.Rectangle()
        rect = gegl.Rectangle(low_rect)
        self.assertIs(rect.rect, low_rect)

    def test_property_reads(self):
        r = gegl.Rectangle(10,10, 30, 30)
        self.assertEqual(r.x, 10)
        self.assertEqual(r.y, 10)
        self.assertEqual(r.width, 30)
        self.assertEqual(r.height, 30)

class TestBuffer(unittest.TestCase):
    def test_can_instantiate(self):
        buffer = gegl.Buffer((0,0,320,240))
        self.assertIsInstance(buffer.buffer, gegl.gegl._gegl.Buffer)
    
    def test_get_extent(self):
        buffer = gegl.Buffer((0,0,320,240))
        self.assertEqual(buffer.get_extent().as_sequence(), (0,0,320,240))
        
    def test_get_data(self):
        buffer = gegl.Buffer((100,100))
        self.assertEqual(len(buffer.get()), 100 * 100 * 4) 
    
    def test_buffer_wrap(self):
        lbuffer =  gegl.gegl._gegl.Buffer.new("RGBA u8", 0, 0, 10, 10)
        buffer = gegl.Buffer(lbuffer)
        self.assertIs(buffer.buffer, lbuffer)

class TestPath(unittest.TestCase):
    def test_instantiate(self):
        path = gegl.Path()
        self.assertIsInstance(path._path, gegl.gegl._gegl.Path)
    
    def test_instantiate_from_raw_path(self):
        rpath = gegl.gegl._gegl.Path()
        path = gegl.Path(rpath)
        self.assertIs(path._path, rpath)

    def test_instantiate_from_string(self):
        path = gegl.Path("M 0 0 L 100 0")
        self.assertIsInstance(path._path, gegl.gegl._gegl.Path)
        self.assertEqual(path._path.get_n_nodes(), 2)

    def test_instantiate_from_path_node_list(self):
        path = gegl.Path("M 0 0", "L 100 0")
        self.assertEqual(path._path.get_n_nodes(), 2)

    def test_path_attributed_to_node(self):
        path = gegl.Path("M 0 0 L 100 0")
        node= gegl.OpNode("vector-stroke")
        node.d = path
        self.assertIs(node.d._path, path._path)


class TestGraphManipulations(unittest.TestCase):
    def test_append_node(self):
        graph = gegl.Graph("color")
        self.assertEqual(len(graph), 1)
        graph.append("over")
        self.assertEqual(len(graph), 2)
        # low level check
        self.assertIs(graph[1]._node.get_producer("input", None), graph[0]._node)
        # high level check
        self.assertEqual(graph[0].output[0], graph[1])
        self.assertIs(graph[0].output[0]._node, graph[1]._node)
        self.assertEqual(graph[1].input, graph[0])
        self.assertIs(graph[1].input._node, graph[0]._node)

    def test_graph_delitem(self):
        graph = gegl.Graph("color", "over", "crop")
        last_node = graph[-1]
        del graph[1]
        self.assertEqual(len(graph), 2)
        self.assertEqual(len(graph._children), 2)
        self.assertEqual(last_node.input, graph[0])

    def test_graph_delitem_subgraph(self):
        middle = gegl.Graph("over", "over")
        graph = gegl.Graph("color", middle, "crop")
        self.assertEqual(middle[0].input, graph[0])
        self.assertEqual(middle[-1].output[0], graph[2])
        del graph[1]
        self.assertEqual(graph[1].input, graph[0])
        self.assertFalse(middle[0].input)
        self.assertFalse(middle[-1].output)

    def test_graph_insert(self):
        graph = gegl.Graph("color", "sdl-display")
        graph.insert(1, "gegl:crop")
        self.assertEqual(len(graph), 3)
        self.assertEqual(graph[1].operation, "gegl:crop")
        self.assertEqual(graph[1].input, graph[0])
        self.assertEqual(graph[2].input, graph[1])

    def test_graph_insert_subgraph(self):
        graph = gegl.Graph("color", "sdl-display")
        middle = gegl.Graph("over", "crop")
        graph.insert(1, middle)
        self.assertEqual(middle[0].input, graph[0])
        self.assertEqual(graph[2].input, middle[1])

    def test_graf_setitem(self):
        graph = gegl.Graph("color", "nop", "sdl-display")
        graph[1] = "gegl:crop"
        self.assertEqual(graph[1].operation, "gegl:crop")
        self.assertEqual(graph[1].input, graph[0])
        self.assertEqual(graph[2].input, graph[1])

    def test_graph_connects_as_aux(self):
        g1 = gegl.Graph("color", "over", "crop", "sdl-display")
        g2 = gegl.Graph("grid", "rotate")
        g2.plug_as_aux(g1[1])  # "over"  node
        self.assertIs(g1[1]._node.get_producer("aux", None), g2[-1]._node)



if __name__ == "__main__":
    unittest.main()