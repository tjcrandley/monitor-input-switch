# monitor-input-switch

Press **Pause/Break** to flip a monitor between two inputs over DDC/CI — and
have it keep working on the **lock screen** and login screen.

Built for a Samsung Odyssey G95NC shared between a Linux PC (DisplayPort) and
an Xbox/KVM (HDMI-1), on KDE Plasma (Wayland) / CachyOS. Tested working from
the unlocked desktop and from the KDE lock screen (kscreenlocker).

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

Re-running it is safe: it overwrites the installed files and restarts the
service, so it doubles as the upgrade step after editing anything in the repo.

**Don't also bind Pause in your desktop's shortcut settings**, or one press
will toggle twice (desktop + daemon) and land back where it started. If a KDE
launcher named `net.local.monitor-input-toggle.desktop` exists (the
pre-daemon setup), the installer renames it to `*.disabled`; that file can be
deleted.

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

A healthy press looks like:

```
monitor-input-pause-listener: Pause pressed -> toggle
monitor-input: toggle: current=sl=0x0f
monitor-input: switching to xbox (0x05)
monitor-input: ddcutil exit 0
```

**`ddcutil exit 1` with "Unable to determine dynamic sleep cache file name"**
— ddcutil won't start without a cache directory, and systemd services get no
`HOME` or `XDG_CACHE_HOME`. The unit sets `CacheDirectory=monitor-input` and
`XDG_CACHE_HOME=/var/cache/monitor-input` for this; keep those lines if you
edit the unit.

**`current=unknown`** — the `getvcp` read failed (same cache issue above, the
monitor's DDC/CI is off, or the `--model` string doesn't match
`ddcutil detect`). The script then defaults to switching to the PC input.

**No "Pause pressed" line** — check the startup lines list your keyboard as
`watching /dev/input/eventN`. Only devices that advertise `KEY_PAUSE` are
watched.
