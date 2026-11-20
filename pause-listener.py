#!/usr/bin/python3
"""Run `monitor-input toggle` when Pause/Break is pressed on any keyboard.

Reads /dev/input directly (as root), so it works on the lock screen and the
login screen, where KDE global shortcuts are suspended. Devices are read
passively (no grab), so other programs still see every key. Only KEY_PAUSE is
inspected; nothing else is logged or stored.
"""
import os, selectors, subprocess, sys, time
import evdev
from evdev import ecodes

SCRIPT = "/usr/local/bin/monitor-input"
RESCAN_SECS = 3      # pick up keyboards that reconnect (receiver sleep, replug)
DEBOUNCE_SECS = 1.5  # ignore key repeat / double taps while the monitor switches

sel = selectors.DefaultSelector()
watched = {}  # path -> InputDevice
last_fire = 0.0


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def rescan():
    for path in evdev.list_devices():
        if path in watched:
            continue
        try:
            dev = evdev.InputDevice(path)
            if ecodes.KEY_PAUSE in dev.capabilities().get(ecodes.EV_KEY, []):
                sel.register(dev, selectors.EVENT_READ)
                watched[path] = dev
                log(f"watching {path} ({dev.name})")
            else:
                dev.close()
        except OSError:
            pass


def drop(dev):
    log(f"lost {dev.path}")
    try:
        sel.unregister(dev)
    except (KeyError, ValueError):
        pass
    watched.pop(dev.path, None)
    try:
        dev.close()
    except OSError:
        pass


def fire():
    global last_fire
    now = time.monotonic()
    if now - last_fire < DEBOUNCE_SECS:
        return
    last_fire = now
    log("Pause pressed -> toggle")
    subprocess.Popen([SCRIPT, "toggle"], stdin=subprocess.DEVNULL)


def main():
    next_scan = 0.0
    while True:
        if time.monotonic() >= next_scan:
            rescan()
            next_scan = time.monotonic() + RESCAN_SECS
        for key, _ in sel.select(timeout=RESCAN_SECS):
            dev = key.fileobj
            try:
                for ev in dev.read():
                    # value 1 = key down (ignore 0 = up, 2 = autorepeat)
                    if ev.type == ecodes.EV_KEY and ev.code == ecodes.KEY_PAUSE and ev.value == 1:
                        fire()
            except OSError:
                drop(dev)
        # reap finished toggle processes
        try:
            while os.waitpid(-1, os.WNOHANG)[0]:
                pass
        except ChildProcessError:
            pass


if __name__ == "__main__":
    main()
