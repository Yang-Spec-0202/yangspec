# 架构决策记录（ADR）

记录“以后可能会被问为什么”的决定，不是日常改动日志。

## 什么时候写

影响维护方式、且推翻成本高的决定：托管方式、样式体系、内容结构、检查方式、隐私边界、依赖引入。单个页面的文案或样式微调不需要。

## 命名与状态

- 文件名：`NNNN-短横线标题.md`，四位递增，不复用编号。
- 状态：`提议`、`已采纳`、`已取代（被 NNNN 取代）`、`已废弃`。
- 只增不改：决定变了就新写一条，旧条目只更新状态，不重写历史。

## 索引

| 编号 | 决定 | 状态 |
| --- | --- | --- |
| [0001](0001-static-hugo-cloudflare-pages.md) | 静态 Hugo + Cloudflare Pages | 已采纳 |
| [0002](0002-single-stylesheet-two-themes.md) | 单一站点样式表 + CSS 变量双主题 | 已采纳 |
| [0003](0003-posts-section-and-article-component.md) | 文章独立 section + 共用 article 组件 | 已采纳 |

## 模板

新建 ADR 时复制 [template.md](template.md)，填完加到上面的索引。
