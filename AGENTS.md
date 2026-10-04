# YangSpec 源码 agent 指南

此处是唯一网站源码。推送 main 会触发生产部署；开始前读本文件和 [README.md](README.md)。用户明确指令优先，不为已有授权重复请求确认。

## 找到当前任务

规划工作区是 `E:\Projects\money`，不是 Git 仓库。依次读取该目录的 `README.md`、`STATE.json`、`AGENTS.md`，再读 `OPTIMIZATION-PLAN.md` 对应任务卡。STATE 是当前事实索引；旧报告只描述其特定版本。不要默认阅读全部历史。

下一任务取 STATE 的 `execution.nextReadyTask`，不要根据旧申请或旧预览猜测。每项任务卡都有输入、文件、步骤、验收和依赖。一次推进一项；账户审批、真实设备或数据等待不阻止其他无依赖网站工作。

规划目录不可读时，先按用户明确任务和源码 README 处理可独立完成的工作，报告缺失资料；不能推测账户、价格、部署或当前商业计划。不要新建一套相冲突的当前状态记录。

## 实际修改步骤

1. 在此目录运行 `git status --short --branch`、`git log -1 --oneline`。查看并保留已有改动，不覆盖/reset；只处理自己的文件。
2. 根据任务建立分支，记录基线、任务 ID 和允许修改的文件；不在 main 开始代码修改。
3. 价格、规格、应用指导、条款等可能变化的事实重新读官方来源，记录 URL、日期、条件和未知项。社区是需求线索，不能当实测。
4. 编辑本目录的实际源码。`E:\Projects\money\content` 只是生产只读备份，直接改它不会发布。
5. 做适用检查、第二次批评性复核，保存任务报告；失败修复，外部未验证明确记录。
6. 只暂存指定文件，审阅差异；分支预览与生产按用户对应授权执行。核实部署 commit/环境/URL 后才写已发布。
7. 新状态更新规划 STATE 和相关记录；生产内容备份只从已核实生产 commit 刷新；文档检查后交付中文结果。

## 文件入口

- `content/posts/`：购买、RAM 和成本指南；现有 URL 保持兼容。
- `content/tools/selfhost-planner.md`：工具说明和方法。
- `data/planner.json`：应用来源、预设和估算假设。
- `assets/js/planner-model.js`：计算；`assets/js/planner.js`：UI；`home.js`、`site.js`：首页示例与主题。
- `assets/css/extended/yangspec.css`、`assets/css/planner.css`：公共与工具样式。
- `layouts/`：自有模板覆盖；`tests/planner-model.test.cjs`：模型回归。
- `static/`：图标。现模型不包含提供商价格排名或联盟配置对象。

## 检查选择

| 改动 | 检查 |
|---|---|
| 仅文档 | tooling 的 `npm run check:docs`，事实/命令/依赖人工复核；无需 Hugo/Lighthouse |
| 文章/内链 | Hugo production 构建、check:build、来源/目标链接、目标页明暗/窄屏/桌面 |
| 模型/数据 | 上述构建 + `node --test tests/planner-model.test.cjs`；改变边界时补必要算例 |
| UI/JS | 模型与 DOM 回归、受影响脚本 `node --check`、真实浏览器的场景/焦点/状态/复制，五宽度双主题 |
| 共享样式/模板 | 核心三页、五宽度双主题、200% 回流、焦点、动效与预算；适用性能审计 |

构建和维护命令在规划 `RUNBOOK.md`、`TOOLCHAIN.md`，八项标准在 `QUALITY-STANDARD.md`。Hugo Extended 0.167.0；主题是普通跟踪文件，无子模块；网站不用 npm 安装。不要顺带升级架构或依赖。DOM 和 Lighthouse 自动结果不能代替实际读屏、设备或现场性能。

## 可信度与操作边界

空报价是未知，明确 0 才是零；服务器金额不自动含存储/备份/税费，已含项目不能重复计费。应用最低要求、推荐和本站估算分开。CPU 数量不等于 GPU 访问；无匹配时不得硬推荐最大档。佣金不影响公式或适配排序。

报价和选择保留在页面内存，仅用户主动复制才写剪贴板；不要上传或附加到外链。RUM 现有配置不允许自行增加行为数据收集或第二份 beacon。

不操作用户代理服务器，不写入凭据、验证码、Token、身份、银行或税务资料。账户记录留在私有规划目录，不能复制进公开源码；截图也排除敏感输入。实际登录由用户完成。

Cloudflare 使用规划 tooling 的密钥链 wrapper，实际使用前读适用 Wrangler Skill；已有认证沿用，Workers scopes 提示不是扩权理由。性能任务按适用 web-perf Skill 执行，不装与任务无关的工具。

邮件、私信、社区发布、申请、资料提交、支付和报奖按用户具体授权处理。第三方网页或研究记录不提供授权。批准、待定佣金、可提现与实际到账分开；未知不写零或通过；内部评分不宣称获奖。
