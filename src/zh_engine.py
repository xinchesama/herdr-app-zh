# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 herdr-app-zh contributors
"""herdr-app 界面文案替换引擎。

目标：只改 JS 里的**字符串字面量**，不碰代码、注释、正则和模板表达式。
上一版用 str.replace('"原文"', ...) 的写法有两个硬伤：
  1. 正则字面量里的引号（如 /['‘’]/g）会让简单的引号扫描错位；
  2. 模板字符串里带变量的文案（`${n} agents`）完全覆盖不到。

这里的做法是一个够用的 JS 词法器：识别行注释、块注释、单双引号字符串、
反引号模板和正则字面量，只对字符串/模板的静态片段做整串替换。
"""
import re

# ---------------------------------------------------------------- 词法

_REGEX_PREV = set("([{,;:!&|?=+-*%~^<>")
_REGEX_KEYWORDS = {
    "return", "typeof", "instanceof", "case", "in", "of", "new", "delete",
    "void", "do", "else", "yield", "await", "throw",
}


class Token:
    __slots__ = ("kind", "start", "end", "raw", "content")

    def __init__(self, kind, start, end, raw, content=None):
        self.kind = kind      # "str" | "tpl" | "code" | "comment" | "regex"
        self.start = start
        self.end = end
        self.raw = raw
        self.content = content


def _scan_string(src, i):
    q = src[i]
    j = i + 1
    buf = []
    n = len(src)
    while j < n:
        c = src[j]
        if c == "\\":
            buf.append(src[j:j + 2])
            j += 2
            continue
        if c == q:
            return j + 1, "".join(buf)
        buf.append(c)
        j += 1
    return n, "".join(buf)


def _scan_template(src, i):
    j = i + 1
    depth = 0
    n = len(src)
    while j < n:
        c = src[j]
        if c == "\\":
            j += 2
            continue
        if c == "$" and j + 1 < n and src[j + 1] == "{":
            depth += 1
            j += 2
            continue
        if c == "}" and depth:
            depth -= 1
            j += 1
            continue
        if c == "`" and depth == 0:
            return j + 1
        j += 1
    return n


def _scan_regex(src, i):
    j = i + 1
    n = len(src)
    in_class = False
    while j < n:
        c = src[j]
        if c == "\\":
            j += 2
            continue
        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            j += 1
            while j < n and src[j].isalpha():
                j += 1
            return j
        elif c == "\n":
            return j
        j += 1
    return n


def _regex_allowed(prev, last_word):
    if prev is None:
        return True
    if prev in _REGEX_PREV:
        return True
    return last_word in _REGEX_KEYWORDS


def tokenize(src):
    """把源码切成 token；code token 原样保留，用于无损重组。"""
    out = []
    i = 0
    n = len(src)
    prev = None
    last_word = ""
    word = []

    def flush_word():
        nonlocal last_word
        if word:
            last_word = "".join(word)
            word.clear()

    while i < n:
        c = src[i]
        if c in " \t\r\n":
            out.append(Token("code", i, i + 1, c))
            i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(Token("comment", i, j, src[i:j]))
            i = j
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(Token("comment", i, j, src[i:j]))
            i = j
            continue
        if c in "\"'":
            flush_word()
            j, content = _scan_string(src, i)
            out.append(Token("str", i, j, src[i:j], content))
            prev = c
            i = j
            continue
        if c == "`":
            flush_word()
            j = _scan_template(src, i)
            out.append(Token("tpl", i, j, src[i:j], src[i + 1:j - 1]))
            prev = "`"
            i = j
            continue
        if c == "/" and _regex_allowed(prev, last_word):
            flush_word()
            j = _scan_regex(src, i)
            out.append(Token("regex", i, j, src[i:j]))
            prev = "/"
            i = j
            continue
        if c.isalpha() or c in "_$":
            word.append(c)
        else:
            flush_word()
        out.append(Token("code", i, i + 1, c))
        prev = c
        i += 1
    flush_word()
    return out


# ---------------------------------------------------------------- 解码/转义

_ESC = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}


def unescape(raw):
    out = []
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c != "\\" or i + 1 >= n:
            out.append(c)
            i += 1
            continue
        e = raw[i + 1]
        if e in _ESC:
            out.append(_ESC[e])
            i += 2
        elif e == "u" and i + 5 < n:
            try:
                out.append(chr(int(raw[i + 2:i + 6], 16)))
                i += 6
            except ValueError:
                out.append(c)
                i += 1
        elif e == "x" and i + 3 < n:
            try:
                out.append(chr(int(raw[i + 2:i + 4], 16)))
                i += 4
            except ValueError:
                out.append(c)
                i += 1
        else:
            out.append(e)
            i += 2
    return "".join(out)


def escape(text, quote):
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == quote:
            out.append("\\" + quote)
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------- 翻译

def _lookup(text, table, words):
    if text in table:
        return table[text]
    stripped = text.strip()
    if stripped != text and stripped in table:
        lead = text[:len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        return lead + table[stripped] + trail
    if words and stripped in words and re.fullmatch(r"[A-Za-z][A-Za-z .,'’\-…]*", stripped):
        lead = text[:len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        return lead + words[stripped] + trail
    return None


def _split_template(content):
    """返回 [(静态片段, 表达式原文)]，最后一个表达式的值是 None。"""
    parts = []
    i = 0
    n = len(content)
    buf = []
    while i < n:
        if content[i] == "\\":
            buf.append(content[i:i + 2])
            i += 2
            continue
        if content[i] == "$" and i + 1 < n and content[i + 1] == "{":
            depth = 1
            j = i + 2
            while j < n and depth:
                if content[j] == "{":
                    depth += 1
                elif content[j] == "}":
                    depth -= 1
                j += 1
            parts.append(("".join(buf), content[i:j]))
            buf = []
            i = j
            continue
        buf.append(content[i])
        i += 1
    parts.append(("".join(buf), None))
    return parts


def translate_literal(content, table, words, quote):
    """翻译一个普通字符串字面量；没有命中返回 None。"""
    hit = _lookup(content, table, None)
    if hit is not None and hit != content:
        return hit
    return None


def translate_template(raw_content, table, words):
    """翻译模板字符串的静态片段，返回原始片段（未加反引号）；没变化返回 None。

    表达式 `${...}` 原样保留，绝不重新转义——否则嵌套模板里的反引号会被转成 \\`。
    """
    parts = _split_template(raw_content)
    changed = False
    out = []
    for text, expr in parts:
        if text:
            zh = _lookup(unescape(text), table, words)
            if zh is not None:
                out.append(escape(zh, "`"))
                changed = True
            else:
                out.append(text)
        if expr is not None:
            inner, n = translate_js(expr[2:-1], table, words)
            if n:
                out.append("${" + inner + "}")
                changed = True
            else:
                out.append(expr)
    return "".join(out) if changed else None


def translate_js(src, table, words=None):
    words = words or {}
    out = []
    changed = 0
    for tok in tokenize(src):
        if tok.kind == "str":
            quote = tok.raw[0]
            content = unescape(tok.content)
            zh = translate_literal(content, table, words, quote)
            if zh is not None and zh != content:
                out.append(quote + escape(zh, quote) + quote)
                changed += 1
                continue
        elif tok.kind == "tpl":
            new = translate_template(tok.content, table, words)
            if new is not None:
                out.append("`" + new + "`")
                changed += 1
                continue
        out.append(tok.raw)
    return "".join(out), changed


def ui_literals(src):
    """审计用：挑出像界面文案的字符串字面量（含模板静态片段）。"""
    found = []
    for tok in tokenize(src):
        if tok.kind == "str":
            text = unescape(tok.content)
            if is_ui_text(text):
                found.append((text, tok.raw[0] != "`"))
        elif tok.kind == "tpl":
            for text, _expr in _split_template(tok.content):
                text = unescape(text)
                if is_ui_text(text):
                    found.append((text, False))
    return found


def is_ui_text(t):
    t = t.strip()
    if len(t) < 2 or len(t) > 240:
        return False
    if not re.search(r"[A-Za-z]", t) or re.search(r"[\u4e00-\u9fff]", t):
        return False
    if re.match(r"^(https?:|\./|\.\./|/|mods/|frame/|icons/|data:|~/|[A-Za-z]:\\)", t):
        return False
    if re.search(r"\.(js|svg|png|json|md|ttf|otf|css|exe)$", t):
        return False
    if re.match(r"^[a-z0-9_.:/#-]+$", t):
        return False
    if ":" in t and " " not in t:
        return False
    return (" " in t) or t[0].isupper() or t.endswith((":", "…", "?", "!"))
