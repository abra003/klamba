#!/usr/bin/env bash
set -euo pipefail

# KLAMBA Kurulum Betiği (Arch/CachyOS, Ubuntu/Debian, Fedora, openSUSE + KDE Plasma)

APP_DIR="$HOME/.local/share/klamba"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_SRC="$SCRIPT_DIR/klamba.py"
LOGO_SRC="$SCRIPT_DIR/klamba-logo.png"

echo "==> KLAMBA kuruluyor..."

if [[ ! -f "$SCRIPT_SRC" ]]; then
    echo "Hata: klamba.py aynı dizinde bulunamadı."
    exit 1
fi

# 1. Dağıtıma göre PySide6 bağımlılık kurulumu
if ! python3 -c "import PySide6.QtWidgets" &>/dev/null; then
    echo "==> PySide6 paketi kuruluyor (sudo gerekir)..."
    if command -v pacman &>/dev/null; then
        sudo pacman -S --needed --noconfirm pyside6
    elif command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtcore || \
            pip3 install --user PySide6
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-pyside6
    elif command -v zypper &>/dev/null; then
        sudo zypper install -y python3-pyside6
    else
        echo "Uyarı: Paket yöneticisi tanınamadı. 'pip install PySide6' ile kurmayı deneyin."
    fi
fi

# 2. Dosyaları kopyala
mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR"
cp "$SCRIPT_SRC" "$APP_DIR/klamba.py"
chmod +x "$APP_DIR/klamba.py"
ln -sf "$APP_DIR/klamba.py" "$BIN_DIR/klamba"

ICON_VALUE="input-keyboard"
if [[ -f "$LOGO_SRC" ]]; then
    cp "$LOGO_SRC" "$APP_DIR/klamba-logo.png"
    ICON_VALUE="$APP_DIR/klamba-logo.png"
fi

# 3. KDE Başlatıcı (.desktop) dosyasını oluştur
cat > "$DESKTOP_DIR/klamba.desktop" <<EOF
[Desktop Entry]
Name=KLAMBA
Comment=Gömülü Klavye Arka Aydınlatma Kontrolü
Exec=python3 $APP_DIR/klamba.py
Icon=$ICON_VALUE
Terminal=false
Type=Application
Categories=Settings;HardwareSettings;Qt;KDE;
Keywords=keyboard;backlight;rgb;led;tuxedo;clevo;klamba;
EOF

if command -v kbuildsycoca6 &>/dev/null; then
    kbuildsycoca6 &>/dev/null || true
fi

# 4. Şifresiz sysfs erişimi için udev kuralı (opsiyonel)
read -r -p "Şifresiz ışık kontrolü için udev kuralı kurulsun mu? [E/h] " ans
if [[ "${ans:-E}" =~ ^[EeYy]$ ]]; then
    sudo tee /etc/udev/rules.d/99-kbd-backlight.rules >/dev/null <<'RULE'
SUBSYSTEM=="leds", KERNEL=="*kbd_backlight*", RUN+="/bin/chmod 0666 /sys/class/leds/%k/brightness /sys/class/leds/%k/multi_intensity"
SUBSYSTEM=="platform", KERNEL=="tuxedo_keyboard", RUN+="/bin/chmod 0666 /sys/devices/platform/tuxedo_keyboard/state /sys/devices/platform/tuxedo_keyboard/brightness /sys/devices/platform/tuxedo_keyboard/color_left /sys/devices/platform/tuxedo_keyboard/color_center /sys/devices/platform/tuxedo_keyboard/color_right /sys/devices/platform/tuxedo_keyboard/color_extra /sys/devices/platform/tuxedo_keyboard/mode"
RULE
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "==> udev kuralı aktif edildi."
fi

echo "==> Kurulum tamamlandı! Uygulama menüsünden 'KLAMBA' olarak açabilirsin."