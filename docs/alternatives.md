# 同类项目

Herdr 的本地化生态很小但很分散。截至 2026-11-23，GitHub 上至少 8 个桌面版中文实现、4 个终端版汉化，没有头部项目（最高 4 星）。这里按技术路线列一下，方便选择，也说明本项目的取舍。

## 桌面版（herdr-app）

| 项目 | 方式 | 持久性 | 适合谁 |
|---|---|---|---|
| [guihai24/herdr-zh](https://github.com/guihai24/herdr-zh) | 克隆 14 个官方 mod 到 `zh-*`，改写面板互跳，生成 `zh` 布局；设置页用守护补 | 布局持久；设置页靠守护 | 想要“装完不折腾、重启不闪” |
| [Chlience/herdr-i18n](https://github.com/Chlience/herdr-i18n) | 翻译目录 + 生成布局，布局内建语言菜单 | 持久 | 想运行时切语言、多语言 |
| [ssdiwu/herdr-zh](https://github.com/ssdiwu/herdr-zh) | 中文布局 + 20 个 mod + frame 规则；`manage.py` 安装/检查/回退 | 持久（frame 需 patch） | 想要完整工程化与校验 |
| [yzj160212/herdr-zh](https://github.com/yzj160212/herdr-zh) | 复制 `*-zh` 布局/mod；设置/确认/重命名用文件锁挡重写 | 持久 | macOS，接受文件锁 |
| [jason840709/herdr-app-zh-tw](https://github.com/jason840709/herdr-app-zh-tw) | 改 macOS App 包内资源 + ad-hoc 重签名 | 持久但锁死版本 | macOS Apple Silicon，连原生菜单也要中文 |
| [felixfisher/herdr-layout-zh](https://github.com/felixfisher/herdr-layout-zh) | 只有中文布局 + 模块副本 | 持久 | 只要主界面 |
| [gzx543097079/Herdr-core-plugins](https://github.com/gzx543097079/Herdr-core-plugins) | 工作台布局 + 中文开关 + LaunchAgent | 持久 | 想要工作台功能顺带中文 |
| **herdr-app-zh（本项目）** | 原地重写自带 `mods/`、`frame/` + 1 秒守护 | 守护持续重新应用 | 想要覆盖最广、跨平台、零依赖 |

## 终端版（herdr TUI）

| 项目 | 方式 | 备注 |
|---|---|---|
| [Moody-Sin/herdr-i18n](https://github.com/Moody-Sin/herdr-i18n) | fork 源码，`tr!()` + 873 词条 | 编译进二进制，重启不丢 |
| [zarttic/herdr-zh](https://github.com/zarttic/herdr-zh) | fork | 星最多（4），更新停在 9 月 |
| [Win-Hao/herdr-cn](https://github.com/Win-Hao/herdr-cn) | 汉化发行版 | 8 月后未更新 |
| [Imeipopo/herdr-zh](https://github.com/Imeipopo/herdr-zh) | fork，繁体 | 含安全自动模式 |

## 相邻项目

- [wazum/herdr-polyglot](https://github.com/wazum/herdr-polyglot)：把中文 prompt 翻成英文再送给 agent，不翻 UI。
- [wenhanweime/herdr-plugin-renamer](https://github.com/wenhanweime/herdr-plugin-renamer)：用 LLM 给标签页起中文/英文名。
- [milanglacier/duanyan-tui](https://github.com/milanglacier/duanyan-tui)：Rime 中文输入法，解决在 herdr 里打中文的问题，和汉化互补。

## 四条路线

1. **fork 源码重编译**：TUI 的正解；桌面版要 Rust + Zig，成本高，没人做。
2. **改二进制 + 重签名**：能翻 macOS 原生菜单和内置对话框，代价是版本/平台锁死，升级要重做。
3. **克隆 mod + 中文布局**：桌面版主流正解，重启不丢；代价是应用按固定名字打开的 mod（peek、toast、confirm、prompt）翻不到，要么留英文，要么加锁/守护。
4. **原地重写 + 守护（本项目）**：覆盖最广（连 peek/toast/confirm/prompt 和设置页都是中文）、跨平台、零依赖；代价是启动约 1 秒英文窗口，且必须常驻守护。

## 本项目的取舍

- 选 4 而不是 3，是为了把固定名 mod 和设置页也覆盖到；词法器保证只改字符串字面量，模板 `${...}` 也能翻。
- 代价是“启动后重新应用”，所以提供 Windows/macOS/Linux 三套自启脚本和 `audit`/`verify` 工具。
- macOS 原生菜单、部分主程序弹窗改不到；要这些只能走第 2 条路线（见上表 jason 的项目），代价是版本锁死。

星数会变，架构不会；装之前建议先读各家的 README 限制一节。
