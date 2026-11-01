# YangSpec 工程文档

给维护者看的文档。站点内容在 `content/`；这里不参与 Hugo 构建，也不出现在线上。

最后复核：2026-11-01

## 按场景找

| 你要做什么 | 先看 |
| --- | --- |
| 第一次改模板或样式 | [architecture.md](architecture.md) |
| 发布、回滚、线上出问题 | [ops/runbook.md](ops/runbook.md) |
| 查历史发布与回滚点 | [ops/releases.md](ops/releases.md) |
| 做一个会影响以后的决定 | [adr/README.md](adr/README.md) |
| 确认“什么算可发布” | [../CONSTRAINTS.md](../CONSTRAINTS.md) |
| 用 agent 改这个仓库 | [../AGENTS.md](../AGENTS.md) |
| 站点页面与本地开发 | [../README.md](../README.md) |

## 目录

```
docs/
├── README.md          入口（本文件）
├── architecture.md    站点如何渲染、内容模型、部署
├── adr/               架构决策记录
└── ops/
    ├── runbook.md     发布、回滚、故障处理
    └── releases.md    每次生产部署的发布记录
```

## 维护约定

- 流程变了就改这里的文档，不另开一份“新流程.md”。
- 阈值和检查项只写在 `CONSTRAINTS.md`，这里链接过去，避免两处漂移。
- ADR 只增不改：决定被推翻时新写一条，并标注取代关系。
- 每次合并到 `main` 的生产部署，在 [ops/releases.md](ops/releases.md) 追加一条记录；完整检查输出留在 gitignored 的 `reports/`。
