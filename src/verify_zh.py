# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 herdr-app-zh contributors
"""Verify the translated files: run `herdr-app check` on every mod and a Node
syntax check on every frame file.

Usage: python src/verify_zh.py
Exit code 0 means everything passed.
"""
import os
import sys
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from apply_zh import APP, MODS, FRAME


def app_bin():
    env = os.environ.get("HERDR_APP_BIN")
    if env and os.path.isfile(env):
        return env
    found = shutil.which("herdr-app") or shutil.which("herdr-app.exe")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA")
    candidates = [
        os.path.join(local, "Programs", "herdr-app", "herdr-app.exe") if local else "",
        "/Applications/Herdr.app/Contents/MacOS/herdr-app",
        os.path.expanduser("~/Applications/Herdr.app/Contents/MacOS/herdr-app"),
        os.path.expanduser("~/.local/bin/herdr-app"),
        "/usr/local/bin/herdr-app",
        "/usr/bin/herdr-app",
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def node_bin():
    env = os.environ.get("HERDR_ZH_NODE")
    if env and os.path.isfile(env):
        return env
    return shutil.which("node")


def check_mods(exe):
    if not exe:
        print("herdr-app binary not found; set HERDR_APP_BIN to its path")
        return 0, 1
    ok = fail = 0
    for name in sorted(os.listdir(MODS)):
        d = os.path.join(MODS, name)
        if not os.path.isdir(d):
            continue
        r = subprocess.run([exe, "check", d], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode == 0 and "check passed" in (r.stdout or ""):
            ok += 1
        else:
            fail += 1
            lines = (r.stdout or r.stderr or "").strip().splitlines()
            print(f"FAIL mod {name}: {lines[0] if lines else r.returncode}")
    print(f"mods: {ok} passed, {fail} failed")
    return ok, fail


def check_frame(node):
    if not node:
        print("node not found; skipping frame syntax check")
        return 0, 0
    ok = fail = 0
    tmp = os.path.join(tempfile.gettempdir(), "_herdr_frame_check.mjs")
    for dp, _, fs in os.walk(FRAME):
        for fn in fs:
            if not fn.endswith(".js"):
                continue
            src = os.path.join(dp, fn)
            shutil.copyfile(src, tmp)
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if r.returncode == 0:
                ok += 1
            else:
                fail += 1
                first = (r.stderr or "").strip().splitlines()[:1]
                print(f"FAIL frame {os.path.relpath(src, FRAME)}: {first}")
    print(f"frame: {ok} passed, {fail} failed")
    return ok, fail


if __name__ == "__main__":
    if not os.path.isdir(APP):
        print(f"herdr-app config not found: {APP}")
        sys.exit(1)
    _, f1 = check_mods(app_bin())
    _, f2 = check_frame(node_bin())
    sys.exit(1 if (f1 or f2) else 0)
