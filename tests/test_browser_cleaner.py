import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.browser_cleaner import BrowserCleaner

class TestBrowserCleanerExtended(unittest.TestCase):
    def setUp(self):
        self.bc = BrowserCleaner()

    def test_format_bytes(self):
        self.assertEqual(self.bc.format_bytes(500), '500.0 B')
        self.assertEqual(self.bc.format_bytes(1500), '1.5 KB')
        self.assertEqual(self.bc.format_bytes(1500000), '1.4 MB')
        self.assertEqual(self.bc.format_bytes(1500000000), '1.4 GB')

    @patch('core.browser_cleaner.Path.exists')
    @patch('core.browser_cleaner.os.walk')
    @patch('core.browser_cleaner.Path.stat')
    def test_get_size_directory(self, mock_stat, mock_walk, mock_exists):
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('/fake', [], ['file1', 'file2']),
            ('/fake/sub', [], ['file3'])
        ]
        mock_stat.return_value.st_size = 1000
        size = self.bc.get_size(Path('/fake'))
        self.assertEqual(size, 3000)

    @patch('core.browser_cleaner.shutil.rmtree')
    @patch('core.browser_cleaner.Path.exists')
    @patch('core.browser_cleaner.Path.is_dir')
    def test_clean_browser_cache(self, mock_is_dir, mock_exists, mock_rmtree):
        browser_data = {
            'name': 'Chrome',
            'cache': Path('/fake/chrome/cache'),
            'cookies': Path('/fake/chrome/cookies'),
            'history': Path('/fake/chrome/history')
        }
        self.bc.browsers['chrome'] = browser_data
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        result = self.bc.clean_browser('chrome', preserve_cookies=False)
        self.assertEqual(result['name'], 'Chrome')
        self.assertGreaterEqual(result['cache_freed'], 0)
        mock_rmtree.assert_called_once_with(browser_data['cache'])

    @patch('core.browser_cleaner.shutil.rmtree')
    @patch('core.browser_cleaner.Path.exists')
    @patch('core.browser_cleaner.Path.is_dir')
    def test_clean_browser_preserve_cookies(self, mock_is_dir, mock_exists, mock_rmtree):
        browser_data = {
            'name': 'Chrome',
            'cache': Path('/fake/chrome/cache'),
            'cookies': Path('/fake/chrome/cookies'),
            'history': Path('/fake/chrome/history')
        }
        self.bc.browsers['chrome'] = browser_data
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        result = self.bc.clean_browser('chrome', preserve_cookies=True)
        self.assertEqual(result['name'], 'Chrome')
        mock_rmtree.assert_called_once_with(browser_data['cache'])

if __name__ == '__main__':
    unittest.main()
