# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 herdr-app-zh contributors
"""Report UI strings that are still English.

Usage:
  python src/audit_zh.py            # print
  python src/audit_zh.py --write    # also write docs/coverage.md
  python src/audit_zh.py --all      # include the win98 demo layout

After a herdr-app update, run this and add the missing strings to zh_dict.py.
"""
import os
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zh_engine import ui_literals
from zh_patches import PATCHES
from apply_zh import REPO, MODS, FRAME, APP

DOC = os.path.join(REPO, "docs", "coverage.md")

# Not interface copy: brands, font names, key names, git codes, months, commands.
KEEP = {
    "Herdr", "Herdr 98", "Herdr ", "JetBrains Mono", "Geist", "Geist Mono",
    "Esc", "Alt", "Ctrl", "Shift", "Super", "Fn", "Ctrl+", "Shift+", "Alt+",
    "HEAD", "HEAD...@{upstream}", "AA", "DD", "NFC", "Darwin",
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    "App", "Layout", "Window", "cannot start sh: program not found",
}


def looks_like_ui(text):
    t = text.strip()
    if t in KEEP:
        return False
    if t.startswith(("hc ", "git ", "uname", "printf", "IFS=", "sudo ")):
        return False
    if t.startswith("$") or ("/" in t and " " not in t):
        return False
    return True


def patch_status():
    """(file, note, applied?) for every code patch, read from the live files."""
    rows = []
    for p in PATCHES:
        path = os.path.join(APP, p["file"])
        try:
            with open(path, encoding="utf-8") as f:
                src = f.read()
        except (OSError, UnicodeDecodeError):
            rows.append((p["file"], p["note"], False))
            continue
        ok = p["new"] in src or bool(p.get("mark") and p["mark"] in src)
        rows.append((p["file"], p["note"], ok))
    return rows


def collect(include_win98=False):
    per = {}
    total = collections.Counter()
    for area in (MODS, FRAME):
        if not os.path.isdir(area):
            continue
        for dp, _, fs in os.walk(area):
            if not include_win98 and "win98" in dp:
                continue
            for fn in fs:
                if not fn.endswith(".js"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    with open(p, encoding="utf-8") as f:
                        src = f.read()
                except (OSError, UnicodeDecodeError):
                    continue
                left = [s for s, _ in ui_literals(src) if looks_like_ui(s)]
                if left:
                    per[os.path.relpath(p, area)] = left
                    total.update(left)
    return per, total


def main():
    include_win98 = "--all" in sys.argv
    per, total = collect(include_win98)
    lines = ["# Coverage\n",
             "Strings still shown in English after applying `zh_dict.py`, excluding",
             "brands, font and key names, git codes, months, and shell commands.",
             "The `win98` demo layout is skipped by default.",
             "This counts **source string literals**; text built at runtime is handled",
             "by the code patches listed at the end.\n",
             f"**{sum(len(v) for v in per.values())} occurrences / {len(total)} unique**, in {len(per)} files.\n",
             "\n## By file\n"]
    if per:
        for rel, items in sorted(per.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"- `{rel}`: {len(items)}")
    else:
        lines.append("None.")
    lines.append("\n## Missing strings\n")
    if total:
        for s, c in total.most_common(200):
            lines.append(f"- {c} x `{s}`")
    else:
        lines.append("None.")
    rows = patch_status()
    missing_patch = [r for r in rows if not r[2]]
    lines.append("\n## Code patches\n")
    lines.append(f"{len(rows) - len(missing_patch)}/{len(rows)} applied.")
    if missing_patch:
        lines.append("")
        for rel, note, _ in missing_patch:
            lines.append(f"- NOT applied: `{rel}` — {note}")
        lines.append("")
        lines.append("Run `python src/apply_zh.py` (and update `zh_patches.py` if the")
        lines.append("anchor is gone after an upstream update).")
    text = "\n".join(lines) + "\n"
    print(text)
    if "--write" in sys.argv:
        os.makedirs(os.path.dirname(DOC), exist_ok=True)
        with open(DOC, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"written to {DOC}")


if __name__ == "__main__":
    main()
