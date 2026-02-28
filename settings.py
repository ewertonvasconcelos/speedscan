# settings.py
import os
app_path = 'dist/SpeedScan.app'
volume_name = 'SpeedScan 0.0.9'
format = 'UDBZ'
size = (640, 400)
files = [app_path]
symlinks = {'Applications': '/Applications'}
icon_locations = {
    'SpeedScan.app': (200, 170),
    'Applications': (440, 170)
}

