#!/usr/bin/env python3
"""
KLAMBA Windows — Monster / Clevo (InsydeDCHU.dll) Keyboard Backlight Control Application
Native Qt6 (PySide6 QtWidgets) | OLED Pure Black Theme | Bilingual UI (TR / EN) | 1-Zone & 3-Zone | by Abra

Requirements on Windows:
  pip install PySide6
"""

import ctypes
import json
import os
import struct
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
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
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "KLAMBA"
PROFILES_FILE = CONFIG_DIR / "profiles.json"
STATE_FILE = CONFIG_DIR / "state.json"

DCHU_DLL_CANDIDATES = [
    Path(r"C:\Program Files (x86)\ControlCenter\DCHU\InsydeDCHU.dll"),
    Path(r"C:\Program Files\ControlCenter\DCHU\InsydeDCHU.dll"),
    Path(__file__).resolve().parent / "InsydeDCHU.dll",
]

DEFAULT_PROFILES = {
    "Breeze Cyan": {"hex": "#1D99F3", "brightness": 85},
    "Windows Blue": {"hex": "#0078D4", "brightness": 90},
    "Gece Çalışma": {"hex": "#FF8F00", "brightness": 40},
    "Sinema Modu": {"hex": "#8E24AA", "brightness": 30},
    "Saf Beyaz": {"hex": "#FFFFFF", "brightness": 100},
}

PRESET_COLORS = [
    "#1D99F3", "#00BFA5", "#2ECC71", "#F39C12",
    "#E74C3C", "#9B59B6", "#E91E63", "#FFFFFF",
]

STRINGS = {
    "tr": {
        "win_title": "KLAMBA — Klavye Aydınlatma Kontrolü",
        "subtitle_ok": "Klavye Aydınlatma Kontrolü",
        "subtitle_demo": "Önizleme Modu (InsydeDCHU.dll Bulunamadı)",
        "refresh": "Yenile",
        "light_on": "Işık: Açık",
        "light_off": "Işık: Kapalı",
        "demo_banner": "InsydeDCHU.dll bulunamadı (Önizleme Modu). Monster Control Center kurulu olduğundan emin olun.",
        "grp_bright": "Parlaklık",
        "lbl_bright": "Parlaklık:",
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
        "ready": "Hazır",
        "refreshed": "Donanım durumu yenilendi.",
        "prof_applied": "'{name}' profili uygulandı.",
        "prof_saved": "'{name}' profili kaydedildi.",
        "tray_show": "Pencereyi Göster / Gizle",
        "tray_toggle": "Klavye Işığını Aç / Kapat",
        "tray_profile": "Profil",
        "tray_quit": "Çıkış",
        "err_hex": "Geçersiz hex renk kodu.",
        "err_dll": "DCHU yazma hatası: Yönetici olarak çalıştırmayı deneyin.",
    },
    "en": {
        "win_title": "KLAMBA — Keyboard Backlight Control",
        "subtitle_ok": "Keyboard Backlight Control",
        "subtitle_demo": "Preview Mode (InsydeDCHU.dll Not Found)",
        "refresh": "Refresh",
        "light_on": "Light: On",
        "light_off": "Light: Off",
        "demo_banner": "InsydeDCHU.dll not found (Preview Mode). Make sure Monster Control Center is installed.",
        "grp_bright": "Brightness",
        "lbl_bright": "Brightness:",
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
        "ready": "Ready",
        "refreshed": "Hardware status refreshed.",
        "prof_applied": "Profile '{name}' applied.",
        "prof_saved": "Profile '{name}' saved.",
        "tray_show": "Show / Hide Window",
        "tray_toggle": "Toggle Keyboard Light",
        "tray_profile": "Profile",
        "tray_quit": "Quit",
        "err_hex": "Invalid hex color code.",
        "err_dll": "DCHU write error: Try running as Administrator.",
    },
}


def find_logo_path() -> Path | None:
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "klamba-logo.png")
    here = Path(__file__).resolve().parent
    candidates.extend([here / "klamba-logo.png", Path(r"C:\KLAMBA\klamba-logo.png")])
    return next((p for p in candidates if p.exists()), None)


def create_fallback_icon(hex_color: str = "#1D99F3") -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setBrush(QColor("#000000"))
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


def load_app_icon() -> QIcon:
    logo = find_logo_path()
    if logo:
        return QIcon(str(logo))
    return create_fallback_icon()


class WindowsDchuBackend:
    """Windows InsydeDCHU.dll keyboard backlight hardware abstraction layer (1-zone & 3-zone)."""

    CMD_KBD_LED = 0x67  # 103

    def __init__(self):
        self._dll = None
        self.driver_type = "demo"
        self.lang = "tr"
        self.enabled = True
        self.brightness = 80
        self.last_nonzero_brightness = 80
        self.sync_zones = True
        self.color_left = "#1D99F3"
        self.color_center = "#1D99F3"
        self.color_right = "#1D99F3"
        self.profiles: dict = {}

        self.load_profiles()
        self._load_state()
        self.detect_hardware()

    def tr(self, key: str) -> str:
        return STRINGS.get(self.lang, STRINGS["tr"]).get(key, key)

    def detect_hardware(self):
        self._dll = None
        self.driver_type = "demo"
        if sys.platform != "win32":
            return

        dll_path = next((p for p in DCHU_DLL_CANDIDATES if p.exists()), None)
        if not dll_path:
            repo = Path(r"C:\Windows\System32\DriverStore\FileRepository")
            if repo.exists():
                found = list(repo.glob("acpibridge*/InsydeDCHU.dll"))
                if found:
                    dll_path = found[0]

        if dll_path:
            try:
                dll = ctypes.WinDLL(str(dll_path))
                dll.SetDCHU_Data.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
                dll.SetDCHU_Data.restype = ctypes.c_int
                self._dll = dll
                self.driver_type = "dchu"
            except Exception:
                self._dll = None
                self.driver_type = "demo"

    def driver_label(self) -> str:
        return self.tr("subtitle_ok") if self.driver_type == "dchu" else self.tr("subtitle_demo")

    def _encode_brg(self, prefix: int, hex_color: str) -> int:
        if not self.enabled or self.brightness <= 0:
            r = g = b = 0
        else:
            c = QColor(hex_color)
            scale = self.brightness / 100.0
            r = round(c.red() * scale)
            g = round(c.green() * scale)
            b = round(c.blue() * scale)
        return (prefix << 24) | (b << 16) | (r << 8) | g

    def _send_dchu(self, value: int):
        buf = (ctypes.c_ubyte * 4).from_buffer_copy(struct.pack("<I", value))
        self._dll.SetDCHU_Data(self.CMD_KBD_LED, buf, 4)

    def apply_to_hardware(self) -> tuple[bool, str]:
        if self.brightness > 0:
            self.last_nonzero_brightness = self.brightness
        self._save_state()

        if self.driver_type != "dchu" or self._dll is None:
            return True, ""

        try:
            if self.enabled and self.brightness > 0:
                self._send_dchu(0x40000000)
                self._send_dchu(0xD0000000)

            if self.sync_zones:
                self._send_dchu(self._encode_brg(0xF0, self.color_left))
            else:
                self._send_dchu(self._encode_brg(0xF0, self.color_left))
                self._send_dchu(self._encode_brg(0xF1, self.color_center))
                self._send_dchu(self._encode_brg(0xF2, self.color_right))
            return True, ""
        except Exception:
            return False, self.tr("err_dll")

    def set_zone_color(self, hex_color: str, zone: int = 0) -> tuple[bool, str]:
        c = QColor(hex_color)
        if not c.isValid():
            return False, self.tr("err_hex")
        norm = c.name().upper()
        if self.sync_zones or zone == 0:
            self.color_left = norm
            if self.sync_zones:
                self.color_center = self.color_right = norm
        elif zone == 1:
            self.color_center = norm
        elif zone == 2:
            self.color_right = norm
        return self.apply_to_hardware()

    def apply_profile(self, name: str) -> tuple[bool, str]:
        prof = self.profiles.get(name)
        if not prof:
            return False, "Profile not found."
        self.enabled = True
        self.brightness = int(prof.get("brightness", 80))
        hex_c = prof.get("hex", "#1D99F3").upper()
        self.color_left = self.color_center = self.color_right = hex_c
        return self.apply_to_hardware()

    def save_profile(self, name: str):
        clean = name.strip()
        if not clean:
            return
        self.profiles[clean] = {"hex": self.color_left, "brightness": self.brightness}
        self._persist_profiles()

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

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self.brightness = int(st.get("brightness", 80))
                self.last_nonzero_brightness = int(st.get("last_nonzero_brightness", 80))
                self.sync_zones = bool(st.get("sync_zones", True))
                self.color_left = st.get("color_left", st.get("hex", "#1D99F3"))
                self.color_center = st.get("color_center", self.color_left)
                self.color_right = st.get("color_right", self.color_left)
                if st.get("lang") in ("tr", "en"):
                    self.lang = st["lang"]
            except Exception:
                pass

    def _save_state(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            st = {
                "brightness": self.brightness,
                "last_nonzero_brightness": self.last_nonzero_brightness,
                "sync_zones": self.sync_zones,
                "color_left": self.color_left,
                "color_center": self.color_center,
                "color_right": self.color_right,
                "lang": self.lang,
            }
            STATE_FILE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


class KeyboardPreviewWidget(QWidget):
    def __init__(self, backend: WindowsDchuBackend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setMinimumHeight(150)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.setBrush(QColor("#040404"))
        painter.setPen(QPen(QColor("#1F2328"), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)

        rows = [14, 14, 13, 12, 8]
        key_h = 20
        gap = 5
        total_h = len(rows) * key_h + (len(rows) - 1) * gap
        start_y = (rect.height() - total_h) // 2
        alpha = max(25, round((self.backend.brightness / 100.0) * 255)) if self.backend.enabled else 20

        for r_idx, count in enumerate(rows):
            widths = [
                124 if (r_idx == 4 and c_idx == 3) else (42 if (r_idx == 2 and c_idx == 0) else 28)
                for c_idx in range(count)
            ]
            row_w = sum(widths) + (count - 1) * gap
            cx = (rect.width() - row_w) // 2
            cy = start_y + r_idx * (key_h + gap)

            for c_idx, kw in enumerate(widths):
                norm_x = (c_idx + 0.5) / count
                if not self.backend.enabled:
                    col = QColor("#2A2E33")
                elif self.backend.sync_zones:
                    col = QColor(self.backend.color_left)
                elif norm_x < 0.34:
                    col = QColor(self.backend.color_left)
                elif norm_x < 0.67:
                    col = QColor(self.backend.color_center)
                else:
                    col = QColor(self.backend.color_right)

                border_col = QColor(col)
                border_col.setAlpha(alpha if self.backend.enabled else 120)
                painter.setBrush(QColor("#0D0F12"))
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

    def __init__(self, backend: WindowsDchuBackend):
        super().__init__()
        self.backend = backend
        self.selected_zone = 0
        self.resize(660, 710)
        self.setMinimumSize(540, 580)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(14, 14, 14, 10)
        root_layout.setSpacing(10)

        header_row = QHBoxLayout()
        logo_path = find_logo_path()
        if logo_path:
            logo_lbl = QLabel()
            pix = QPixmap(str(logo_path)).scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            header_row.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_lbl = QLabel("KLAMBA")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.driver_lbl = QLabel()
        self.driver_lbl.setStyleSheet("font-size: 11px; color: #8A939E;")
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

        self.banner_frame = QFrame()
        self.banner_frame.setFrameShape(QFrame.StyledPanel)
        banner_lay = QHBoxLayout(self.banner_frame)
        self.banner_lbl = QLabel()
        self.banner_lbl.setWordWrap(True)
        banner_lay.addWidget(self.banner_lbl, 1)
        root_layout.addWidget(self.banner_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        content_lay = QVBoxLayout(scroll_content)
        content_lay.setSpacing(12)

        self.preview = KeyboardPreviewWidget(self.backend)
        content_lay.addWidget(self.preview)

        self.bright_group = QGroupBox()
        b_row = QHBoxLayout(self.bright_group)
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
        content_lay.addWidget(self.bright_group)

        self.color_group = QGroupBox()
        color_lay = QVBoxLayout(self.color_group)

        z_row = QHBoxLayout()
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
        color_lay.addLayout(z_row)

        presets_row = QHBoxLayout()
        for hex_c in PRESET_COLORS:
            pbtn = QPushButton()
            pbtn.setFixedSize(30, 30)
            pbtn.setStyleSheet(f"background-color: {hex_c}; border-radius: 15px; border: 1px solid #333;")
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

        content_lay.addStretch()
        scroll.setWidget(scroll_content)
        root_layout.addWidget(scroll, 1)

        footer_row = QHBoxLayout()
        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet("font-size: 11px; color: #8A939E;")
        author_lbl = QLabel("by Abra")
        author_lbl.setStyleSheet("font-size: 11px; color: #6C757D;")
        footer_row.addWidget(self.status_lbl)
        footer_row.addStretch()
        footer_row.addWidget(author_lbl)
        root_layout.addLayout(footer_row)

        self._rebuild_profile_buttons()
        self._apply_language()
        self._sync_ui()

    def _active_hex(self) -> str:
        if self.selected_zone == 1:
            return self.backend.color_center
        if self.selected_zone == 2:
            return self.backend.color_right
        return self.backend.color_left

    def _apply_language(self):
        t = self.backend.tr
        self.setWindowTitle(t("win_title"))
        self.lang_btn.setText("EN" if self.backend.lang == "tr" else "TR")
        self.refresh_btn.setText(t("refresh"))
        self.bright_group.setTitle(t("grp_bright"))
        self.bright_lbl.setText(t("lbl_bright"))
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
        self.status_lbl.setText(t("ready"))
        self._sync_ui()

    def _on_toggle_lang(self):
        self.backend.lang = "en" if self.backend.lang == "tr" else "tr"
        self.backend._save_state()
        self._apply_language()

    def _sync_ui(self):
        self.driver_lbl.setText(self.backend.driver_label())
        self.power_btn.setChecked(self.backend.enabled)
        self.power_btn.setText(self.backend.tr("light_on") if self.backend.enabled else self.backend.tr("light_off"))

        self.banner_frame.setVisible(self.backend.driver_type == "demo")
        self.banner_lbl.setText(self.backend.tr("demo_banner"))

        self.bright_slider.blockSignals(True)
        self.bright_slider.setValue(self.backend.brightness)
        self.bright_slider.blockSignals(False)
        self.bright_val_lbl.setText(f"{self.backend.brightness}%")

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
            "font-size: 11px; color: #DA4453;" if is_error else "font-size: 11px; color: #8A939E;"
        )

    def _on_refresh(self):
        self.backend.detect_hardware()
        self._sync_ui()
        self._set_status(self.backend.tr("refreshed"))

    def _on_power_toggled(self, checked: bool):
        self.backend.enabled = checked
        ok, msg = self.backend.apply_to_hardware()
        self._sync_ui()
        if not ok and msg:
            self._set_status(msg, True)

    def _on_brightness_changed(self, val: int):
        self.backend.brightness = val
        if val > 0 and not self.backend.enabled:
            self.backend.enabled = True
        elif val == 0:
            self.backend.enabled = False
        ok, msg = self.backend.apply_to_hardware()
        self._sync_ui()
        if not ok and msg:
            self._set_status(msg, True)

    def _on_sync_toggled(self, checked: bool):
        self.backend.sync_zones = checked
        if checked:
            self.backend.color_center = self.backend.color_right = self.backend.color_left
        self.backend.apply_to_hardware()
        self._sync_ui()

    def _select_zone(self, idx: int):
        self.selected_zone = idx
        self._sync_ui()

    def _apply_hex(self, hex_c: str):
        ok, msg = self.backend.set_zone_color(hex_c, self.selected_zone)
        self._sync_ui()
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
        self._apply_hex(QColor(r, g, b).name())

    def _on_apply_profile(self, name: str):
        ok, msg = self.backend.apply_profile(name)
        self._sync_ui()
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


def apply_oled_black_palette(app: QApplication):
    app.setStyle("Fusion")
    app.setStyleSheet(
        """
        QWidget { background-color: #000000; color: #F0F2F5; font-family: "Segoe UI", sans-serif; }
        QGroupBox { background-color: #050505; border: 1px solid #1E2227; border-radius: 8px; margin-top: 10px; padding-top: 10px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #8A939E; }
        QPushButton { background-color: #0E1013; border: 1px solid #262B31; border-radius: 5px; padding: 5px 12px; }
        QPushButton:hover { border-color: #0078D4; }
        QPushButton:checked { background-color: #0078D4; border-color: #0078D4; color: #FFFFFF; }
        QLineEdit { background-color: #08090B; border: 1px solid #262B31; border-radius: 5px; padding: 4px 8px; }
        QSlider::groove:horizontal { height: 5px; background: #1A1D21; border-radius: 2px; }
        QSlider::handle:horizontal { background: #0078D4; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
        QMenu { background-color: #0A0B0D; border: 1px solid #262B31; }
        QMenu::item:selected { background-color: #0078D4; }
        """
    )


def setup_system_tray(app: QApplication, window: MainWindow, backend: WindowsDchuBackend, icon: QIcon) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip(APP_NAME)

    menu = QMenu()
    show_act = QAction(backend.tr("tray_show"), menu)
    show_act.triggered.connect(lambda: (window.showNormal(), window.raise_(), window.activateWindow()))
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
    tray.show()
    return tray


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    apply_oled_black_palette(app)

    app_icon = load_app_icon()
    app.setWindowIcon(app_icon)

    backend = WindowsDchuBackend()
    window = MainWindow(backend)
    window.setWindowIcon(app_icon)
    _tray = setup_system_tray(app, window, backend, app_icon)

    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()