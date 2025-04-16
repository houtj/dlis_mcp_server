import unittest
from dlis_server import DLISAnalyzer
import os

class TestDLISAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sample_file = '/home/houtj/projects/dlis_mcp_server/sample/sample xpt 1.DLIS'
        self.analyzer = DLISAnalyzer(self.sample_file)
        # Load the file before testing
        self.analyzer.load_file()

    def test_get_meta(self):
        # Test that get_meta returns a non-empty string
        meta = self.analyzer.get_meta()
        self.assertIsInstance(meta, str)
        self.assertTrue(len(meta) > 0)

    def test_extract_channels(self):
        # Test that extract_channels returns a non-empty string
        output_path = self.analyzer.extract_channels()
        self.assertIsInstance(output_path, str)
        self.assertTrue(len(output_path) > 0)

if __name__ == '__main__':
    unittest.main() 