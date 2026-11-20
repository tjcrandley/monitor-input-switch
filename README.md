# monitor-input-switch

Press **Pause/Break** to flip a monitor between two inputs over DDC/CI — and
have it keep working on the **lock screen** and login screen.

Built for a Samsung Odyssey G95NC shared between a Linux PC (DisplayPort) and
an Xbox/KVM (HDMI-1), on KDE Plasma (Wayland).

## Why a daemon?

A desktop global shortcut (KDE, GNOME, etc.) is handled inside the user
session, and the screen locker suspends those shortcuts while it holds the
keyboard. So once the PC locks while you're looking at the other input, the
key goes dead.

`pause-listener.py` runs as a root systemd service and reads key events
straight from `/dev/input` with python-evdev, below the desktop. When it sees
Pause pressed it runs `monitor-input toggle`.

- Passive read only (no device grab) — every key still reaches the desktop.
- Only `KEY_PAUSE` is inspected; nothing else is logged or stored.
- Rescans every 3 s, so keyboards that sleep/reconnect are picked back up.
- 1.5 s debounce so autorepeat or a double tap doesn't bounce the input.

## Files

| File | Installed to | Purpose |
|---|---|---|
| `monitor-input` | `/usr/local/bin/monitor-input` | `xbox` / `pc` / `toggle` via `ddcutil setvcp 60` |
| `pause-listener.py` | `/usr/local/bin/monitor-input-pause-listener` | Watches keyboards for Pause |
| `monitor-input-pause.service` | `/etc/systemd/system/` | Runs the listener as root at boot |
| `install.sh` / `uninstall.sh` | — | Set up / tear down |

## Requirements

- `ddcutil` with DDC/CI enabled in the monitor's OSD
- `python-evdev` (`pacman -S python-evdev` / `apt install python3-evdev`)
- systemd

## Install

```sh
sudo ./install.sh
```

If a KDE shortcut launcher named `net.local.monitor-input-toggle.desktop`
exists, the installer renames it to `*.disabled` so one press doesn't toggle
twice. Remove any other desktop binding of Pause to `monitor-input` yourself.

Uninstall with `sudo ./uninstall.sh`.

## Adapting to another monitor

Edit `monitor-input`:

- `M=` — the model string `ddcutil detect` reports.
- Input codes for VCP `0x60`. Find yours with `ddcutil capabilities` and
  `ddcutil getvcp 60` while on each input. (Samsung: HDMI-1 `0x05`,
  HDMI-2 `0x06`, DP-1 `0x0f`; HDMI-3 isn't selectable over DDC.)

To use a different key, change `KEY_PAUSE` in `pause-listener.py`
(names from `python -c "from evdev import ecodes; print(ecodes.KEY)"`).

Re-run `sudo ./install.sh` after edits.

## Debugging

```sh
journalctl -u monitor-input-pause -f      # listener: devices watched, presses
journalctl -t monitor-input -f            # switch script: current input, ddcutil exit code
```
