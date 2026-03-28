"""
NOSTROMO Settings Screen.
System info, WiFi and Bluetooth configuration.
"""

import os
import subprocess
import threading
import pygame

from nostromo.screen import Screen
from nostromo.terminal import BaseTerminal
from nostromo import config as cfg


BOOT_LINES = [
    "",
    "  WEYLAND-YUTANI CORP.",
    "  SYSTEM CONFIGURATION v1.0",
    "",
    "  DIAGNOSTICS ...... ONLINE",
    "  NETWORK CONTROL .. ONLINE",
    "  WIRELESS MGMT .... ONLINE",
    "",
]


def _run(cmd, timeout=5):
    """Run a shell command, return stdout or error string.
    Uses DEVNULL for stdin to prevent interactive hangs.
    Uses start_new_session so timeout can kill process group.
    """
    try:
        r = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        return f"ERROR: {e}"


def _get_system_info():
    """Gather system info lines."""
    lines = []

    hostname = _run("hostname")
    lines.append(f"  HOSTNAME: {hostname}")

    ips = _run("hostname -I")
    if ips:
        for ip in ips.split():
            lines.append(f"  IP: {ip}")
    else:
        lines.append("  IP: NOT CONNECTED")

    temp = _run("vcgencmd measure_temp")
    if temp:
        lines.append(f"  CPU {temp.upper()}")

    freq = _run("vcgencmd measure_clock arm")
    if "=" in freq:
        mhz = int(freq.split("=")[1]) // 1000000
        lines.append(f"  CPU FREQ: {mhz} MHZ")

    throttle = _run("vcgencmd get_throttled")
    if throttle:
        lines.append(f"  {throttle.upper()}")

    mem = _run("free -m | awk 'NR==2{printf \"%s/%sMB (%.0f%%)\", $3,$2,$3*100/$2}'")
    if mem:
        lines.append(f"  RAM: {mem}")

    disk = _run("df -h / | awk 'NR==2{printf \"%s/%s (%s)\", $3,$2,$5}'")
    if disk:
        lines.append(f"  DISK: {disk}")

    uptime = _run("uptime -p")
    if uptime:
        lines.append(f"  {uptime.upper()}")

    vcore = _run("vcgencmd pmic_read_adc EXT5V_V 2>/dev/null | awk -F= '{print $2}'")
    if vcore and vcore[0].isdigit():
        lines.append(f"  EXT5V: {vcore}")

    return lines


def _get_wifi_info():
    """Get WiFi status."""
    lines = []

    ssid = _run("iwgetid -r")
    if ssid:
        lines.append(f"  CONNECTED: {ssid}")
        signal = _run("iwconfig wlan0 2>/dev/null | grep -oP 'Signal level=\\K[^ ]+'")
        if signal:
            lines.append(f"  SIGNAL: {signal}")
        ip = _run("ip -4 addr show wlan0 | grep -oP 'inet \\K[^/]+'")
        if ip:
            lines.append(f"  IP: {ip}")
    else:
        lines.append("  WIFI: NOT CONNECTED")

    blocked = _run("rfkill list wifi | grep -i 'Soft blocked: yes'")
    if blocked:
        lines.append("  WIFI: SOFT BLOCKED (DISABLED)")

    return lines


def _get_wifi_networks():
    """Scan for available WiFi networks."""
    raw = _run("nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list 2>/dev/null", timeout=15)
    if not raw or raw.startswith("ERROR"):
        raw = _run("sudo iwlist wlan0 scan 2>/dev/null | grep ESSID | sed 's/.*ESSID:\"//;s/\"//'")
        if raw:
            return [(ssid, "", "") for ssid in raw.split("\n") if ssid]
        return []

    networks = []
    seen = set()
    for line in raw.split("\n"):
        parts = line.split(":")
        if len(parts) >= 3 and parts[0] and parts[0] not in seen:
            seen.add(parts[0])
            networks.append((parts[0], parts[1], parts[2]))
    return sorted(networks, key=lambda x: int(x[1]) if x[1].isdigit() else 0, reverse=True)


def _bt_cmd(cmd, timeout=3):
    """Run a single bluetoothctl command non-interactively."""
    full = f"echo '{cmd}' | bluetoothctl 2>/dev/null"
    return _run(full, timeout=timeout)


def _get_bt_info():
    """Get Bluetooth status and paired devices."""
    lines = []

    raw = _bt_cmd("show")
    powered = "ON" if "Powered: yes" in raw else "OFF"
    lines.append(f"  BLUETOOTH: {powered}")

    paired = _run("bluetoothctl devices Paired", timeout=3)
    if paired and not paired.startswith("ERROR"):
        lines.append("")
        lines.append("  PAIRED DEVICES:")
        for line in paired.split("\n"):
            if line.strip():
                parts = line.strip().split(" ", 2)
                if len(parts) >= 3:
                    mac = parts[1]
                    name = parts[2]
                    info = _bt_cmd(f"info {mac}")
                    connected = "[*]" if "Connected: yes" in info else "[ ]"
                    bat_str = ""
                    for il in info.split("\n"):
                        if "Battery" in il and "%" in il:
                            import re
                            m = re.search(r'(\d+)', il.split("Battery")[-1])
                            if m:
                                bat_str = f" {m.group(1)}%"
                    lines.append(f"  {connected} {name}{bat_str}")
                    lines.append(f"      {mac}")
    else:
        lines.append("  NO PAIRED DEVICES")

    return lines


class SettingsTerminal(BaseTerminal):
    """Interactive settings menu terminal."""

    STATE_MAIN = "main"
    STATE_SYSINFO = "sysinfo"
    STATE_WIFI = "wifi"
    STATE_WIFI_SCAN = "wifi_scan"
    STATE_WIFI_PASS = "wifi_pass"
    STATE_BT = "bt"
    STATE_BT_SCAN = "bt_scan"
    STATE_VIDEO = "video"

    def __init__(self, renderer):
        super().__init__(renderer, boot_lines=BOOT_LINES, prompt="CMD> ")
        self.state = self.STATE_MAIN
        self._worker = None
        self._worker_result = None
        self._worker_task = None
        self._wifi_networks = []
        self._selected_ssid = None

    def on_boot_complete(self):
        self._show_main_menu()

    def _show_main_menu(self):
        self.state = self.STATE_MAIN
        self.add_line("  +------------------------------+")
        self.add_line("  |   NOSTROMO SYSTEM CONFIG     |")
        self.add_line("  +------------------------------+")
        self.add_line("  |  1. SYSTEM INFO              |")
        self.add_line("  |  2. WIFI                     |")
        self.add_line("  |  3. BLUETOOTH                |")
        self.add_line("  |  4. VIDEO                    |")
        self.add_line("  |                              |")
        self.add_line("  |  0. REFRESH                  |")
        self.add_line("  +------------------------------+")
        self.add_line("")

    def _show_wifi_menu(self):
        self.state = self.STATE_WIFI
        self.add_line("  +------------------------------+")
        self.add_line("  |   WIFI CONFIGURATION         |")
        self.add_line("  +------------------------------+")
        self.add_line("  |  1. STATUS                   |")
        self.add_line("  |  2. SCAN NETWORKS            |")
        self.add_line("  |  3. DISCONNECT               |")
        self.add_line("  |  4. ENABLE WIFI              |")
        self.add_line("  |  5. DISABLE WIFI             |")
        self.add_line("  |                              |")
        self.add_line("  |  0. BACK                     |")
        self.add_line("  +------------------------------+")
        self.add_line("")

    def _show_bt_menu(self):
        self.state = self.STATE_BT
        self.add_line("  +------------------------------+")
        self.add_line("  |   BLUETOOTH CONFIGURATION    |")
        self.add_line("  +------------------------------+")
        self.add_line("  |  1. STATUS & DEVICES         |")
        self.add_line("  |  2. SCAN FOR DEVICES         |")
        self.add_line("  |  3. ENABLE BLUETOOTH         |")
        self.add_line("  |  4. DISABLE BLUETOOTH        |")
        self.add_line("  |                              |")
        self.add_line("  |  0. BACK                     |")
        self.add_line("  +------------------------------+")
        self.add_line("")

    def on_submit(self, query):
        q = query.strip().upper()

        if self.state == self.STATE_MAIN:
            self._handle_main(q)
        elif self.state == self.STATE_WIFI:
            self._handle_wifi(q)
        elif self.state == self.STATE_WIFI_SCAN:
            self._handle_wifi_scan(q)
        elif self.state == self.STATE_WIFI_PASS:
            self._handle_wifi_pass(query.strip())
        elif self.state == self.STATE_BT:
            self._handle_bt(q)
        elif self.state == self.STATE_BT_SCAN:
            self._handle_bt_scan(q)
        elif self.state == self.STATE_VIDEO:
            self._handle_video(q)
        elif self.state == self.STATE_SYSINFO:
            self._show_main_menu()

    def _handle_main(self, q):
        if q == "1":
            self._start_worker("sysinfo", _get_system_info)
        elif q == "2":
            self._show_wifi_menu()
        elif q == "3":
            self._show_bt_menu()
        elif q == "4":
            self._show_video_menu()
        elif q == "0":
            self._show_main_menu()
        else:
            self.add_line("  INVALID OPTION")
            self.add_line("")

    def _handle_wifi(self, q):
        if q == "1":
            self._start_worker("wifi_status", _get_wifi_info)
        elif q == "2":
            self._start_worker("wifi_scan", _get_wifi_networks)
        elif q == "3":
            self._start_worker("wifi_disconnect",
                               lambda: [f"  {_run('nmcli dev disconnect wlan0 2>/dev/null || echo NOT CONNECTED')}"])
        elif q == "4":
            self._start_worker("wifi_enable",
                               lambda: [f"  {_run('nmcli radio wifi on && echo WIFI ENABLED')}"])
        elif q == "5":
            self._start_worker("wifi_disable",
                               lambda: [f"  {_run('nmcli radio wifi off && echo WIFI DISABLED')}"])
        elif q == "0":
            self._show_main_menu()
        else:
            self.add_line("  INVALID OPTION")
            self.add_line("")

    def _handle_wifi_scan(self, q):
        if q == "0":
            self._show_wifi_menu()
            return
        if q.isdigit():
            idx = int(q) - 1
            if 0 <= idx < len(self._wifi_networks):
                ssid, sig, sec = self._wifi_networks[idx]
                self._selected_ssid = ssid
                if sec and sec != "--":
                    self.add_line(f"  CONNECT TO: {ssid}")
                    self.add_line("  ENTER PASSWORD (CASE-SENSITIVE):")
                    self.add_line("")
                    self.state = self.STATE_WIFI_PASS
                    self.prompt = "PASS> "
                else:
                    self._start_worker("wifi_connect",
                                       lambda s=ssid: [f"  {_run(f'nmcli dev wifi connect \"{s}\"')}"])
                return
        self.add_line("  INVALID SELECTION")
        self.add_line("")

    def _handle_wifi_pass(self, password):
        ssid = self._selected_ssid
        self.prompt = "CMD> "
        self._start_worker("wifi_connect",
                           lambda s=ssid, p=password: [f"  {_run(f'nmcli dev wifi connect \"{s}\" password \"{p}\"')}"])

    def _handle_bt(self, q):
        if q == "1":
            self._start_worker("bt_status", _get_bt_info)
        elif q == "2":
            self._start_worker("bt_scan", self._do_bt_scan)
        elif q == "3":
            self._start_worker("bt_enable",
                               lambda: [f"  {_bt_cmd('power on')}",
                                        "  BLUETOOTH ENABLED"])
        elif q == "4":
            self._start_worker("bt_disable",
                               lambda: [f"  {_bt_cmd('power off')}",
                                        "  BLUETOOTH DISABLED"])
        elif q == "0":
            self._show_main_menu()
        else:
            self.add_line("  INVALID OPTION")
            self.add_line("")

    def _handle_bt_scan(self, q):
        if q == "0":
            _bt_cmd("scan off")
            self._show_bt_menu()
            return
        self.add_line("  SCAN COMPLETE. 0 TO GO BACK.")
        self.add_line("")

    def _do_bt_scan(self):
        """Scan for BT devices using non-interactive bluetoothctl."""
        _run("timeout 6 bash -c 'echo \"scan on\" | bluetoothctl >/dev/null 2>&1'", timeout=8)
        _bt_cmd("scan off")

        raw = _run("bluetoothctl devices", timeout=3)
        lines = ["", "  DISCOVERED DEVICES:"]
        if raw and not raw.startswith("ERROR"):
            for line in raw.split("\n"):
                parts = line.strip().split(" ", 2)
                if len(parts) >= 3:
                    lines.append(f"  {parts[2]}")
                    lines.append(f"      {parts[1]}")
        else:
            lines.append("  NO DEVICES FOUND")
        lines.append("")
        lines.append("  0. BACK")
        lines.append("")
        return lines

    def _show_video_menu(self):
        self.state = self.STATE_VIDEO
        current = cfg.VIDEO_SCALE.upper()
        self.add_line("  +------------------------------+")
        self.add_line("  |   VIDEO SETTINGS             |")
        self.add_line("  +------------------------------+")
        self.add_line(f"  |  SCALE MODE: {current:<16s}|")
        self.add_line("  |                              |")
        self.add_line("  |  1. FILL (CROP EDGES)        |")
        self.add_line("  |  2. FIT  (BLACK BARS)        |")
        self.add_line("  |                              |")
        self.add_line("  |  0. BACK                     |")
        self.add_line("  +------------------------------+")
        self.add_line("")

    def _handle_video(self, q):
        if q == "1":
            cfg.VIDEO_SCALE = "fill"
            self.add_line("  SCALE MODE: FILL")
            self.add_line("")
        elif q == "2":
            cfg.VIDEO_SCALE = "fit"
            self.add_line("  SCALE MODE: FIT")
            self.add_line("")
        elif q == "0":
            self._show_main_menu()
            return
        else:
            self.add_line("  INVALID OPTION")
            self.add_line("")

    def _start_worker(self, task_name, func):
        self.set_busy(True)
        self._working_dots = 0
        self._last_dot_time = pygame.time.get_ticks()
        self._worker_result = None
        self._worker_task = task_name
        self._worker = threading.Thread(
            target=self._run_worker, args=(func,), daemon=True
        )
        self._worker.start()

    def _run_worker(self, func):
        try:
            self._worker_result = func()
        except Exception as e:
            self._worker_result = [f"  ERROR: {e}"]

    def update(self):
        super().update()
        if self._worker and not self._worker.is_alive():
            self._worker = None
            self.set_busy(False)
            result = self._worker_result
            task = self._worker_task

            if task == "wifi_scan" and isinstance(result, list) and result and isinstance(result[0], tuple):
                self._wifi_networks = result
                self.state = self.STATE_WIFI_SCAN
                self.add_line(f"  FOUND {len(result)} NETWORKS:")
                self.add_line("")
                for i, (ssid, sig, sec) in enumerate(result):
                    sec_str = f" [{sec}]" if sec and sec != "--" else " [OPEN]"
                    sig_str = f" {sig}%" if sig else ""
                    name = ssid[:cfg.COLS - 20]
                    self.add_line(f"  {i+1:2d}. {name}{sig_str}{sec_str}")
                self.add_line("")
                self.add_line("  ENTER NUMBER TO CONNECT  [0] BACK")
                self.add_line("")
            elif task == "bt_scan":
                self.state = self.STATE_BT_SCAN
                if isinstance(result, list):
                    for line in result:
                        self.add_line(line)
            elif task == "sysinfo":
                self.state = self.STATE_SYSINFO
                if isinstance(result, list):
                    self.add_line("")
                    for line in result:
                        self.add_line(line)
                    self.add_line("")
                    self.add_line("  PRESS ENTER TO GO BACK")
                    self.add_line("")
            else:
                if isinstance(result, list):
                    for line in result:
                        self.add_line(line)
                    self.add_line("")
                    if task.startswith("wifi"):
                        self._show_wifi_menu()
                    elif task.startswith("bt"):
                        self._show_bt_menu()

    def render(self):
        if self._worker:
            r = self.renderer
            visible = self._get_visible_lines(self.output_rows - 1)
            for i, line in enumerate(visible):
                row = self.output_rows - 1 - len(visible) + i
                r.render_text_line(line, row)
            self.show_working()
        else:
            super().render()


class SettingsScreen(Screen):
    """Screen adapter for settings terminal."""

    def __init__(self):
        super().__init__("CONFIG", "C-4")
        self.terminal = None

    def init(self, renderer):
        super().init(renderer)
        self.terminal = SettingsTerminal(renderer)

    def handle_event(self, event):
        if self.terminal and event.type == pygame.KEYDOWN:
            return self.terminal.handle_key(event)
        return False

    def update(self):
        if self.terminal:
            self.terminal.update()

    def render(self):
        if self.terminal:
            self.terminal.render()

    def on_activate(self):
        super().on_activate()

    def cleanup(self):
        pass


def create():
    """Factory function."""
    return SettingsScreen()
