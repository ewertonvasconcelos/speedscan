#!/usr/bin/env python3
import subprocess
def send_notification(t,m,i='dialog-info',to=5000):
    try:
        r=subprocess.run(['dbus-send','--session','--dest=org.freedesktop.Notifications','/org/freedesktop/notifications','org.freedesktop.Notifications.Notify','string:SpeedScan','uint32:0',f'string:{i}',f'string:{t}',f'string:{m}','array:string:',f'int32:{to}'],capture_output=True,text=True)
        return r.returncode==0
    except Exception as e: print(f"Notify failed: {e}"); return False
send_success=lambda m="OK":send_notification("SpeedScan",m,'emblem-ok')
send_error=lambda m="Error":send_notification("SpeedScan",m,'dialog-error')
send_warning=lambda m="Warning":send_notification("SpeedScan",m,'dialog-warning')
