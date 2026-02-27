# core/scheduler.py
import os
import subprocess
from pathlib import Path

class Scheduler:
    """Gerencia agendamento de tarefas via crontab (Linux), schtasks (Windows) ou launchd (macOS)."""
    def __init__(self, so, log_dir, agent_script):
        self.so = so
        self.log_dir = log_dir
        self.agent_script = agent_script

    def create_schedule(self, schedule):
        """Cria ou atualiza o agendamento baseado na configuração."""
        if not schedule["enabled"]:
            self.remove_schedule()
            return

        cmd = f"python3 {self.agent_script}"
        if self.so == "Linux":
            self._schedule_linux(schedule, cmd)
        elif self.so == "Windows":
            self._schedule_windows(schedule, cmd)
        elif self.so == "Darwin":
            self._schedule_macos(schedule, cmd)

    def remove_schedule(self):
        """Remove o agendamento."""
        if self.so == "Linux":
            self._remove_crontab()
        elif self.so == "Windows":
            self._remove_schtasks()
        elif self.so == "Darwin":
            self._remove_launchd()

    def _schedule_linux(self, schedule, cmd):
        try:
            current = subprocess.check_output("crontab -l 2>/dev/null", shell=True, text=True)
        except:
            current = ""
        hour, minute = schedule["hour"].split(":")
        if schedule["frequency"] == "daily":
            cron_time = f"{minute} {hour} * * *"
        elif schedule["frequency"] == "weekly":
            day_map = {"monday":1, "tuesday":2, "wednesday":3, "thursday":4, "friday":5, "saturday":6, "sunday":0}
            dow = day_map.get(schedule["day_of_week"], 1)
            cron_time = f"{minute} {hour} * * {dow}"
        elif schedule["frequency"] == "monthly":
            day = schedule["day_of_month"]
            cron_time = f"{minute} {hour} {day} * *"
        else:  # custom
            cron_time = f"{minute} {hour} * * *"  # simplificado; idealmente usaria intervalo
        full_cmd = f"{cmd} >> {self.log_dir}/schedule.log 2>&1"
        new_lines = [line for line in current.splitlines() if "speedscan-agent.py" not in line]
        new_lines.append(f"{cron_time} {full_cmd}")
        tmp = "/tmp/speedscan_cron"
        with open(tmp, "w") as f:
            f.write("\n".join(new_lines) + "\n")
        subprocess.run(f"crontab {tmp}", shell=True)
        os.unlink(tmp)

    def _remove_crontab(self):
        try:
            current = subprocess.check_output("crontab -l 2>/dev/null", shell=True, text=True)
            new_lines = [line for line in current.splitlines() if "speedscan-agent.py" not in line]
            tmp = "/tmp/speedscan_cron"
            with open(tmp, "w") as f:
                f.write("\n".join(new_lines) + "\n")
            subprocess.run(f"crontab {tmp}", shell=True)
            os.unlink(tmp)
        except:
            pass

    def _schedule_windows(self, schedule, cmd):
        task_name = "SpeedScanAgent"
        hour, minute = schedule["hour"].split(":")
        if schedule["frequency"] == "daily":
            schtask = f'schtasks /create /tn "{task_name}" /tr "{cmd}" /sc daily /st {hour}:{minute} /f'
        elif schedule["frequency"] == "weekly":
            day_map = {"monday":"MON", "tuesday":"TUE", "wednesday":"WED", "thursday":"THU", "friday":"FRI", "saturday":"SAT", "sunday":"SUN"}
            dow = day_map.get(schedule["day_of_week"], "MON")
            schtask = f'schtasks /create /tn "{task_name}" /tr "{cmd}" /sc weekly /d {dow} /st {hour}:{minute} /f'
        elif schedule["frequency"] == "monthly":
            day = schedule["day_of_month"]
            schtask = f'schtasks /create /tn "{task_name}" /tr "{cmd}" /sc monthly /d {day} /st {hour}:{minute} /f'
        else:
            return
        if schedule["elevated"]:
            schtask += " /ru SYSTEM"
        subprocess.run(schtask, shell=True)

    def _remove_schtasks(self):
        subprocess.run('schtasks /delete /tn "SpeedScanAgent" /f', shell=True)

    def _schedule_macos(self, schedule, cmd):
        plist_path = Path.home() / "Library/LaunchAgents/org.speedscan.agent.plist"
        hour, minute = schedule["hour"].split(":")
        import plistlib
        plist = {"Label": "org.speedscan.agent", "ProgramArguments": ["/bin/bash", "-c", cmd], "StartCalendarInterval": []}
        if schedule["frequency"] == "daily":
            plist["StartCalendarInterval"] = {"Hour": int(hour), "Minute": int(minute)}
        elif schedule["frequency"] == "weekly":
            day_map = {"monday":1, "tuesday":2, "wednesday":3, "thursday":4, "friday":5, "saturday":6, "sunday":0}
            dow = day_map.get(schedule["day_of_week"], 1)
            plist["StartCalendarInterval"] = {"Weekday": dow, "Hour": int(hour), "Minute": int(minute)}
        elif schedule["frequency"] == "monthly":
            plist["StartCalendarInterval"] = {"Day": schedule["day_of_month"], "Hour": int(hour), "Minute": int(minute)}
        else:
            return
        with open(plist_path, "wb") as f:
            plistlib.dump(plist, f)
        subprocess.run(f"launchctl load {plist_path}", shell=True)

    def _remove_launchd(self):
        plist_path = Path.home() / "Library/LaunchAgents/org.speedscan.agent.plist"
        subprocess.run(f"launchctl unload {plist_path}", shell=True)
        if plist_path.exists():
            plist_path.unlink()
