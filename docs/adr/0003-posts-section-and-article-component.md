# 0003 文章独立 section + 共用 article 组件

- 状态：已采纳
- 日期：2026-10-30
- 相关：[../architecture.md](../architecture.md)、[../ops/runbook.md](../ops/runbook.md)

## 背景

站点原本只有关于、联系、隐私三个固定页。添加文章栏目时，文章页与固定页的骨架完全重复：眉标、标题、描述、正文容器；随后列表页和 404 也各自复制了一份页头。继续下去，任何排版调整都要改四处。

与此同时，文章需要固定页没有的东西：日期眉标、按时间倒序的列表、文末导航。

## 决定

- 文章放在 `content/posts/`，URL 为 `/posts/` 与 `/posts/<slug>/`。
- 文章使用 `layouts/posts/list.html`、`layouts/posts/single.html`；固定页继续用 `layouts/single.html`。
- 两者共用 `_partials/page-header.html` 和 `_partials/article.html`；文章独有的日期眉标、文末导航留在 posts 模板。
- 不启用标签与分类：`hugo.toml` 的 `taxonomies` 保持为空。

## 后果

- 新增文章不需要碰模板；新增页面类型也不会再复制一套骨架。
- 固定页保持独立 URL 与独立模板，不会因为“本质也是文章”而混进按时间排序的文章流。
- 首页最新文章用紧凑列表，不复用完整文章行——两者展示目的不同，强行复用会引入条件分支。
- 没有标签/分类页，文章一多就需要归档页和分页补位（`writing` 模块）。
- 文章列表的 RSS 仍自动生成，但页面没有可见订阅入口；需要时手动使用 `/posts/index.xml`。

## 重新评估的时机

- 文章超过 20 篇，或需要按主题组织，再评估标签/系列。
- 站内出现第二种结构化栏目（如 `/docs/`）时，复用 `article`/`page-header`，不为新栏目复制骨架。
