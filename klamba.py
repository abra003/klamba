#!/usr/bin/env python3
"""
KLAMBA — Linux (CachyOS / Arch / KDE Plasma) Keyboard Backlight Control Application
Native Qt6 (PySide6 QtWidgets) | Bilingual UI (TR / EN)

CLI Shortcut Commands:
  klamba --toggle           Turn backlight off / restore previous brightness
  klamba --brightness-up    Increase brightness by 15%
  klamba --brightness-down  Decrease brightness by 15%
  klamba --next-profile     Switch to next saved profile
  klamba --profile "Name"   Apply a specific profile
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSlider,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "KLAMBA"
CONFIG_DIR = Path.home() / ".config" / "klamba"
PROFILES_FILE = CONFIG_DIR / "profiles.json"
STATE_FILE = CONFIG_DIR / "state.json"
UDEV_RULE_PATH = "/etc/udev/rules.d/99-kbd-backlight.rules"
DESKTOP_DIR = Path.home() / ".local" / "share" / "applications"

DEFAULT_PROFILES = {
    "Breeze Cyan": {"hex": "#1D99F3", "brightness": 85, "mode": 0},
    "CachyOS Teal": {"hex": "#00BFA5", "brightness": 90, "mode": 0},
    "Gece Çalışma": {"hex": "#FF8F00", "brightness": 40, "mode": 0},
    "Sinema Modu": {"hex": "#8E24AA", "brightness": 30, "mode": 0},
    "Saf Beyaz": {"hex": "#FFFFFF", "brightness": 100, "mode": 0},
}

PRESET_COLORS = [
    "#1D99F3", "#00BFA5", "#2ECC71", "#F39C12",
    "#E74C3C", "#9B59B6", "#E91E63", "#FFFFFF",
]

STRINGS = {
    "tr": {
        "win_title": "KLAMBA — Klavye Aydınlatma Kontrolü",
        "subtitle_ok": "Klavye Aydınlatma Kontrolü",
        "subtitle_demo": "Önizleme Modu (Sürücü Bulunamadı)",
        "refresh": "Yenile",
        "light_on": "Işık: Açık",
        "light_off": "Işık: Kapalı",
        "udev_banner": "SysFS yazma izni eksik. Klavye ışıklarını şifresiz kontrol etmek için udev kuralı kurabilirsiniz.",
        "udev_btn": "Şifresiz Erişim İzni Ver",
        "demo_banner": "SysFS klavye sürücüsü bulunamadı (Önizleme Modu). Monster/Clevo cihazlarda 'sudo modprobe tuxedo_keyboard' çalıştırın.",
        "grp_bright": "Parlaklık ve Mod",
        "lbl_bright": "Parlaklık:",
        "lbl_mode": "Efekt Modu:",
        "grp_color": "Renk Kontrolü",
        "sync_zones": "Tüm Bölgeleri Senkronize Et",
        "zones": ["Sol", "Orta", "Sağ"],
        "color_picker": "Renk Seçici...",
        "color_dialog": "Klavye Rengi Seç",
        "lbl_hex": "Hex Kodu:",
        "apply": "Uygula",
        "grp_profiles": "Profiller",
        "prof_placeholder": "Yeni profil adı (örn: Gece Kodlama)",
        "save_prof": "Profili Kaydet",
        "grp_shortcuts": "KDE Kısayolları",
        "sc_info": "Aşağıdaki butonla KLAMBA eylemlerini KDE Sistem Ayarları > Kısayollar menüsüne ekleyip kendi tuşlarını atayabilirsin.",
        "sc_btn": "KDE Kısayollarına Ekle ve Ayarları Aç",
        "ready": "Hazır",
        "refreshed": "Donanım durumu yenilendi.",
        "prof_applied": "'{name}' profili uygulandı.",
        "prof_saved": "'{name}' profili kaydedildi.",
        "tray_show": "Pencereyi Göster / Gizle",
        "tray_toggle": "Klavye Işığını Aç / Kapat",
        "tray_profile": "Profil",
        "tray_quit": "Çıkış",
        "modes": ["Sabit (Custom)", "Nefes (Breathe)", "Renk Döngüsü (Cycle)", "Dans (Dance)", "Flaş (Flash)", "Rastgele (Random)", "Tempo", "Dalga (Wave)"],
        "err_perm": "Yazma izni yok. Üstteki 'Şifresiz Erişim İzni Ver' butonunu kullanın.",
        "err_hex": "Geçersiz hex renk kodu.",
        "udev_ok": "udev kuralı kuruldu! Artık şifresiz kontrol edebilirsiniz.",
        "udev_fail": "Yetkilendirme iptal edildi veya başarısız oldu.",
        "sc_ok": "KDE Kısayol eylemleri eklendi! Sistem Ayarları > Kısayollar penceresi açılıyor.",
    },
    "en": {
        "win_title": "KLAMBA — Keyboard Backlight Control",
        "subtitle_ok": "Keyboard Backlight Control",
        "subtitle_demo": "Preview Mode (Driver Not Found)",
        "refresh": "Refresh",
        "light_on": "Light: On",
        "light_off": "Light: Off",
        "udev_banner": "SysFS write permission missing. Install the udev rule to control keyboard lights without a password.",
        "udev_btn": "Grant Passwordless Access",
        "demo_banner": "SysFS keyboard driver not found (Preview Mode). On Monster/Clevo laptops, run 'sudo modprobe tuxedo_keyboard'.",
        "grp_bright": "Brightness & Mode",
        "lbl_bright": "Brightness:",
        "lbl_mode": "Effect Mode:",
        "grp_color": "Color Control",
        "sync_zones": "Sync All Zones",
        "zones": ["Left", "Center", "Right"],
        "color_picker": "Color Picker...",
        "color_dialog": "Choose Keyboard Color",
        "lbl_hex": "Hex Code:",
        "apply": "Apply",
        "grp_profiles": "Profiles",
        "prof_placeholder": "New profile name (e.g. Night Coding)",
        "save_prof": "Save Profile",
        "grp_shortcuts": "KDE Shortcuts",
        "sc_info": "Use the button below to add KLAMBA actions to KDE System Settings > Shortcuts and assign your own keys.",
        "sc_btn": "Add to KDE Shortcuts & Open Settings",
        "ready": "Ready",
        "refreshed": "Hardware status refreshed.",
        "prof_applied": "Profile '{name}' applied.",
        "prof_saved": "Profile '{name}' saved.",
        "tray_show": "Show / Hide Window",
        "tray_toggle": "Toggle Keyboard Light",
        "tray_profile": "Profile",
        "tray_quit": "Quit",
        "modes": ["Custom (Static)", "Breathe", "Cycle", "Dance", "Flash", "Random", "Tempo", "Wave"],
        "err_perm": "No write permission. Use the 'Grant Passwordless Access' button above.",
        "err_hex": "Invalid hex color code.",
        "udev_ok": "udev rule installed! You can now control the lights without a password.",
        "udev_fail": "Authorization cancelled or failed.",
        "sc_ok": "KDE Shortcut actions added! Opening System Settings > Shortcuts.",
    },
}


def create_tray_icon(hex_color: str = "#1D99F3") -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setBrush(QColor("#232629"))
    painter.setPen(QColor(hex_color))
    painter.drawRoundedRect(4, 14, 56, 36, 8, 8)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(hex_color))
    for row in range(3):
        y = 21 + row * 9
        for col in range(5):
            x = 10 + col * 9
            w = 7 if not (row == 2 and col == 1) else 16
            if row == 2 and col == 2:
                continue
            painter.drawRoundedRect(x, y, w, 5, 1.5, 1.5)

    painter.end()
    return QIcon(pixmap)


class KeyboardBackend:
    """SysFS keyboard backlight hardware abstraction layer."""

    def __init__(self):
        self.driver_type = "demo"
        self.sysfs_path: Path | None = None
        self.has_rgb = True
        self.has_zones = False
        self.has_modes = False
        self.writable = False

        self.lang = "tr"
        self.enabled = True
        self.brightness = 80
        self.last_nonzero_brightness = 80
        self.max_brightness = 255
        self.color_left = "#1D99F3"
        self.color_center = "#1D99F3"
        self.color_right = "#1D99F3"
        self.color_extra = "#1D99F3"
        self.sync_zones = True
        self.mode_index = 0
        self.profiles: dict = {}

        self.load_profiles()
        self._load_state()
        self.detect_hardware()

    def tr(self, key: str) -> str:
        return STRINGS.get(self.lang, STRINGS["tr"]).get(key, key)

    def detect_hardware(self):
        leds_dir = Path("/sys/class/leds")
        if leds_dir.exists():
            candidates = sorted(
                [p for p in leds_dir.iterdir() if "kbd_backlight" in p.name],
                key=lambda p: (0 if "rgb" in p.name else 1, p.name),
            )
            if candidates:
                self.sysfs_path = candidates[0]
                self.driver_type = "led_sysfs"
                self.has_rgb = (self.sysfs_path / "multi_intensity").exists()
                self.has_zones = False
                self.has_modes = False
                self._read_led_sysfs()
                self.writable = os.access(self.sysfs_path / "brightness", os.W_OK)
                return

        tuxedo_dir = Path("/sys/devices/platform/tuxedo_keyboard")
        if tuxedo_dir.exists():
            self.sysfs_path = tuxedo_dir
            self.driver_type = "tuxedo_platform"
            self.has_rgb = (tuxedo_dir / "color_left").exists()
            self.has_zones = (tuxedo_dir / "color_center").exists() and (tuxedo_dir / "color_right").exists()
            self.has_modes = (tuxedo_dir / "mode").exists()
            self._read_tuxedo_sysfs()
            self.writable = os.access(tuxedo_dir / "brightness", os.W_OK)
            return

        self.driver_type = "demo"
        self.sysfs_path = None
        self.has_rgb = True
        self.has_zones = False
        self.has_modes = False
        self.writable = True

    def driver_label(self) -> str:
        if self.driver_type in ("led_sysfs", "tuxedo_platform"):
            return self.tr("subtitle_ok")
        return self.tr("subtitle_demo")

    def _read_led_sysfs(self):
        if not self.sysfs_path:
            return
        try:
            max_b = self.sysfs_path / "max_brightness"
            if max_b.exists():
                self.max_brightness = max(1, int(max_b.read_text().strip()))
            b_file = self.sysfs_path / "brightness"
            if b_file.exists():
                raw_b = int(b_file.read_text().strip())
                self.enabled = raw_b > 0
                pct = max(0, min(100, round((raw_b / self.max_brightness) * 100)))
                self.brightness = pct
                if pct > 0:
                    self.last_nonzero_brightness = pct
            mi = self.sysfs_path / "multi_intensity"
            if mi.exists():
                parts = [int(x) for x in mi.read_text().strip().split()]
                if len(parts) >= 3:
                    hex_c = f"#{parts[0]:02X}{parts[1]:02X}{parts[2]:02X}"
                    self.color_left = self.color_center = self.color_right = self.color_extra = hex_c
        except Exception:
            pass

    def _read_tuxedo_sysfs(self):
        if not self.sysfs_path:
            return
        try:
            st = self.sysfs_path / "state"
            if st.exists():
                self.enabled = st.read_text().strip() == "1"
            bf = self.sysfs_path / "brightness"
            if bf.exists():
                raw_b = int(bf.read_text().strip())
                pct = max(0, min(100, round((raw_b / 255) * 100)))
                self.brightness = pct if self.enabled else 0
                if pct > 0:
                    self.last_nonzero_brightness = pct
            for attr, field in [
                ("color_left", "color_left"),
                ("color_center", "color_center"),
                ("color_right", "color_right"),
                ("color_extra", "color_extra"),
            ]:
                f = self.sysfs_path / attr
                if f.exists():
                    val = f.read_text().strip().replace("0x", "").replace("#", "")
                    if len(val) == 6:
                        setattr(self, field, f"#{val.upper()}")
            mf = self.sysfs_path / "mode"
            if mf.exists():
                self.mode_index = int(mf.read_text().strip())
        except Exception:
            pass

    def _write_sysfs(self, filename: str, value: str) -> tuple[bool, str]:
        if self.driver_type == "demo" or not self.sysfs_path:
            return True, ""
        target = self.sysfs_path / filename
        if not target.exists():
            return False, ""
        try:
            target.write_text(str(value))
            self.writable = True
            return True, ""
        except PermissionError:
            self.writable = False
            return False, self.tr("err_perm")
        except Exception as exc:
            return False, f"SysFS error: {exc}"

    def apply_to_hardware(self) -> tuple[bool, str]:
        if self.brightness > 0:
            self.last_nonzero_brightness = self.brightness
        self._save_state()

        if self.driver_type == "led_sysfs":
            if self.has_rgb:
                c = QColor(self.color_left)
                ok, msg = self._write_sysfs("multi_intensity", f"{c.red()} {c.green()} {c.blue()}")
                if not ok and msg:
                    return False, msg
            raw_b = round((self.brightness / 100) * self.max_brightness) if self.enabled else 0
            return self._write_sysfs("brightness", str(raw_b))

        if self.driver_type == "tuxedo_platform":
            ok, msg = self._write_sysfs("state", "1" if self.enabled else "0")
            if not ok and msg:
                return False, msg
            raw_b = round((self.brightness / 100) * 255)
            self._write_sysfs("brightness", str(raw_b))
            if self.has_rgb:
                self._write_sysfs("color_left", f"0x{self.color_left.lstrip('#')}")
                if self.has_zones:
                    c_mid = self.color_left if self.sync_zones else self.color_center
                    c_rgt = self.color_left if self.sync_zones else self.color_right
                    c_ext = self.color_left if self.sync_zones else self.color_extra
                    self._write_sysfs("color_center", f"0x{c_mid.lstrip('#')}")
                    self._write_sysfs("color_right", f"0x{c_rgt.lstrip('#')}")
                    self._write_sysfs("color_extra", f"0x{c_ext.lstrip('#')}")
            if self.has_modes:
                self._write_sysfs("mode", str(self.mode_index))
        return True, ""

    def toggle_power(self) -> tuple[bool, str]:
        self.enabled = not self.enabled
        if self.enabled and self.brightness == 0:
            self.brightness = max(20, self.last_nonzero_brightness)
        return self.apply_to_hardware()

    def step_brightness(self, delta: int) -> tuple[bool, str]:
        if delta < 0:
            if not self.enabled or self.brightness <= 0:
                self.brightness = 0
                self.enabled = False
            else:
                self.brightness = max(0, self.brightness + delta)
                self.enabled = self.brightness > 0
        elif delta > 0:
            if not self.enabled or self.brightness <= 0:
                self.enabled = True
                self.brightness = min(100, delta)
            else:
                self.brightness = min(100, self.brightness + delta)
                self.enabled = True
        return self.apply_to_hardware()

    def next_profile(self) -> tuple[bool, str]:
        names = list(self.profiles.keys())
        if not names:
            return False, "No profiles."
        cur = self._load_state_raw().get("active_profile", "")
        idx = (names.index(cur) + 1) % len(names) if cur in names else 0
        return self.apply_profile(names[idx])

    def set_zone_color(self, hex_color: str, zone: int = 0) -> tuple[bool, str]:
        c = QColor(hex_color)
        if not c.isValid():
            return False, self.tr("err_hex")
        norm = c.name().upper()
        if self.sync_zones or zone == 0:
            self.color_left = norm
            if self.sync_zones:
                self.color_center = self.color_right = self.color_extra = norm
        elif zone == 1:
            self.color_center = norm
        elif zone == 2:
            self.color_right = norm
        elif zone == 3:
            self.color_extra = norm
        return self.apply_to_hardware()

    def apply_profile(self, name: str) -> tuple[bool, str]:
        prof = self.profiles.get(name)
        if not prof:
            return False, "Profile not found."
        self.enabled = True
        self.brightness = int(prof.get("brightness", 80))
        self.mode_index = int(prof.get("mode", 0))
        hex_c = prof.get("hex", "#1D99F3").upper()
        self.color_left = self.color_center = self.color_right = self.color_extra = hex_c
        self._save_state(active_profile=name)
        return self.apply_to_hardware()

    def save_profile(self, name: str):
        clean = name.strip()
        if not clean:
            return
        self.profiles[clean] = {
            "hex": self.color_left,
            "brightness": self.brightness,
            "mode": self.mode_index,
        }
        self._persist_profiles()

    def register_kde_shortcut_entries(self) -> tuple[bool, str]:
        try:
            DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
            script_path = Path(__file__).resolve()
            entries = [
                ("klamba-toggle.desktop", "KLAMBA: Toggle Light", f"python3 {script_path} --toggle"),
                ("klamba-up.desktop", "KLAMBA: Brightness Up", f"python3 {script_path} --brightness-up"),
                ("klamba-down.desktop", "KLAMBA: Brightness Down", f"python3 {script_path} --brightness-down"),
                ("klamba-next.desktop", "KLAMBA: Next Profile", f"python3 {script_path} --next-profile"),
            ]
            for fname, name, exec_cmd in entries:
                content = (
                    "[Desktop Entry]\n"
                    f"Name={name}\n"
                    f"Exec={exec_cmd}\n"
                    "Icon=input-keyboard\n"
                    "Terminal=false\n"
                    "Type=Application\n"
                    "NoDisplay=true\n"
                    "Categories=Settings;HardwareSettings;KDE;\n"
                )
                (DESKTOP_DIR / fname).write_text(content, encoding="utf-8")
            subprocess.run(["kbuildsycoca6"], capture_output=True)
            subprocess.Popen(["systemsettings", "kcm_keys"])
            return True, self.tr("sc_ok")
        except Exception as exc:
            return False, f"Shortcut error: {exc}"

    def install_udev_rule(self) -> tuple[bool, str]:
        rule_content = (
            'SUBSYSTEM=="leds", KERNEL=="*kbd_backlight*", RUN+="/bin/chmod 0666 /sys/class/leds/%k/brightness /sys/class/leds/%k/multi_intensity"\n'
            'SUBSYSTEM=="platform", KERNEL=="tuxedo_keyboard", RUN+="/bin/chmod 0666 /sys/devices/platform/tuxedo_keyboard/state /sys/devices/platform/tuxedo_keyboard/brightness /sys/devices/platform/tuxedo_keyboard/color_left /sys/devices/platform/tuxedo_keyboard/color_center /sys/devices/platform/tuxedo_keyboard/color_right /sys/devices/platform/tuxedo_keyboard/color_extra /sys/devices/platform/tuxedo_keyboard/mode"\n'
        )
        cmd = (
            f"printf '%s' '{rule_content}' > {UDEV_RULE_PATH} && "
            "udevadm control --reload-rules && udevadm trigger"
        )
        try:
            res = subprocess.run(["pkexec", "sh", "-c", cmd], capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                self.detect_hardware()
                return True, self.tr("udev_ok")
            return False, self.tr("udev_fail")
        except Exception as exc:
            return False, f"udev error: {exc}"

    def load_profiles(self):
        if PROFILES_FILE.exists():
            try:
                self.profiles = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
                return
            except Exception:
                pass
        self.profiles = dict(DEFAULT_PROFILES)
        self._persist_profiles()

    def _persist_profiles(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            PROFILES_FILE.write_text(json.dumps(self.profiles, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def _load_state_raw(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _load_state(self):
        st = self._load_state_raw()
        if "last_nonzero_brightness" in st:
            self.last_nonzero_brightness = int(st["last_nonzero_brightness"])
        if st.get("lang") in ("tr", "en"):
            self.lang = st["lang"]

    def _save_state(self, active_profile: str | None = None):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            st = self._load_state_raw()
            st["last_nonzero_brightness"] = self.last_nonzero_brightness
            st["hex"] = self.color_left
            st["lang"] = self.lang
            if active_profile is not None:
                st["active_profile"] = active_profile
            STATE_FILE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


class KeyboardPreviewWidget(QWidget):
    """Live RGB/brightness keyboard preview widget."""

    def __init__(self, backend: KeyboardBackend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setMinimumHeight(150)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.setBrush(QColor("#1B1E20"))
        painter.setPen(QPen(QColor(80, 86, 94), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)

        rows = [14, 14, 13, 12, 8]
        key_h = 20
        gap = 5
        total_h = len(rows) * key_h + (len(rows) - 1) * gap
        start_y = (rect.height() - total_h) // 2

        alpha = max(25, round((self.backend.brightness / 100.0) * 255)) if self.backend.enabled else 20

        for r_idx, count in enumerate(rows):
            widths = []
            for c_idx in range(count):
                if r_idx == 4 and c_idx == 3:
                    widths.append(124)
                elif r_idx == 2 and c_idx == 0:
                    widths.append(42)
                else:
                    widths.append(28)
            row_w = sum(widths) + (count - 1) * gap
            cx = (rect.width() - row_w) // 2
            cy = start_y + r_idx * (key_h + gap)

            for c_idx, kw in enumerate(widths):
                norm_x = (c_idx + 0.5) / count
                if not self.backend.enabled:
                    col = QColor("#3A3E42")
                elif self.backend.sync_zones or not self.backend.has_zones:
                    col = QColor(self.backend.color_left)
                elif norm_x < 0.34:
                    col = QColor(self.backend.color_left)
                elif norm_x < 0.67:
                    col = QColor(self.backend.color_center)
                else:
                    col = QColor(self.backend.color_right)

                border_col = QColor(col)
                border_col.setAlpha(alpha if self.backend.enabled else 120)
                painter.setBrush(QColor("#262A2E"))
                painter.setPen(QPen(border_col, 1.5))
                painter.drawRoundedRect(cx, cy, kw, key_h, 4, 4)

                led_col = QColor(col)
                led_col.setAlpha(alpha)
                painter.setPen(Qt.NoPen)
                painter.setBrush(led_col)
                painter.drawRoundedRect(cx + 4, cy + key_h // 2 - 1, kw - 8, 3, 1.5, 1.5)

                cx += kw + gap

        painter.end()


class MainWindow(QMainWindow):
    stateUpdated = Signal()

    def __init__(self, backend: KeyboardBackend):
        super().__init__()
        self.backend = backend
        self.selected_zone = 0

        self.resize(660, 760)
        self.setMinimumSize(540, 620)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(14, 14, 14, 10)
        root_layout.setSpacing(10)

        # Top Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("KLAMBA")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.driver_lbl = QLabel()
        self.driver_lbl.setStyleSheet("font-size: 11px; opacity: 0.75;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.driver_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.lang_btn = QPushButton()
        self.lang_btn.setFixedWidth(48)
        self.lang_btn.clicked.connect(self._on_toggle_lang)
        header_row.addWidget(self.lang_btn)

        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self._on_refresh)
        header_row.addWidget(self.refresh_btn)

        self.power_btn = QPushButton()
        self.power_btn.setCheckable(True)
        self.power_btn.clicked.connect(self._on_power_toggled)
        header_row.addWidget(self.power_btn)
        root_layout.addLayout(header_row)

        # Permission / Demo Banner
        self.banner_frame = QFrame()
        self.banner_frame.setFrameShape(QFrame.StyledPanel)
        banner_lay = QHBoxLayout(self.banner_frame)
        self.banner_lbl = QLabel()
        self.banner_lbl.setWordWrap(True)
        self.udev_btn = QPushButton()
        self.udev_btn.clicked.connect(self._on_install_udev)
        banner_lay.addWidget(self.banner_lbl, 1)
        banner_lay.addWidget(self.udev_btn)
        root_layout.addWidget(self.banner_frame)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        content_lay = QVBoxLayout(scroll_content)
        content_lay.setSpacing(12)

        self.preview = KeyboardPreviewWidget(self.backend)
        content_lay.addWidget(self.preview)

        # Brightness & Mode
        self.bright_group = QGroupBox()
        bright_lay = QVBoxLayout(self.bright_group)
        b_row = QHBoxLayout()
        self.bright_lbl = QLabel()
        b_row.addWidget(self.bright_lbl)
        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(0, 100)
        self.bright_slider.valueChanged.connect(self._on_brightness_changed)
        self.bright_val_lbl = QLabel("80%")
        self.bright_val_lbl.setMinimumWidth(42)
        self.bright_val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        b_row.addWidget(self.bright_slider, 1)
        b_row.addWidget(self.bright_val_lbl)
        bright_lay.addLayout(b_row)

        self.mode_row_widget = QWidget()
        m_row = QHBoxLayout(self.mode_row_widget)
        m_row.setContentsMargins(0, 0, 0, 0)
        self.mode_lbl = QLabel()
        m_row.addWidget(self.mode_lbl)
        self.mode_combo = QComboBox()
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        m_row.addWidget(self.mode_combo, 1)
        bright_lay.addWidget(self.mode_row_widget)
        content_lay.addWidget(self.bright_group)

        # Color Control
        self.color_group = QGroupBox()
        color_lay = QVBoxLayout(self.color_group)

        self.zone_widget = QWidget()
        z_row = QHBoxLayout(self.zone_widget)
        z_row.setContentsMargins(0, 0, 0, 0)
        self.sync_check = QCheckBox()
        self.sync_check.toggled.connect(self._on_sync_toggled)
        z_row.addWidget(self.sync_check)
        z_row.addStretch()
        self.zone_btns: list[QPushButton] = []
        for idx in range(3):
            zb = QPushButton()
            zb.setCheckable(True)
            zb.clicked.connect(lambda _=False, i=idx: self._select_zone(i))
            z_row.addWidget(zb)
            self.zone_btns.append(zb)
        color_lay.addWidget(self.zone_widget)

        presets_row = QHBoxLayout()
        for hex_c in PRESET_COLORS:
            pbtn = QPushButton()
            pbtn.setFixedSize(30, 30)
            pbtn.setStyleSheet(f"background-color: {hex_c}; border-radius: 15px; border: 1px solid #666;")
            pbtn.clicked.connect(lambda _=False, c=hex_c: self._apply_hex(c))
            presets_row.addWidget(pbtn)
        presets_row.addStretch()
        self.pick_btn = QPushButton()
        self.pick_btn.clicked.connect(self._open_color_dialog)
        presets_row.addWidget(self.pick_btn)
        color_lay.addLayout(presets_row)

        self.rgb_sliders: dict[str, tuple[QSlider, QLabel]] = {}
        for ch, col_hex in [("R", "#E74C3C"), ("G", "#2ECC71"), ("B", "#1D99F3")]:
            r_row = QHBoxLayout()
            lbl = QLabel(ch)
            lbl.setStyleSheet(f"font-weight: bold; color: {col_hex};")
            lbl.setFixedWidth(18)
            sld = QSlider(Qt.Horizontal)
            sld.setRange(0, 255)
            sld.valueChanged.connect(self._on_rgb_slider_changed)
            val_lbl = QLabel("0")
            val_lbl.setFixedWidth(34)
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            r_row.addWidget(lbl)
            r_row.addWidget(sld, 1)
            r_row.addWidget(val_lbl)
            color_lay.addLayout(r_row)
            self.rgb_sliders[ch] = (sld, val_lbl)

        hex_row = QHBoxLayout()
        self.hex_lbl = QLabel()
        hex_row.addWidget(self.hex_lbl)
        self.hex_edit = QLineEdit()
        self.hex_edit.setMaximumWidth(110)
        self.hex_edit.returnPressed.connect(lambda: self._apply_hex(self.hex_edit.text()))
        self.hex_apply_btn = QPushButton()
        self.hex_apply_btn.clicked.connect(lambda: self._apply_hex(self.hex_edit.text()))
        hex_row.addWidget(self.hex_edit)
        hex_row.addWidget(self.hex_apply_btn)
        hex_row.addStretch()
        color_lay.addLayout(hex_row)
        content_lay.addWidget(self.color_group)

        # Profiles
        self.prof_group = QGroupBox()
        prof_lay = QVBoxLayout(self.prof_group)
        self.prof_buttons_lay = QHBoxLayout()
        prof_lay.addLayout(self.prof_buttons_lay)

        add_prof_row = QHBoxLayout()
        self.new_prof_edit = QLineEdit()
        self.save_prof_btn = QPushButton()
        self.save_prof_btn.clicked.connect(self._on_save_profile)
        add_prof_row.addWidget(self.new_prof_edit, 1)
        add_prof_row.addWidget(self.save_prof_btn)
        prof_lay.addLayout(add_prof_row)
        content_lay.addWidget(self.prof_group)

        # KDE Shortcuts
        self.sc_group = QGroupBox()
        sc_lay = QVBoxLayout(self.sc_group)
        self.sc_info = QLabel()
        self.sc_info.setWordWrap(True)
        self.sc_info.setStyleSheet("font-size: 11px; opacity: 0.85;")
        sc_lay.addWidget(self.sc_info)

        self.sc_btn = QPushButton()
        self.sc_btn.clicked.connect(self._on_register_shortcuts)
        sc_lay.addWidget(self.sc_btn)
        content_lay.addWidget(self.sc_group)

        content_lay.addStretch()
        scroll.setWidget(scroll_content)
        root_layout.addWidget(scroll, 1)

        footer_row = QHBoxLayout()
        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet("font-size: 11px; opacity: 0.8;")
        author_lbl = QLabel("by Abra")
        author_lbl.setStyleSheet("font-size: 11px; opacity: 0.65;")
        footer_row.addWidget(self.status_lbl)
        footer_row.addStretch()
        footer_row.addWidget(author_lbl)
        root_layout.addLayout(footer_row)

        self._rebuild_profile_buttons()
        self._apply_language()
        self._sync_ui_from_backend()

    def _apply_language(self):
        t = self.backend.tr
        self.setWindowTitle(t("win_title"))
        self.lang_btn.setText("EN" if self.backend.lang == "tr" else "TR")
        self.refresh_btn.setText(t("refresh"))
        self.udev_btn.setText(t("udev_btn"))
        self.bright_group.setTitle(t("grp_bright"))
        self.bright_lbl.setText(t("lbl_bright"))
        self.mode_lbl.setText(t("lbl_mode"))

        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        self.mode_combo.addItems(STRINGS[self.backend.lang]["modes"])
        self.mode_combo.setCurrentIndex(self.backend.mode_index)
        self.mode_combo.blockSignals(False)

        self.color_group.setTitle(t("grp_color"))
        self.sync_check.setText(t("sync_zones"))
        for idx, zname in enumerate(STRINGS[self.backend.lang]["zones"]):
            self.zone_btns[idx].setText(zname)
        self.pick_btn.setText(t("color_picker"))
        self.hex_lbl.setText(t("lbl_hex"))
        self.hex_apply_btn.setText(t("apply"))
        self.prof_group.setTitle(t("grp_profiles"))
        self.new_prof_edit.setPlaceholderText(t("prof_placeholder"))
        self.save_prof_btn.setText(t("save_prof"))
        self.sc_group.setTitle(t("grp_shortcuts"))
        self.sc_info.setText(t("sc_info"))
        self.sc_btn.setText(t("sc_btn"))
        self.status_lbl.setText(t("ready"))
        self._sync_ui_from_backend()

    def _on_toggle_lang(self):
        self.backend.lang = "en" if self.backend.lang == "tr" else "tr"
        self.backend._save_state()
        self._apply_language()

    def _active_hex(self) -> str:
        if self.selected_zone == 1:
            return self.backend.color_center
        if self.selected_zone == 2:
            return self.backend.color_right
        return self.backend.color_left

    def _sync_ui_from_backend(self):
        self.driver_lbl.setText(self.backend.driver_label())
        self.power_btn.setChecked(self.backend.enabled)
        self.power_btn.setText(self.backend.tr("light_on") if self.backend.enabled else self.backend.tr("light_off"))

        show_banner = (not self.backend.writable) or (self.backend.driver_type == "demo")
        self.banner_frame.setVisible(show_banner)
        if not self.backend.writable:
            self.banner_lbl.setText(self.backend.tr("udev_banner"))
            self.udev_btn.setVisible(True)
        elif self.backend.driver_type == "demo":
            self.banner_lbl.setText(self.backend.tr("demo_banner"))
            self.udev_btn.setVisible(False)

        self.bright_slider.blockSignals(True)
        self.bright_slider.setValue(self.backend.brightness)
        self.bright_slider.blockSignals(False)
        self.bright_val_lbl.setText(f"{self.backend.brightness}%")

        self.mode_row_widget.setVisible(self.backend.has_modes)
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(self.backend.mode_index)
        self.mode_combo.blockSignals(False)

        self.color_group.setVisible(self.backend.has_rgb)
        self.zone_widget.setVisible(self.backend.has_zones)
        self.sync_check.blockSignals(True)
        self.sync_check.setChecked(self.backend.sync_zones)
        self.sync_check.blockSignals(False)
        for idx, zb in enumerate(self.zone_btns):
            zb.setVisible(not self.backend.sync_zones)
            zb.setChecked(self.selected_zone == idx)

        c = QColor(self._active_hex())
        for ch, val in [("R", c.red()), ("G", c.green()), ("B", c.blue())]:
            sld, lbl = self.rgb_sliders[ch]
            sld.blockSignals(True)
            sld.setValue(val)
            sld.blockSignals(False)
            lbl.setText(str(val))

        self.hex_edit.setText(c.name().upper())
        self.preview.update()
        self.stateUpdated.emit()

    def _rebuild_profile_buttons(self):
        while self.prof_buttons_lay.count():
            item = self.prof_buttons_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for name in self.backend.profiles.keys():
            btn = QPushButton(name)
            btn.clicked.connect(lambda _=False, n=name: self._on_apply_profile(n))
            self.prof_buttons_lay.addWidget(btn)
        self.prof_buttons_lay.addStretch()

    def _set_status(self, msg: str, is_error: bool = False):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(
            "font-size: 11px; color: #DA4453;" if is_error else "font-size: 11px; opacity: 0.8;"
        )

    def _on_refresh(self):
        self.backend.detect_hardware()
        self._sync_ui_from_backend()
        self._set_status(self.backend.tr("refreshed"))

    def _on_power_toggled(self, checked: bool):
        self.backend.enabled = checked
        ok, msg = self.backend.apply_to_hardware()
        self._sync_ui_from_backend()
        if not ok and msg:
            self._set_status(msg, True)

    def _on_brightness_changed(self, val: int):
        self.backend.brightness = val
        if val > 0 and not self.backend.enabled:
            self.backend.enabled = True
        ok, msg = self.backend.apply_to_hardware()
        self._sync_ui_from_backend()
        if not ok and msg:
            self._set_status(msg, True)

    def _on_mode_changed(self, idx: int):
        self.backend.mode_index = idx
        ok, msg = self.backend.apply_to_hardware()
        self._sync_ui_from_backend()
        if not ok and msg:
            self._set_status(msg, True)

    def _on_sync_toggled(self, checked: bool):
        self.backend.sync_zones = checked
        if checked:
            self.backend.color_center = self.backend.color_right = self.backend.color_extra = self.backend.color_left
        self.backend.apply_to_hardware()
        self._sync_ui_from_backend()

    def _select_zone(self, idx: int):
        self.selected_zone = idx
        self._sync_ui_from_backend()

    def _apply_hex(self, hex_c: str):
        ok, msg = self.backend.set_zone_color(hex_c, self.selected_zone)
        self._sync_ui_from_backend()
        if not ok and msg:
            self._set_status(msg, True)

    def _open_color_dialog(self):
        c = QColorDialog.getColor(QColor(self._active_hex()), self, self.backend.tr("color_dialog"))
        if c.isValid():
            self._apply_hex(c.name())

    def _on_rgb_slider_changed(self):
        r = self.rgb_sliders["R"][0].value()
        g = self.rgb_sliders["G"][0].value()
        b = self.rgb_sliders["B"][0].value()
        c = QColor(r, g, b)
        self._apply_hex(c.name())

    def _on_apply_profile(self, name: str):
        ok, msg = self.backend.apply_profile(name)
        self._sync_ui_from_backend()
        if ok:
            self._set_status(self.backend.tr("prof_applied").format(name=name))
        elif msg:
            self._set_status(msg, True)

    def _on_save_profile(self):
        name = self.new_prof_edit.text().strip()
        if not name:
            return
        self.backend.save_profile(name)
        self.new_prof_edit.clear()
        self._rebuild_profile_buttons()
        self._set_status(self.backend.tr("prof_saved").format(name=name))

    def _on_install_udev(self):
        ok, msg = self.backend.install_udev_rule()
        self._sync_ui_from_backend()
        self._set_status(msg, not ok)

    def _on_register_shortcuts(self):
        ok, msg = self.backend.register_kde_shortcut_entries()
        self._set_status(msg, not ok)


def setup_system_tray(app: QApplication, window: MainWindow, backend: KeyboardBackend) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(create_tray_icon(backend.color_left), app)
    tray.setToolTip(APP_NAME)

    menu = QMenu()
    show_act = QAction(backend.tr("tray_show"), menu)
    show_act.triggered.connect(lambda: (window.setVisible(not window.isVisible()), window.raise_(), window.activateWindow()))
    menu.addAction(show_act)

    toggle_act = QAction(backend.tr("tray_toggle"), menu)
    toggle_act.triggered.connect(lambda: window._on_power_toggled(not backend.enabled))
    menu.addAction(toggle_act)

    menu.addSeparator()
    for p_name in backend.profiles.keys():
        act = QAction(f"{backend.tr('tray_profile')}: {p_name}", menu)
        act.triggered.connect(lambda _=False, n=p_name: window._on_apply_profile(n))
        menu.addAction(act)

    menu.addSeparator()
    quit_act = QAction(backend.tr("tray_quit"), menu)
    quit_act.triggered.connect(app.quit)
    menu.addAction(quit_act)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: (window.setVisible(not window.isVisible()), window.raise_(), window.activateWindow())
        if reason == QSystemTrayIcon.Trigger
        else None
    )
    window.stateUpdated.connect(lambda: tray.setIcon(create_tray_icon(backend.color_left)))
    tray.show()
    return tray


def main():
    if len(sys.argv) >= 2:
        arg = sys.argv[1]
        if arg == "--toggle":
            KeyboardBackend().toggle_power()
            sys.exit(0)
        if arg == "--brightness-up":
            KeyboardBackend().step_brightness(15)
            sys.exit(0)
        if arg == "--brightness-down":
            KeyboardBackend().step_brightness(-15)
            sys.exit(0)
        if arg == "--next-profile":
            KeyboardBackend().next_profile()
            sys.exit(0)
        if arg == "--profile" and len(sys.argv) >= 3:
            KeyboardBackend().apply_profile(sys.argv[2])
            sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setDesktopFileName("klamba")
    app.setQuitOnLastWindowClosed(False)

    backend = KeyboardBackend()
    window = MainWindow(backend)
    _tray = setup_system_tray(app, window, backend)

    window.show()
    window.raise_()
    window.activateWindow()
    print("[KLAMBA] UI started.", flush=True)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()