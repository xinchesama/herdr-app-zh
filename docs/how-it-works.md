# 工作方式

## 1. herdr-app 的界面从哪来

herdr-app 的窗口不是编译死的布局，而是配置目录里的一组 JavaScript：

```
<herdr-app home>/
  mods/<name>/main.js    面板、菜单、对话框
  frame/<name>/main.js   设置页、欢迎页、命令面板、反馈页
  layouts/<name>.json    窗口结构
```

界面是 hot reload 的：保存 JS，窗口约 1 秒内跟随。

home 的查找顺序：`HERDR_APP_HOME` → `$XDG_CONFIG_HOME/herdr-app` → `~/.config/herdr-app`。

## 2. 为什么改完会自己变回英文

`herdr-app/build.rs` 用 `include_bytes!` 把 `defaults/mods/**` 和 `defaults/frame/**` 编进 exe；每次启动 `mods::write_workspace()` → `sync_defaults()` 会：

- 用 exe 内置英文原文算 `shipped` 指纹；
- 与 `installed.json` 比对，不一致就把 mod 重命名成 `xxx-edited` 并装回英文原版；
- `frame/` 更直接：`remove_dir_all` 后重写。

所以改 `installed.json` 没用——基准永远来自 exe。配置层汉化只能"启动后重新应用"。

## 3. 替换引擎

`src/zh_engine.py` 是一个够用的 JS 词法器，不是正则替换：

- 识别行注释、块注释、单/双引号字符串、反引号模板、正则字面量（包括 `/['‘’]/g` 这种带引号的正则）；
- 只改字符串和模板的**静态片段**，代码、注释、表达式一律原样保留；
- 普通字符串：整串命中 `EXACT` 才替换，不做全局片段替换（避免翻掉命令 ID、路径、标识符）；
- 模板字符串：按 `${...}` 切段，只翻静态段；表达式内部递归处理（嵌套模板也能翻）；
- 解码/转义只处理 `\\ \" \' \n \t \uXXXX`；模板表达式部分绝不重新转义。

对 37 个原始文件做过无损往返：把源码切 token 再拼回去，byte-identical。

## 4. 词典

`src/zh_dict.py`：

- `EXACT`：整串映射，约 480 条，覆盖设置页、命令面板、欢迎页、反馈、worktree、添加机器、变更、空间、文件、菜单、选择器。
- `TEMPLATE_WORDS`：只作用于模板静态片段，例如 `agents → 个智能体`，让 `` `${n} agents` `` 变成 `n 个智能体`。
- 不翻译：品牌（Herdr）、字体名、按键名、Git 状态码（HEAD/AA/DD）、月份缩写、shell 命令，以及代码里用于判断的错误串（如 `cannot start sh: program not found`）。

## 5. 守护进程

`src/zh_watch.py`：

- 每秒扫描 `mods/`、`frame/` 的 `.js`；
- 用 `(mtime, size)` 缓存，没变就不读；
- 发现被重置成英文就重写（幂等）；
- `installed.json` 的 mtime 变化 = 应用重启/更新 → 清缓存，立刻全量重扫；
- 日志写到 `<herdr-app home>/zh-watch.log`，超过 512 KB 轮转成 `.old`。

启动瞬间仍有一个扫描间隔的英文窗口（默认 1 秒）；把 `HERDR_ZH_INTERVAL` 调到 0.3 可以缩短，但更费 CPU。

## 6. 验收

- `python src/verify_zh.py`：对每个 mod 跑 `herdr-app check`（加载并渲染一次），对每个 frame 文件跑 `node --check`。
- `python src/audit_zh.py`：扫描仍显示英文的界面文案，白名单（品牌/字体/按键/命令）与 `win98` 演示布局除外。

在 0.1.16 上：32 个文件、534 处文案；mods 21/21、frame 7/7 通过；白名单外残留 0。

## 7. 边界

- 不是源码级 i18n，无法做到"重启后仍持久"；本质是持续重新应用。
- Herdr 升级会带来新文案，需要补词条后重新 `--rebuild`。
- 不 fork、不改 exe、不碰指纹；这样升级不会把项目弄坏，代价是必须常驻一个进程。
