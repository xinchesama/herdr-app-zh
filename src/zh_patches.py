# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 herdr-app-zh contributors
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 herdr-app-zh contributors
"""代码级补丁：字典够不到的文字，用精确文本替换改掉。

为什么需要这一层：
  有些文案不是源码里的字面量，而是**运行时拼出来的**。典型两处——
    mods/help/main.js   label() 把命令 id 转成 "space select 1"
    frame/palette/main.js  titleOf() 把 "terminal.search" 拼成 "Search terminal"
  字典和审计都只看字面量，自然覆盖不到；只能改代码。

约定：
  * 补丁作用在**英文原文**上（--rebuild 时是备份里的原文），因此锚点是上游原文；
  * 锚点必须逐字符匹配，找不到就报错——上游改版时立刻暴露，而不是悄悄留下半英文界面；
  * 补丁注入的代码块包在 /* zh:protect */ ... /* /zh:protect */ 之间，
    引擎会整段跳过，避免把里面的英文键名（Recent/Tab/App…）当文案翻掉。
"""
import re


class PatchError(RuntimeError):
    pass


# 每项：file（相对 herdr-app home）、note、old、new、count（默认 1）
PATCHES = [
    # ------------------------------------------------------------------ 快捷键页
    {
        "file": "mods/help/main.js",
        "note": "快捷键分组标题",
        "mark": "[\"空间\", /^space\\./]",
        "old": """const GROUPS = [
  ["spaces", /^space\\./],
  ["tabs", /^tab\\./],
  ["panes", /^pane\\./],
  ["agents", /^agent\\./],
  ["terminal", /^terminal\\.|^send:/],
  ["window", /./],
];""",
        "new": """const GROUPS = [
  ["空间", /^space\\./],
  ["标签页", /^tab\\./],
  ["窗格", /^pane\\./],
  ["智能体", /^agent\\./],
  ["终端", /^terminal\\.|^send:/],
  ["窗口", /./],
];""",
    },
    {
        "file": "mods/help/main.js",
        "note": "命令 id → 中文名表，并重写 label()",
        "mark": "const LABELS = {",
        "old": """function label(action) {
  if (action.startsWith("send:")) return "type " + JSON.stringify(action.slice(5));
  const [name, arg] = action.split(":");
  const words = name.replace(/[._]/g, " ");
  return arg ? `${words} ${arg}` : words;
}""",
        "new": """/* zh:protect */
// 命令 id → 中文名。键与 keys.json 的 action 一致，带 ":" 的是带参数的写法。
const DIRECTIONS = { left: "左", right: "右", up: "上", down: "下" };
const SECTIONS = { terminal: "终端" };
const SENDS = { "\\u0017": "Ctrl+W（删前一词）", "\\u001bb": "Esc b（前移一词）", "\\u001bf": "Esc f（后移一词）" };
const LABELS = {
  "space.select": "切换到空间", "space.new": "新建空间", "space.rename": "重命名空间",
  "space.next": "下一个空间", "space.prev": "上一个空间", "space.close": "关闭空间",
  "tab.select": "切换到标签页", "tab.new": "新建标签页", "tab.rename": "重命名标签页",
  "tab.next": "下一个标签页", "tab.prev": "上一个标签页", "tab.close": "关闭标签页",
  "pane.go": "聚焦窗格", "pane.swap": "交换窗格", "pane.close": "关闭窗格", "pane.zoom": "缩放窗格",
  "pane.split:right": "向右分屏", "pane.split:down": "向下分屏",
  "agent.next": "下一个智能体", "agent.prev": "上一个智能体",
  "terminal.copy": "复制", "terminal.paste": "粘贴", "terminal.search": "搜索", "terminal.paste_image": "粘贴图片",
  "app.zoom_in": "放大", "app.zoom_out": "缩小", "app.zoom_reset": "重置缩放",
  "app.help": "快捷键", "app.settings": "设置", "app.palette": "命令面板", "app.quit": "退出",
  "layout.switch": "下一个布局", "layout.toggle:sidebar": "切换侧边栏",
  "mod.open:picker": "转到空间或标签页…",
};
/* /zh:protect */

function label(action) {
  if (action.startsWith("send:")) {
    const raw = action.slice(5);
    return "发送 " + (SENDS[raw] ?? JSON.stringify(raw));
  }
  const [name, arg] = action.split(":");
  const exact = LABELS[name + ":" + arg];
  if (exact) return exact;
  const zh = LABELS[name];
  if (!zh) {
    const words = name.replace(/[._]/g, " ");
    return arg ? `${words} ${arg}` : words;
  }
  return arg ? `${zh} ${DIRECTIONS[arg] ?? arg}` : zh;
}""",
    },
    {
        "file": "mods/help/main.js",
        "note": "过滤器同时匹配英文 action，中文化后仍可用英文搜",
        "mark": "|| k.action.includes(f)",
        "old": """    const all = keys().filter((k) => !f || k.keys.includes(f) || label(k.action).includes(f));""",
        "new": """    const all = keys().filter((k) => !f || k.keys.includes(f) || label(k.action).includes(f) || k.action.includes(f));""",
    },
    {
        "file": "mods/help/main.js",
        "note": "快捷键所属分区后缀 (terminal) → （终端）",
        "mark": "SECTIONS[k.section] ?? k.section",
        "old": """(k.section !== "global" ? `  (${k.section})` : "")""",
        "new": """(k.section !== "global" ? `  （${SECTIONS[k.section] ?? k.section}）` : "")""",
    },
    # ---------------------------------------------------------------- 命令面板
    {
        "file": "frame/palette/main.js",
        "note": "方向词/主题/布局/动态命令的中文映射表",
        "mark": "const ZH_GROUP = {",
        "old": """const GROUPS = ["Recent", "Tab", "Pane", "Space", "Layout", "Terminal", "Agent", "Window", "App"];""",
        "new": """const GROUPS = ["Recent", "Tab", "Pane", "Space", "Layout", "Terminal", "Agent", "Window", "App"];

/* zh:protect */
// 分组名、方向词、主题名、以及没在 NAMED 里起名的命令，统一在这里给中文。
const ZH_GROUP = { Recent: "最近", Tab: "标签页", Pane: "窗格", Space: "空间", Layout: "布局", Terminal: "终端", Agent: "智能体", Window: "窗口", App: "应用" };
const ZH_DIR = { left: "左", right: "右", up: "上", down: "下" };
const ZH_THEME = { graphite: "石墨", ink: "墨黑", moss: "苔绿", "atom-one-dark": "Atom One Dark" };
const ZH_CMD = {
  "terminal.select_all": "全选终端内容",
  "terminal.select": "选择终端文本",
  "terminal.clear_selection": "清除终端选择",
  "terminal.scroll": "滚动终端",
  "terminal.paste_image": "粘贴图片",
  "terminal.search": "搜索终端",
  "app.feedback": "发送反馈",
  "app.check_updates": "检查更新",
  "app.update_core": "更新 herdr-core",
  "app.update": "重启并更新",
};
/* /zh:protect */
const zhDir = (d) => ZH_DIR[d] ?? d;""",
    },
    {
        "file": "frame/palette/main.js",
        "note": "聚焦窗格的方向词",
        "mark": "聚焦窗格 ${zhDir(d)}",
        "old": """  ...["left", "right", "up", "down"].map((d) => ["pane.go", { direction: d }, "Pane", `Focus pane ${d}`, "move go"]),""",
        "new": """  ...["left", "right", "up", "down"].map((d) => ["pane.go", { direction: d }, "Pane", `聚焦窗格 ${zhDir(d)}`, "move go"]),""",
    },
    {
        "file": "frame/palette/main.js",
        "note": "交换窗格的方向词",
        "mark": "交换窗格 ${zhDir(d)}",
        "old": """  ...["left", "right", "up", "down"].map((d) => ["pane.swap", { direction: d }, "Pane", `Swap pane ${d}`, "move"]),""",
        "new": """  ...["left", "right", "up", "down"].map((d) => ["pane.swap", { direction: d }, "Pane", `交换窗格 ${zhDir(d)}`, "move"]),""",
    },
    {
        "file": "frame/palette/main.js",
        "note": "主题名与前缀",
        "mark": "主题：${ZH_THEME[n]",
        "old": """  ...["graphite", "ink", "moss", "atom-one-dark"].map((n) => ["app.theme", { name: n }, "App", `Theme: ${n.replace(/-/g, " ")}`, "colors look"]),""",
        "new": """  ...["graphite", "ink", "moss", "atom-one-dark"].map((n) => ["app.theme", { name: n }, "App", `主题：${ZH_THEME[n] ?? n.replace(/-/g, " ")}`, "colors look"]),""",
    },
    {
        "file": "frame/palette/main.js",
        "note": "动态命令的标题与分组（10 个未起名命令）",
        "mark": "ZH_CMD[name] ??",
        "old": """function titleOf(name) {
  const [noun, verb] = name.split(".");
  return { group: noun.charAt(0).toUpperCase() + noun.slice(1), title: `${verb.replace(/_/g, " ")} ${noun}`.replace(/^./, (c) => c.toUpperCase()) };
}""",
        "new": """function titleOf(name) {
  const [noun, verb] = name.split(".");
  const group = noun.charAt(0).toUpperCase() + noun.slice(1);
  return { group: ZH_GROUP[group] ?? group, title: ZH_CMD[name] ?? `${verb.replace(/_/g, " ")} ${noun}`.replace(/^./, (c) => c.toUpperCase()) };
}""",
    },
    {
        "file": "frame/palette/main.js",
        "note": "布局名与前缀",
        "mark": "布局：${t}",
        "old": """    const t = { main: "Herdr", terminals: "Terminals", win98: "Herdr 98" }[l] ?? l.charAt(0).toUpperCase() + l.slice(1);
    list.push({ name: "layout.switch", args: { name: l }, group: "Layout", title: `Layout: ${t}`, words: `look ${l}` });""",
        "new": """    const t = { main: "默认", terminals: "终端", win98: "Herdr 98" }[l] ?? l.charAt(0).toUpperCase() + l.slice(1);
    list.push({ name: "layout.switch", args: { name: l }, group: "Layout", title: `布局：${t}`, words: `look ${l}` });""",
    },
]


def patches_for(rel):
    key = rel.replace("\\", "/")
    return [p for p in PATCHES if p["file"] == key]


def patch_source(rel, src):
    """在英文原文上打补丁，返回 (新文本, 实际生效条数)。

    幂等：增量模式（不加 --rebuild）下文件可能已经打过补丁，
    此时 new 已存在而 old 不在，视为已应用，不报错。

    行尾：上游文件是 CRLF，锚点按 LF 书写；这里统一换算，写完再换回去。
    """
    crlf = "\r\n" in src
    if crlf:
        src = src.replace("\r\n", "\n")
    applied = 0
    for p in patches_for(rel):
        old, new = p["old"], p["new"]
        n = src.count(old)
        want = p.get("count", 1)
        if n == 0:
            # 增量模式：旧锚点已消失，但补丁痕迹还在（可能已被翻译），视为已应用
            if new in src or (p.get("mark") and p["mark"] in src):
                continue
        if n != want:
            raise PatchError(
                f'{rel}: 补丁「{p["note"]}」锚点匹配 {n} 次，应为 {want} 次。'
                "herdr-app 升级后原文变了，请更新 zh_patches.py。"
            )
        src = src.replace(old, new)
        applied += 1
    if crlf:
        src = src.replace("\n", "\r\n")
    return src, applied


def patchable_files():
    return sorted({p["file"] for p in PATCHES})


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("补丁清单：")
        for p in PATCHES:
            print(f'  {p["file"]:28s} {p["note"]}')
        print(f"\n共 {len(PATCHES)} 条，涉及 {len(patchable_files())} 个文件")
        sys.exit(0)

    # 自检：对备份原文逐条试打
    from pathlib import Path

    base = Path(sys.argv[1])
    bad = 0
    for rel in patchable_files():
        f = base / rel
        if not f.is_file():
            print(f"缺少原文: {rel}")
            bad += 1
            continue
        try:
            _, n = patch_source(rel, f.read_text(encoding="utf-8"))
            print(f"OK   {rel}  ({n} 条)")
        except PatchError as e:
            print(f"FAIL {e}")
            bad += 1
    sys.exit(1 if bad else 0)
