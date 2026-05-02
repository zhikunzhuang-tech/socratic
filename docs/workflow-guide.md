# Matt Pocock Skills 开发工作流速查

> 以 socratic 项目为例，总结常用技能的使用场景和流程。

---

## 零、项目初始化

> **前置条件**：任何项目第一次用这套技能前，必须先初始化。只需做一次。

### 流程

```bash
# 在 Hermes 里加载 setup 技能
hermes -s setup-matt-pocock-skills
```

然后在对话中，挨个回答 3 个问题：

| 问题 | 你要决定的事 | 推荐 |
|------|------------|------|
| **Issue tracker** | issue 存在哪？GitHub / GitLab / 本地 markdown？ | 个人项目选**本地 markdown**，多人协作选 **GitHub** |
| **Triage 标签** | 5 种标准状态用不用默认标签名？ | 第一次用直接**默认**，后续随时改 |
| **领域文档布局** | 单上下文（根目录 CONTEXT.md）还是多上下文（monorepo）？ | 普通项目选**单上下文** |

### 初始化后项目里会多出什么

```
your-project/
├── CLAUDE.md                   ← 追加 ## Agent skills 区块
├── docs/
│   └── agents/
│       ├── issue-tracker.md     ← 记录 issue tracker 类型和操作命令
│       ├── triage-labels.md     ← 记录 5 种标签的映射
│       └── domain.md            ← 记录 CONTEXT.md 放哪、ADR 放哪
```

### 为什么要先初始化

没有初始化时，跑 `/to-issues` 等技能，agent 不知道：
- issue 发 GitHub 还是写本地文件？→ 乱猜
- 标签叫什么名字？→ 贴一个不存在的标签
- 领域术语在哪？→ 找不到

做了初始化后，agent 直接读 `docs/agents/`：

> "这个项目用 GitHub Issues，走 `gh` CLI"
> "`ready-for-agent` 对应标签就叫 `ready-for-agent`"
> "CONTEXT.md 在根目录，改 `docs/agents/*.md` 就能改配置"

### 实战：socratic 项目初始化

```
/setup-matt-pocock-skills
  → 主动探索项目：发现是 GitHub 仓库，没有 CLAUDE.md / CONTEXT.md
  → 问你 3 个问题：
    Q1: Issue tracker？→ GitHub Issues
    Q2: 标签？→ 默认
    Q3: 文档布局？→ 单上下文
  → 产出：
    CLAUDE.md          ← 追加 Agent skills 区块
    docs/agents/*.md   ← 3 个配置文件
    CONTEXT.md         ← 待后续 grill 时填充
```

---

## 一、新功能 / 新模块

### 流程

```
设计讨论  →  需求文档  →  拆 Issue  →  选择 Issue  →  实现  →  维护
```

### 对应技能

| 阶段 | 技能 | 做啥 |
|------|------|------|
| **设计讨论** | `/grill-with-docs` | 对计划穷追猛打提问，统一术语，建立 `CONTEXT.md` + ADR |
| **需求文档** | `/to-prd` | 把对话共识写成 PRD，发到 GitHub Issues |
| **拆 Issue** | `/to-issues` | 拆成垂直切片（每个切片端到端完整），标注 AFK/HITL |
| **选择 Issue** | `/triage` | 查看待办，状态流转：needs-triage → ready-for-agent |
| **实现** | `/tdd` | 红-绿-重构，一次一个垂直切片 |
| **维护** | `/diagnose` / `/improve-codebase-architecture` / `/zoom-out` | 修 bug、重构、理解代码 |

### 实战：在 socratic 上加"常用命令"科目

```
/grill-with-docs
  → 质询：题目格式？缓存题量？闪卡还是问答？正向反向各半？
  → 产出：CONTEXT.md 统一术语

/to-prd
  → 合成 PRD → 发到 GitHub Issues

/to-issues
  → 拆成 3 个垂直切片：
     1. 科目注册 + 80 题缓存（AFK，可直接干）
     2. 闪卡模式适配 cmd 科目（AFK）
     3. 科目选择器显示适配（AFK）

/triage
  → 标 ready-for-agent → 开干
```

---

## 二、修 Bug

### 流程

```
建立反馈环  →  复现  →  假设  →  仪表化  →  修复  →  回归测试  →  清理
```

### 对应技能

| 阶段 | 技能 | 做啥 |
|------|------|------|
| **全流程** | `/diagnose` | 6 阶段调试，核心是**先建反馈环** |

**关键原则**：
- 反馈环是第一优先级 — 没有快速、确定的可复现信号，不要动代码
- 3-5 个假设排序后再测试，避免锚定第一个想法
- 每次只改一个变量
- 修复前先写回归测试（如果有正确的 seam），看它失败，再修复，看它通过
- 打完收工删掉所有 `[DEBUG-xxx]` 日志

---

## 三、重构 / 清理代码

### 流程

```
探索 → 列出候选 → 逐个讨论 → 深度化 → 验证
```

### 对应技能

| 阶段 | 技能 | 做啥 |
|------|------|------|
| **全流程** | `/improve-codebase-architecture` | 找"浅模块"→提出深度化方案 |
| **理解代码** | `/zoom-out` | 不熟悉某块代码时全局俯瞰 |

**核心概念**：
- **深模块**：小接口，大功能。调用者只需要知道很少就能用
- **浅模块**：接口和实现一样复杂。删掉它，复杂度只是转移到调用方
- **删除测试**：想象删掉这个模块，复杂度是消失还是分散到 N 个调用方？分散 = 它在干活

**实战：socratic 的 cache.py 问题**：
- 各科目出题逻辑散在一个大函数里
- 每加一个新科目就要改一大块代码
- 可考虑抽成出题策略类，每个科目独立实现

---

## 四、工具技能

| 技能 | 用途 | 怎么用 |
|------|------|--------|
| `/grill-me` | 轻量讨论（不需要写文档时） | 输入 `/grill-me` 后直接聊方案 |
| `/caveman` | agent 太啰嗦时省 token | 输入 `/caveman`，说"停"就恢复 |
| `/zoom-out` | 看不懂代码时让 agent 讲全貌 | 输入 `/zoom-out` 后问某块代码 |
| `/write-a-skill` | 把重复流程固化为 skill | 按模板创建 skill，下次直接用 |

---

## 五、几个要点

1. **先初始化项目** — `setup-matt-pocock-skills` 是第一步。做完它，其他技能才知道你的项目用什么基础设施
2. **先想清楚再做** — `/grill-with-docs` 是最常用的技能。磨刀不误砍柴工
3. **垂直切片** — 每个 issue 是一次完整端到端，不是只改一层
4. **AFK 优先** — 能写成 agent 能干的事，就别等人工
5. **反馈环优先** — debug 时不建好可复现信号，别动代码
6. **深模块** — 好的代码是小接口大功能，差的代码是接口和实现一样复杂

---

## 六、常用命令速查

```bash
# 在 Hermes 里加载 skill（当前会话）
/skill grill-with-docs
/skill tdd
/skill diagnose

# 在 Hermes 里启动时预加载
hermes -s tdd,diagnose,grill-with-docs

# 在 Claude Code 里直接用（已装好）
/grill-with-docs  # 或者 /tdd、/diagnose 等

# 管理 skills
/skills list      # 查看已安装
/skills search    # 搜索技能
```
