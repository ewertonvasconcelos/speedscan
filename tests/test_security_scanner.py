import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.security_scanner import SecurityScanner

class TestSecurityScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = SecurityScanner('Linux')

    @patch('core.security_scanner.subprocess.run')
    def test_scan_open_ports_linux_ss(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout='Netid  State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port\n'
                   'tcp    LISTEN  0       128     0.0.0.0:22            0.0.0.0:*\n',
            returncode=0
        )
        ports = self.scanner.scan_open_ports()
        self.assertIn('0.0.0.0:22', ports)

    @patch('core.security_scanner.subprocess.run')
    def test_scan_open_ports_linux_netstat_fallback(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=1),
            MagicMock(stdout='tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN', returncode=0)
        ]
        ports = self.scanner.scan_open_ports()
        self.assertIn('0.0.0.0:22', ports)

    @patch('core.security_scanner.subprocess.run')
    def test_scan_open_ports_windows(self, mock_run):
        self.scanner.so = 'Windows'
        mock_run.return_value = MagicMock(
            stdout='  TCP    0.0.0.0:22            0.0.0.0:0              LISTENING',
            returncode=0
        )
        ports = self.scanner.scan_open_ports()
        self.assertIn('0.0.0.0:22', ports)

    @patch('core.security_scanner.subprocess.run')
    def test_check_firewall_status_linux_ufw(self, mock_run):
        mock_run.return_value = MagicMock(stdout='Status: active', returncode=0)
        status = self.scanner.check_firewall_status()
        self.assertIn('active', status)

    @patch('core.security_scanner.subprocess.run')
    def test_check_firewall_status_linux_iptables(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=1),
            MagicMock(stdout='Chain INPUT (policy ACCEPT)', returncode=0)
        ]
        status = self.scanner.check_firewall_status()
        self.assertIn('iptables', status)

    @patch('core.security_scanner.subprocess.run')
    def test_check_security_updates_linux_apt(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout='linux-image/upgradable 5.15.0-91-generic amd64 [upgradable from: 5.15.0-86-generic]',
            returncode=0
        )
        updates = self.scanner.check_security_updates()
        self.assertGreater(len(updates), 0)
        self.assertIn('linux-image', updates[0])

if __name__ == '__main__':
    unittest.main()
