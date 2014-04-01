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

    def test_node_has_pad(self):
        node = gegl.OpNode("over")
        self.assertTrue(node.has_pad("input"))
        self.assertTrue(node.has_pad("output"))
        self.assertTrue(node.has_pad("aux"))
        node = gegl.OpNode("color")
        self.assertFalse(node.has_pad("input"))




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
        self.assertEqual(graph.to_xml().split(), expected)


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


class TestGraphConnections(unittest.TestCase):

    def test_graph_connects_as_aux(self):
        g1 = gegl.Graph("color", "over", "crop", "sdl-display")
        g2 = gegl.Graph("grid", "rotate")
        g2.plug_as_aux(g1[1])  # "over"  node
        self.assertIs(g1[1]._node.get_producer("aux", None), g2[-1]._node)


if __name__ == "__main__":
    unittest.main()