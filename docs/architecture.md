# 站点架构

## 一句话

Hugo 把 Markdown 和模板生成静态 HTML，Cloudflare Pages 托管；push `main` 即发布。没有服务端、数据库、账号系统，也没有运行时日志。

## 运行环境

- Hugo 0.167.0 **extended**（生产构建版本）。
- PaperMod 以普通文件放在 `themes/PaperMod`，不是 submodule，不需要初始化。
- 没有前端构建链：CSS/JS 由 Hugo 的 asset pipeline 合并、压缩、加指纹。
- 本机没有全局 `hugo` 时，检查脚本通过 `HUGO_BIN` 指到对应版本：

```bash
HUGO_BIN=/path/to/hugo scripts/check.sh
```

## 内容模型

| 内容 | 位置 | URL |
| --- | --- | --- |
| 固定页（关于、联系、隐私） | `content/*.md` | `/about/` 等 |
| 文章列表 | `content/posts/_index.md` | `/posts/` |
| 文章 | `content/posts/<slug>.md` | `/posts/<slug>/` |
| 归档页 | `content/archives/_index.md` | `/archives/` |

- Front matter 必填 `title`、`date`、`description`；`eyebrow` 控制页面眉标，文章不用它（眉标由日期生成）。
- 文章按日期倒序；`draft: true` 不进生产构建。列表每页篇数由 `hugo.toml` 的 `[pagination] pagerSize` 决定，取值与理由见 [adr/0004](adr/0004-pagination-archive-and-post-navigation.md)。
- `taxonomies` 为空：没有标签、分类页，这是有意为之，不是遗漏。
- 模板不硬编码邮箱、城市；一律取 `hugo.toml` 的 `params`，正文里出现的邮箱也必须与 `params.email` 一致。

## 渲染管线

- `layouts/baseof.html`：拼 `<head>`、站点页头、`main` block、页脚；`main` 由具体页面定义。
- 模板查找按 Hugo 规则，section 模板优先：`layouts/posts/single.html` 先于 `layouts/single.html`。
- 共用 partial：

| partial | 作用 |
| --- | --- |
| `header.html` / `footer.html` | 站点导航与页脚（页脚含归档入口） |
| `page-header.html` | 眉标 + 标题 + 描述（文章、列表、归档、404 共用） |
| `article.html` | 文章骨架：`article.page` + 页头 + 正文，可选文末 partial |
| `post-footer.html` | 文章底部的最后更新、上一篇/下一篇与返回链接 |
| `pagination.html` | 列表分页页码；只有一页时不输出 |
| `extend_head.html` | 额外 head 内容（当前为空） |

- 页面模板：`layouts/home.html`、`layouts/posts/list.html`、`layouts/posts/single.html`、`layouts/archives/list.html`、`layouts/single.html`、`layouts/404.html`。
- `/posts/` 用 `.Paginate` 分页；Hugo 生成 `/posts/page/<n>/`，其中 `/posts/page/1/` 是指向 `/posts/` 的别名。分页页不进 `sitemap.xml`，也不应被当成可索引页面。
- 文章页按日期给出上一篇（更早，`.PrevInSection`）与下一篇（更新，`.NextInSection`）；`lastmod` 与 `date` 不同才渲染“最后更新”。
- 归档页 `/archives/` 用 `GroupByDate "2006"` 按年倒序分组；`content/archives/_index.md` 的 `outputs: ["html"]` 让归档只产出 HTML，没有 `/archives/index.xml`。
- 表格由 `layouts/_markup/render-table.html` 包裹横向滚动容器；提示与区域名称为中文，窄屏可在框内左右滚动（`tabindex="0"` + `role="region"` 让其可聚焦、可键盘滚动）。
- RSS 由 Hugo 自动生成（首页与文章栏目），页面没有可见入口；需要时手动用 `/posts/index.xml`。归档页只输出 HTML，没有 RSS。

## 样式与脚本

- 唯一站点样式入口：`assets/css/extended/personal.css`，与 PaperMod 样式一起打包、压缩、指纹化。
- 颜色、间距、字体走 `:root` 自定义属性；深色主题由 `:root[data-theme="dark"]` 覆盖同名变量。新增组件只用变量，否则深色模式会漏。
- JS 只有 `assets/js/site.js`：主题切换 + `localStorage` 的 `pref-theme`；按钮名称用中文描述下一步动作，图标表示点击后的目标主题（亮色显示月亮、暗色显示太阳），无 JS 时静态名称仍然准确，正文、导航仍可用。
- 除已登记的两处外不新增 `!important`；确需使用必须注释原因。
- 图标由 `scripts/make-icons.py <头像图片>` 从头像生成并写入 `static/`；换图后重跑脚本，并递增 `hugo.toml` 里 `[params.assets]` 的 `?v=`。`safari-pinned-tab.svg` 是单色 Y 形蒙版，只用于 Safari 固定标签页；头像转单色蒙版会糊，暂不自动生成。

## 检查脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/check.sh` | 生产构建 + `check-docs.py`（文档链接、ADR、复核日期、阈值单一来源、密钥）+ `check.py`（必需页面、sitemap、站内链接、Front matter、身份字段、隐私扫描、占位、体积预算、分页结构、归档覆盖、上一篇/下一篇、最后更新）；`--full` 增加外链 |
| `scripts/check-record.sh [--full]` | 运行 `check.sh`，把完整输出、commit 与退出码存到 gitignored 的 `reports/`，供发布记录引用 |
| `scripts/preview-check.sh <url>` | Lighthouse 七条路由、安全头、`Set-Cookie`、第三方请求；localhost 自动跳过安全头 |
| `scripts/make-icons.py` | 从头像生成站点图标 |

发布记录的格式与追加规则见 [ops/releases.md](ops/releases.md)；没有 CI（`CONSTRAINTS.md` 第 6 节登记 2026-12-31 前接入），所有检查靠合并前手动执行。

## 输出与部署

- 构建产物在 `public/`（gitignored）；`static/` 里的文件原样发布，包括 `static/_headers` 的安全头配置。
- Cloudflare Pages：生产分支 `main`；PR 分支生成预览。
- 分支预览别名是 `<branch>.yangspec.pages.dev`；较长的分支名可能没有别名（返回 404），此时用部署哈希地址 `<hash>.yangspec.pages.dev`，链接在 PR 的 Cloudflare 检查里。
- 回滚用 Cloudflare 的部署回滚，不用 revert 抢时间；步骤见 `ops/runbook.md`。

## 隐私与数据流

- 源码不写 Cookie、不引第三方统计/字体/CDN 脚本；没有表单和账号。
- 访问统计只有 Cloudflare Web Analytics（边缘注入，不写 Cookie）；Cloudflare 侧的访问日志属于托管层。
- `localStorage` 只存主题偏好 `pref-theme`。
- 数据流一变，必须在同一次改动里更新 `/privacy/`。

## 已知边界

- 没有运行时日志、没有线上探针：静态站只能靠构建期检查、实验室检查和托管层的访问数据。
- Cloudflare 的项目设置不在本仓库，改 DNS、缓存、分析开关都要去控制台。
- Hugo 与主题升级需要手动确认兼容；当前有一条已登记的 PaperMod 弃用警告。
