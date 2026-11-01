# YangSpec

个人网站：YangSpec 在成都，用这个站点放近况、写下的东西和联系方式。中文为主，静态生成。

站点：<https://yangspec.com/> · 托管在 Cloudflare Pages，push 到 `main` 即生产发布，所以改动先走分支和预览。

## 页面结构

| 路径 | 内容 |
| --- | --- |
| `/` | 首页：署名、一句介绍、最新文章与站点说明 |
| `/posts/` | 文章：写下的东西，按日期倒序 |
| `/posts/<slug>/` | 文章正文：日期、正文与返回入口 |
| `/about/` | 关于：我是谁、这个站怎么来的、联系方式 |
| `/contact/` | 联系：邮箱与几条边界 |
| `/privacy/` | 隐私：本站处理哪些数据 |

导航在 `hugo.toml` 的 `[menu.main]` 里维护，加一项就多一个入口。

## 文档

- [docs/](docs/README.md)：维护者入口——架构、ADR、发布与故障手册
- [CONSTRAINTS.md](CONSTRAINTS.md)：什么算可发布，质量门槛与检查命令
- [AGENTS.md](AGENTS.md)：在这个仓库里工作的 agent 规则

## 本地开发

需要 Hugo Extended 0.167.0（生产构建的版本）。PaperMod 以普通文件放在 `themes/PaperMod`，不是 submodule，不需要初始化主题，也不需要装前端依赖。

```bash
hugo server                      # 本地预览，默认 http://localhost:1313
hugo --environment production    # 构建到 public/
HUGO_BIN=/path/to/hugo scripts/check.sh   # 构建 + 静态检查，/path/to/hugo 换成实际路径
```

构建时会出现一条 PaperMod 的 `.Language.LanguageCode` 弃用警告，不影响输出；升级 Hugo 前需要先确认主题兼容。

## 代码约定

- 模板在 `layouts/` 覆盖主题默认；文章与页面共用 `_partials/article.html`，页面、文章、列表与 404 共用 `_partials/page-header.html`，细节见 [docs/architecture.md](docs/architecture.md)。
- `assets/css/extended/personal.css` 是唯一的站点样式，改样式只改这一个文件。
- `params.city`、`params.email` 被多页共用；正文里的邮箱也必须与 `params.email` 一致。
- 图标由 `python3 scripts/make-icons.py <头像图片>` 生成，换图后重跑脚本，并把 `hugo.toml` 里 `[params.assets]` 的 `?v=` 加一。

## 旧内容归档

改版前这里有两个浏览器工具（图片附件处理、自托管容量规划）和几篇自托管指南。源码没有删除，整体移到了 `archive/legacy-tools-site/`，不进构建、不再对外提供。要恢复其中某个工具时，把对应文件移回原位即可，但需要重新检查测试与文案。

## 发布前检查

完整步骤见 [docs/ops/runbook.md](docs/ops/runbook.md)，最小检查如下：

- `scripts/check.sh` 通过：0 ERROR、仅一条已登记 WARN、全部检查项 PASS。
- 首页、文章列表、文章正文、关于、联系、隐私在 390 / 768 / 1440 px、深浅两套主题下排版正常。
- 键盘 Tab 能走完导航、正文链接和页脚，`跳到主要内容` 链接可用。
- 数据流有变化时，`/privacy/` 已同步更新。
