# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 herdr-app-zh contributors
"""Apply the Simplified Chinese interface layer to herdr-app.

Usage:
  python src/apply_zh.py             # translate the files in place (incremental)
  python src/apply_zh.py --rebuild   # prefer pristine copies in backup/original
  python src/apply_zh.py --dry-run   # count only, write nothing
  python src/apply_zh.py --restore   # copy backup/original back, if present

Why a re-apply is needed: herdr-app embeds its English UI JavaScript into the
binary and rewrites the config directory on every start. This tool rewrites the
string literals in those files; zh_watch.py keeps them translated while the app
is running. See docs/how-it-works.md.
"""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zh_dict import EXACT, TEMPLATE_WORDS
from zh_engine import translate_js

REPO = os.path.dirname(HERE)


def app_home():
    """HERDR_APP_HOME, else $XDG_CONFIG_HOME/herdr-app, else ~/.config/herdr-app."""
    env = os.environ.get("HERDR_APP_HOME")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    base = os.environ.get("XDG_CONFIG_HOME")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "herdr-app")


APP = app_home()
MODS = os.path.join(APP, "mods")
FRAME = os.path.join(APP, "frame")
ORIGINAL = os.environ.get("HERDR_ZH_ORIGINAL") or os.path.join(REPO, "backup", "original")


def iter_js(area):
    for dp, _, fs in os.walk(area):
        for fn in fs:
            if fn.endswith(".js"):
                yield os.path.join(dp, fn)


def source_for(path, rel, rebuild):
    if rebuild:
        bak = os.path.join(ORIGINAL, rel)
        if os.path.isfile(bak):
            with open(bak, "rb") as f:
                return f.read(), "original"
    with open(path, "rb") as f:
        return f.read(), "live"


def run(rebuild=False, dry_run=False):
    if not os.path.isdir(APP):
        print(f"herdr-app config not found: {APP}")
        print("Start herdr-app once, or set HERDR_APP_HOME to its home folder.")
        return 1

    changed = []
    total = 0
    for area in (MODS, FRAME):
        if not os.path.isdir(area):
            continue
        for path in iter_js(area):
            rel = os.path.relpath(path, APP)
            raw, origin = source_for(path, rel, rebuild)
            try:
                txt = raw.decode("utf-8")
            except UnicodeDecodeError:
                print(f"skip (not UTF-8): {rel}")
                continue
            out, n = translate_js(txt, EXACT, TEMPLATE_WORDS)
            total += n
            if out == txt:
                continue
            changed.append((rel, n, origin))
            if not dry_run:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(out)

    verb = "would translate" if dry_run else "translated"
    print(f"{verb} {len(changed)} files, {total} strings")
    for rel, n, origin in changed:
        print(f"  {n:3d}  {rel}  ({origin})")
    return 0


def restore():
    if not os.path.isdir(ORIGINAL):
        print("No backup/original folder. Restart herdr-app: it restores English on start.")
        return 1
    n = 0
    for dp, _, fs in os.walk(ORIGINAL):
        for fn in fs:
            src = os.path.join(dp, fn)
            rel = os.path.relpath(src, ORIGINAL)
            dst = os.path.join(APP, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            n += 1
    print(f"restored {n} files from backup/original")
    return 0


if __name__ == "__main__":
    if "--restore" in sys.argv:
        sys.exit(restore())
    sys.exit(run("--rebuild" in sys.argv, "--dry-run" in sys.argv))
