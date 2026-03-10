import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.temperature_monitor import TemperatureMonitor

class TestTemperatureMonitorExtended(unittest.TestCase):
    def setUp(self):
        self.tm = TemperatureMonitor()

    @patch('core.temperature_monitor.psutil')
    def test_get_cpu_temperatures_via_psutil(self, mock_psutil):
        mock_sensors = {
            'coretemp': [
                MagicMock(current=45.0, label='Core 0'),
                MagicMock(current=50.0, label='Core 1')
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_sensors
        temps = self.tm.get_cpu_temperatures()
        self.assertIn('CPU Core 0', temps)
        self.assertIn('CPU Core 1', temps)
        self.assertEqual(temps['CPU Core 0'], 45.0)
        self.assertEqual(temps['CPU Core 1'], 50.0)

    @patch('core.temperature_monitor.psutil')
    @patch('builtins.open', new_callable=mock_open, read_data='45000')
    def test_get_cpu_temperatures_fallback(self, mock_file, mock_psutil):
        mock_psutil.sensors_temperatures.return_value = {}
        temps = self.tm.get_cpu_temperatures()
        self.assertIn('CPU', temps)
        self.assertEqual(temps['CPU'], 45.0)

    @patch('core.temperature_monitor.subprocess.run')
    def test_get_gpu_temperatures_nvidia(self, mock_run):
        mock_run.return_value = MagicMock(stdout='45\n', returncode=0)
        temps = self.tm.get_gpu_temperatures()
        self.assertIn('GPU 0', temps)
        self.assertEqual(temps['GPU 0'], 45.0)

    @patch('core.temperature_monitor.subprocess.run')
    def test_get_gpu_temperatures_no_nvidia(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        temps = self.tm.get_gpu_temperatures()
        self.assertEqual(temps, {})

    @patch('core.temperature_monitor.subprocess.run')
    def test_get_disk_temperatures(self, mock_run):
        mock_lsblk = MagicMock(stdout='NAME\nsda\n')
        mock_smart = MagicMock(stdout='194 Temperature_Celsius     0x0022   040   040   000    Old_age   Always       -       40')
        mock_run.side_effect = [mock_lsblk, mock_smart]
        temps = self.tm.get_disk_temperatures()
        self.assertIn('Disk sda', temps)
        self.assertEqual(temps['Disk sda'], 40.0)

if __name__ == '__main__':
    unittest.main()
