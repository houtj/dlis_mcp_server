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

        # Test that the output contains expected metadata sections
        expected_sections = [
            'fileheader:',
            'channels:',
            'frames:',
            'parameters:',
            'tools:'
        ]
        for section in expected_sections:
            self.assertIn(section, meta)

        # Test that the metadata has the expected hierarchical structure
        self.assertIn('\t', meta)  # Check for indentation
        self.assertIn('\t\t', meta)  # Check for nested indentation
        self.assertIn('\t\t\t', meta)  # Check for deeply nested indentation

if __name__ == '__main__':
    unittest.main() 