#!/bin/sh
# Install monitor-input + the root Pause-key listener.
# Run from the repo: sudo ./install.sh
set -e
[ "$(id -u)" = 0 ] || { echo "run with sudo" >&2; exit 1; }
SRC="$(dirname "$(readlink -f "$0")")"

install -m 755 -o root -g root "$SRC/monitor-input"     /usr/local/bin/monitor-input
install -m 755 -o root -g root "$SRC/pause-listener.py" /usr/local/bin/monitor-input-pause-listener
install -m 644 -o root -g root "$SRC/monitor-input-pause.service" /etc/systemd/system/monitor-input-pause.service

systemctl daemon-reload
systemctl enable --now monitor-input-pause.service
systemctl restart monitor-input-pause.service

# Retire an old KDE global shortcut for the same key, otherwise one press toggles twice.
if [ -n "$SUDO_USER" ]; then
  USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
  DESK="$USER_HOME/.local/share/applications/net.local.monitor-input-toggle.desktop"
  if [ -f "$DESK" ]; then
    mv "$DESK" "$DESK.disabled"
    echo "Disabled KDE shortcut launcher: $DESK.disabled"
  fi
fi

sleep 1
systemctl --no-pager status monitor-input-pause.service | head -15
