# YangSpec

个人网站：YangSpec 在成都，用这个站点放近况、写下的东西和联系方式。中文为主，静态生成。

站点：<https://yangspec.com/> · 托管在 Cloudflare Pages，push 到 `main` 即生产发布，所以改动先走分支和预览。

## 页面结构

| 路径 | 内容 |
| --- | --- |
| `/` | 首页：署名、一句介绍、关于与站点说明 |
| `/about/` | 关于：我是谁、这个站怎么来的、联系方式 |
| `/contact/` | 联系：邮箱与几条边界 |
| `/privacy/` | 隐私：本站处理哪些数据 |

导航在 `hugo.toml` 的 `[menu.main]` 里维护，加一项就多一个入口。

## 本地开发

需要 Hugo Extended 0.167.0（生产构建的版本）。PaperMod 以普通文件放在 `themes/PaperMod`，不是 submodule，不需要初始化主题，也不需要装前端依赖。

```bash
hugo server                 # 本地预览，默认 http://localhost:1313
hugo --environment production   # 构建到 public/
```

构建时会出现一条 PaperMod 的 `.Language.LanguageCode` 弃用警告，不影响输出；升级 Hugo 前需要先确认主题兼容。

## 代码约定

- `layouts/home.html`、`layouts/single.html`、`layouts/404.html` 是项目自带模板，覆盖主题默认。
- `assets/css/extended/personal.css` 是唯一的站点样式，Hugo 会与主题样式合并、压缩并加指纹。改样式只改这一个文件。
- `hugo.toml` 里的 `params.city` 与 `params.email` 被首页、关于页和页脚共用，改一处全站生效。
- 图标来自 GitHub 头像，由 `scripts/make-icons.py` 生成：`python3 scripts/make-icons.py avatar.jpg`。换头像后重跑脚本，不要手改 `static/` 里的图标。
- 换完图标要把 `hugo.toml` 里 `[params.assets]` 的 `?v=` 数字加一，否则浏览器和 CDN 会继续用缓存里的旧图。
- `safari-pinned-tab.svg` 是单色 Y 形蒙版，只用于 Safari 固定标签页；头像转单色蒙版会糊，暂不改。

## 旧内容归档

改版前这里有两个浏览器工具（图片附件处理、自托管容量规划）和几篇自托管指南。源码没有删除，整体移到了 `archive/legacy-tools-site/`，不进构建、不再对外提供。要恢复其中某个工具时，把对应文件移回原位即可，但需要重新检查测试与文案。

## 发布前检查

- `hugo --environment production` 无报错，输出页数与本页结构一致。
- 首页、关于、联系、隐私在 390 / 768 / 1024 / 1440 px 下排版正常，深浅色都看一遍。
- 键盘 Tab 能走完导航、正文链接和页脚，焦点环可见；`跳到主要内容` 链接可用。
- 站内链接没有 404，`sitemap.xml` 只包含上面四个页面。
- Cloudflare 的统计是托管层面注入的，不在本仓库里；如果启停或改了范围，同步更新 `/privacy/`。
