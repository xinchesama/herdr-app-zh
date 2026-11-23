# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 herdr-app-zh contributors
"""Keep herdr-app's interface Chinese while it runs.

herdr-app rewrites mods/ and frame/ from English sources embedded in the binary
on every start. The window hot-reloads JS files, so re-applying the dictionary
right after a start is enough; this watcher does that once per second, and only
reads files whose (mtime, size) changed.

Run it at login (scripts/install-autostart.ps1, systemd, launchd) or manually:
  python src/zh_watch.py
Set HERDR_ZH_INTERVAL to change the poll interval in seconds (default 1).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zh_dict import EXACT, TEMPLATE_WORDS
from zh_engine import translate_js
from apply_zh import APP, MODS, FRAME

INTERVAL = float(os.environ.get("HERDR_ZH_INTERVAL", "1"))
LOG = os.path.join(APP, "zh-watch.log")
LOG_MAX = 512 * 1024
INSTALLED = os.path.join(APP, "installed.json")


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > LOG_MAX:
            os.replace(LOG, LOG + ".old")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def scan_once(cache):
    n = 0
    for area in (MODS, FRAME):
        if not os.path.isdir(area):
            continue
        for dp, _, fs in os.walk(area):
            for fn in fs:
                if not fn.endswith(".js"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                key = (st.st_mtime_ns, st.st_size)
                if cache.get(p) == key:
                    continue
                try:
                    with open(p, encoding="utf-8", newline="") as f:
                        src = f.read()
                except (OSError, UnicodeDecodeError):
                    continue
                out, changed = translate_js(src, EXACT, TEMPLATE_WORDS)
                if changed:
                    try:
                        with open(p, "w", encoding="utf-8", newline="") as f:
                            f.write(out)
                        n += 1
                        st = os.stat(p)
                    except OSError:
                        continue
                cache[p] = (st.st_mtime_ns, st.st_size)
    return n


def main():
    log(f"watcher started: {APP}")
    cache = {}
    installed_stamp = None
    while True:
        try:
            try:
                stamp = os.stat(INSTALLED).st_mtime_ns
            except OSError:
                stamp = None
            if stamp != installed_stamp:
                installed_stamp = stamp
                cache.clear()

            n = scan_once(cache)
            if n:
                log(f"re-applied {n} files")
        except Exception as e:  # a watcher must survive a single bad file
            log(f"error: {e!r}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
