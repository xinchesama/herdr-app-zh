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
from apply_zh import REPO, MODS, FRAME

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
             "The `win98` demo layout is skipped by default.\n",
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
    text = "\n".join(lines) + "\n"
    print(text)
    if "--write" in sys.argv:
        os.makedirs(os.path.dirname(DOC), exist_ok=True)
        with open(DOC, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"written to {DOC}")


if __name__ == "__main__":
    main()
