# Changelog

## 0.1.0 — 2026-11-23

首个公开版本。

- 基于 JS 词法器的字符串替换引擎：只改字符串字面量，支持模板 `${...}` 与嵌套表达式。
- 约 480 条英→中词条，覆盖设置页、命令面板、欢迎页、反馈、worktree、添加机器、变更、空间、文件、菜单、选择器。
- `apply_zh.py`：增量应用、`--rebuild`、`--dry-run`、`--restore`。
- `zh_watch.py`：1 秒缓存扫描，应用重启后自动重新汉化。
- `audit_zh.py`、`verify_zh.py`：覆盖审计与全量验收。
- Windows 自启安装脚本，Linux systemd / macOS launchd 模板。
- 在 herdr-app 0.1.16 上验证：32 个文件、534 处；mods 21/21、frame 7/7；白名单外残留 0。
