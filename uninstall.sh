#!/bin/sh
# Remove the service and installed scripts. Run: sudo ./uninstall.sh
set -e
[ "$(id -u)" = 0 ] || { echo "run with sudo" >&2; exit 1; }
systemctl disable --now monitor-input-pause.service 2>/dev/null || true
rm -f /etc/systemd/system/monitor-input-pause.service \
      /usr/local/bin/monitor-input-pause-listener \
      /usr/local/bin/monitor-input
systemctl daemon-reload
echo "Removed."
