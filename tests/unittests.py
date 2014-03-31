import random
import unittest
import gegl


class TestNodes(unittest.TestCase):
    def test_is_available(self):
        print (dir(gegl), gegl.__file__)
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


class TestGraph(unittest.TestCase):

    def test_can_instantiate_from_string(self):
        graph = gegl.Graph()
        self.assertIsInstance(graph, gegl.Graph)
        self.assertTrue(graph._node) 
   
    def test_instantiate_with_nodes_from_string(self):
        graph = gegl.Graph("png-load", "invert-linear")
        self.assertEqual(graph[0].operation, "gegl:png-load")
        self.assertEqual(graph[1].operation, "gegl:invert-linear") 
    
    def test_add_nodes(self):
        graph = gegl.Graph()
        graph.append("png-load")
        self.assertIsInstance(graph[0], gegl.OpNode)

    def test_add_nodes_from_nodes(self):
        graph = gegl.Graph()
        node = gegl.OpNode("gegl:png-load")
        graph.append(node)
        self.assertIsInstance(graph[0], gegl.OpNode)

if __name__ == "__main__":
    unittest.main()