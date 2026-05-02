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

#### 第 1 步：/grill-with-docs

你的想法："我想加一个学习 Linux / vi / git 常用命令的功能。"

agent 会逐个追问：

```
Q1: 题目形式是什么？
     推荐：缓存 80 题 + AI 补充，命令知识固定，缓存更快更准

Q2: 分几个主题模块？
     Linux 基础命令(35题) / vi 编辑器(20题) / git 版本控制(25题)

Q3: 题目方向怎么分？
     正向 40 题（命令→用途："ls 的作用是什么？"）
     反向 40 题（场景→命令："想看到隐藏文件用什么？"）

Q4: 难度怎么分？
     基础 48 题（ls、cd、add、commit...）
     进阶 32 题（chmod、grep -r、merge、stash...）

Q5: 默认学习模式？
     闪卡（看题→默答→回车看答案→自评），和生物地理一样
```

每确定一个概念，agent 会更新 CONTEXT.md：
```
## Language
**正向题**：给出命令名，问其作用
**反向题**：给出场景，问对应命令
**闪卡模式**：看题→默答→看答案→自评
```

#### 第 2 步：/to-prd

agent 不会再次问你问题，而是直接综合之前对话中已经确定的内容，写出 PRD：

```
## 题目：为 socratic 新增"常用命令"科目

## Problem Statement
用户需要学习 Linux / vi / git 的常用命令，现有的科目体系没有覆盖。

## User Stories
1. 作为初学者，我想刷 Linux 基础命令，以便快速上手终端操作
2. 作为初学者，我想通过场景反推命令，以便真正能用起来
3. 作为 socratic 用户，我想从菜单中直接选择"常用命令"科目

## Implementation Decisions
- 新增科目 key: cmd，显示名"常用命令"
- 按模块分：Linux 基础命令 / vi 编辑器 / git 版本控制
- 缓存 80 题，正向反向各半，基础进阶分层
- 默认闪卡模式，走章节选择

## Out of Scope
- 不包含网络命令（curl/wget/ssh 等将来考虑）
```

然后 `gh issue create` 发布到 GitHub Issues，自动贴 `needs-triage` 标签。

#### 第 3 步：/to-issues

agent 展示切片方案，等你确认后再创建 issue：

```
Q: 以下是我建议的切片，您看粒度是否合适？

切片 1 (AFK): 科目注册 + 80 题缓存
  - 在 problems.py 注册 cmd 科目
  - 直接写入 data/cache/cmd.json（80 题手写，无需 AI 等待）
  - 被 切片 2 阻塞？否

切片 2 (AFK): cli.py / flash.py 适配 cmd 闪卡
  - cli.py 里 cmd 默认走闪卡
  - flash.py 里 cmd 支持按模块选章节
  - 被 切片 1 阻塞？是（科目必须先注册）

切片 3 (AFK): 科目选择器显示适配
  - select_subject() 里 cmd 显示"80 题"而不是"AI实时出题"
  - 被 切片 1 阻塞？是
```

你确认后，agent 按依赖顺序逐个发到 GitHub Issues，每个 issue 带 `# What to build`、`## Acceptance criteria`、`## Blocked by` 模板。

#### 第 4 步：/triage

```
/triage
  → agent 查 GitHub Issues → 展示 3 个待处理 issue
  → 你选一个：标 ready-for-agent → 开干
```

#### 第 5 步：/tdd

你想用 TDD 实现"闪卡模式适配 cmd"这个 issue。

```
/tdd
  → agent 问你要测什么行为
  → 你：cmd 进入时能选模块，刷题时能正确显示
  → RED: 先写测试 — 验证 flash.py 的章节选择能识别 cmd
  → GREEN: 改 flash.py 条件判断，把 cmd 加入章节选择逻辑
  → REFACTOR: 发现条件判断散在 3 处，可以统一抽成函数
  → 跑测试通过 → 下一个 RED
  → RED: 测试 cli.py 里 cmd 默认走闪卡路径
  → GREEN: cli.py 把 cmd 加入闪卡分支
  → ...
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

### 实战：闪卡模式下刷"常用命令"崩溃

假设用户反馈：`socratic -s cmd` 进去，选完章节后崩了，报错 `KeyError: 'alternatives'`。

#### Phase 1 — 建反馈环

这是最重要的阶段。agent 尝试多种方式建一个能快速复现的循环：

```
尝试 1：直接跑 socratic -s cmd → 需要手动交互，不能自动跑
尝试 2：写个 Python 脚本调用 flash.py 的 run_flash_mode → 可能可以
尝试 3：写个 pytest 测试，构造 cmd 题库数据跑闪卡循环
  → 成功！2 秒跑完，稳定复现 KeyError
  → 反馈环：pytest test_flash_cmd.py
```

反馈环建好前，**不动任何代码**。

#### Phase 2 — 复现

```
运行 pytest test_flash_cmd.py
→ 确认报错 KeyError: 'alternatives'
→ 确认是用户说的那个 bug，不是周边别的 bug
→ 确认反复跑都能复现
```

#### Phase 3 — 假设

agent 一次性列出 3-5 个假设，**不急着试第一个**：

```
假设 1：flash.py 里 _show_explanation() 访问了 problem['alternatives']，
        但 cmd 的题目没有 alternatives 字段
假设 2：生物/地理的种子题有 alternatives 字段，cmd 的没有
假设 3：闪卡模式走到 "e"（讲解）分支时报错
```

#### Phase 4 — 仪表化

```
验证假设 1：看 _show_explanation() 代码 → 确实没用到 alternatives
验证假设 2：看 cmd 种子题 → 仅有 "alternatives":[]，不影响
验证假设 3：traceback 指向 flash.py 的 ... → 确认是假设 1
```

#### Phase 5 — 修复 + 回归测试

```
修复前先写回归测试（确认它会失败）
→ 修复 flash.py：_show_explanation() 里访问 alternatives 前加 .get()
→ 看回归测试通过
→ 再跑一次 Phase 1 的反馈环验证原始 bug 消失
```

#### Phase 6 — 清理

```
[ ] 原始 bug 不再复现（重跑反馈环）
[ ] 回归测试已通过并提交
[ ] 所有 [DEBUG-xxx] 日志已删除
[ ] 临时脚本已删除
[ ] commit message 说明正确假设是什么
```

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

### 核心概念

- **深模块**：小接口，大功能。调用者只需要知道很少就能用
- **浅模块**：接口和实现一样复杂。删掉它，复杂度只是转移到调用方
- **删除测试**：想象删掉这个模块，复杂度是消失还是分散到 N 个调用方？分散 = 它在干活

### 实战：重构 socratic 的 cache.py

#### 第 1 步：/improve-codebase-architecture

agent 走一遍探索：

```
→ 读 CONTEXT.md 了解术语（题目、主题、缓存题、AI出题）
→ 读 docs/adr/（没有，跳过）
→ 读 cache.py
→ 发现：cache.py 里 _generate() 是一个 400 行的大函数
   if subject == "claude": ...
   if subject == "hermes": ...
   每个科目都在这里硬编码
→ 删除测试：删掉 _generate()，复杂度不会消失，会分散到各个调用方
→ 结论：这是一个**浅模块** — 加了太多科目的特殊逻辑，接口复杂
```

#### 第 2 步：列出候选给用户选

```
候选 1：抽取出题策略类
  - 问题：每加一个新科目就要改一个大函数
  - 方案：每个科目独立一个生成策略类，_generate() 按 subject 分发
  - 好处：新科目只加一个文件，不影响已有的

候选 2：统一题目字段校验
  - 问题：每个科目的 seed 题格式不完全一致
  - 方案：Pydantic model 统一校验
  - 好处：运行时更早发现字段缺失

请选择想深入哪个？
```

#### 第 3 步：你选了候选 1，进入深度化讨论

```
→ 讨论接口设计：GeneratorStrategy(base) → ClaudeGenerator、HermesGenerator...
→ 更新 CONTEXT.md：新增术语 "出题策略"、"策略分发"
→ 你拒绝了一个方案（把所有生成结果聚合成一个大列表），offer ADR：
   "要记录这条做个 ADR 吗？防止以后有人再踩这个坑。"
→ 更新 CONTEXT.md、实现、测试
```

### 配套：/zoom-out

```
/zoom-out
  → "自适应系统 adaptive.py 我不熟悉"
  → agent 跳出来给全局地图：

  自适应系统由 3 部分组成：
  1. ability.py — 维护每个 topic 的能力估值（使用 Elo 评分）
  2. pick_problems() — 选题时优先选 ability 最低的话题
  3. update_ability() — 每题答完后更新评分

  对应关系：
  adaptive.py → 选题策略
  progress.py → 进度追踪
  cache.py → 题目来源
```

---

## 四、工具技能

| 技能 | 用途 | 怎么用 |
|------|------|--------|
| `/grill-me` | 轻量讨论（不需要写文档时） | 输入 `/grill-me` 后直接聊方案，不会写 CONTEXT.md 和 ADR |
| `/caveman` | agent 太啰嗦时省 token | 输入 `/caveman`，agent 省掉所有客套话。说"停"或"normal mode"恢复 |
| `/zoom-out` | 看不懂代码时让 agent 讲全貌 | 输入 `/zoom-out` 后问某块代码，agent 跳出细节给全局视角 |
| `/write-a-skill` | 把重复流程固化为 skill | 描述需求 → agent 创建 SKILL.md → 下次直接在 Hermes 里用 |

### 实战：用 /caveman

```
你：我们闪卡里正确答案显示样式太丑了，我想改一下
    （正常回答很啰嗦）

你：/caveman
你：闪卡答案样式太丑，改好看点
    （agent 用压缩模式回答）

→ 你做完后：stop caveman
→ agent 恢复正常语气
```

### 实战：用 /write-a-skill

你发现每次加新科目都要改 4 个文件，很烦：

```
你在 Hermes 里：
/write-a-skill
  → 描述：我想创建一个 skill，自动在 socratic 项目里加一个新科目：
     - problems.py 加一条 SUBJECTS 记录
     - cache.py 加 SUBJECT_NAMES / SUBJECT_TAGS / SEEDS
     - cli.py 处理新科目的模式选择
     - 生成 N 题缓存的空模板
  → agent 创建 SKILL.md
  → 下次加科目 -> /skill add-socratic-subject -> 自动配好
```

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

### 技能调用方式

```
/技能名           ← 直接输，不带参数
/技能名 + 描述    ← 某些技能需要一句话描述
```

**规则**：
- 设计类技能（`/grill-with-docs`、`/grill-me`、`/tdd`、`/diagnose`）：**直接输 `/技能名`**，然后 agent 会主动问你问题
- 综合类技能（`/to-prd`）：先聊完再输 `/to-prd`，agent 直接综合已有内容，**不会再次问你**
- 带参数技能（`/triage`、`/zoom-out`）：可以加一句话描述，也可以先 `/技能名` 再对话

### 各技能触发方式速查

| 技能 | 正确用法 | 触发后 |
|------|---------|--------|
| `/grill-with-docs` | `/grill-with-docs` | 逐个问你问题，直到设计清晰 |
| `/grill-me` | `/grill-me` | 同上，但不会写文档 |
| `/tdd` | `/tdd` | 问你测什么行为，走红-绿-重构 |
| `/diagnose` | `/diagnose` | 问你什么 bug，开始 6 阶段调试 |
| `/to-prd` | 先讨论完，再输 `/to-prd` | 不问你，综合对话内容直接写 PRD |
| `/to-issues` | 先有方案，再输 `/to-issues` | 展示切片方案等你确认 |
| `/triage` | `/triage 看看有什么待办的` | 按描述查 issue / 管理状态 |
| `/zoom-out` | `/zoom-out 我不懂 adaptive.py` | 跳出细节，给全局视角 |
| `/caveman` | `/caveman` | 切换省 token 模式，说 stop 恢复 |
| `/setup-matt-pocock-skills` | `/setup-matt-pocock-skills` | 探索项目 → 问你 3 个问题 |

### 命令行启动方式

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
