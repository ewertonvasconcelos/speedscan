import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.actions import CommandRunner, ActionMapper, ActionHandler

class TestCommandRunner(unittest.TestCase):
    def setUp(self):
        self.runner = CommandRunner('Linux')

    @patch('core.actions.subprocess.Popen')
    def test_run_command_without_sudo(self, mock_popen):
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        proc = self.runner.run('echo test', use_sudo=False)
        mock_popen.assert_called_once()
        self.assertEqual(proc, mock_proc)

    @patch('core.actions.subprocess.Popen')
    def test_run_command_with_sudo_linux(self, mock_popen):
        self.runner.so = 'Linux'
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        proc = self.runner.run('apt update', use_sudo=True)
        args, kwargs = mock_popen.call_args
        self.assertIn('pkexec', args[0])
        self.assertEqual(proc, mock_proc)

    @patch('core.actions.subprocess.Popen')
    def test_run_command_with_sudo_windows(self, mock_popen):
        self.runner.so = 'Windows'
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        proc = self.runner.run('some_command', use_sudo=True)
        args, kwargs = mock_popen.call_args
        self.assertIn('runas', args[0])
        self.assertEqual(proc, mock_proc)

class TestActionMapper(unittest.TestCase):
    def setUp(self):
        self.runner = MagicMock()
        self.mapper = ActionMapper('Linux', self.runner)

    def test_get_command_existing(self):
        cmd = self.mapper.get_command('cache')
        self.assertIsNotNone(cmd)
        self.assertIn('sudo', cmd)

    def test_get_command_non_existing(self):
        cmd = self.mapper.get_command('non_existent_action')
        self.assertIsNone(cmd)

    def test_dns_command_linux(self):
        cmd = self.mapper.dns_command('8.8.8.8')
        self.assertIn('8.8.8.8', cmd)
        self.assertIn('tee', cmd)

    def test_dns_command_windows(self):
        self.mapper.so = 'Windows'
        cmd = self.mapper.dns_command('8.8.8.8')
        self.assertIn('8.8.8.8', cmd)
        self.assertIn('netsh', cmd)

class TestActionHandler(unittest.TestCase):
    def setUp(self):
        self.mock_app = MagicMock()
        self.mock_app.SO = 'Linux'
        self.mock_app.runner = MagicMock()
        self.handler = ActionHandler(self.mock_app)

    @patch('core.actions.ActionHandler._run_linux_command')
    def test_run_cache_clean(self, mock_run):
        log_mock = MagicMock()
        self.handler.run_cache_clean(log_mock)
        mock_run.assert_called_once()

    @patch('core.actions.ActionHandler._run_linux_command')
    def test_run_swap_reset(self, mock_run):
        log_mock = MagicMock()
        self.handler.run_swap_reset(log_mock)
        self.assertEqual(mock_run.call_count, 2)

if __name__ == '__main__':
    unittest.main()
