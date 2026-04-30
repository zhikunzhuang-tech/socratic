# Socratic — 苏格拉底互动学习系统

## 快速上手

```bash
socratic                    # 选科目 → 自适应练题
socratic -s english         # 直接进英语
socratic --help             # 查看所有命令
```

---

## 一、练习模式

### 自适应练习（默认）
```
socratic
socratic -s math
socratic -s physics
socratic -s english
```
- 根据你的掌握度动态选题
- 弱项优先，强项偶尔复习
- 每道题答完追问"为什么"
- 做完一题问是否继续

### 每日一题
```
socratic --no-loop
```
- 按日期种子选题，同一天同一题
- 适合固定每天练一题的习惯

### 自由输入题目
```
socratic --solve
socratic -s english --solve
```
- 输入自己的题目
- AI 苏格拉底式一步步引导
- `h` 看提示，`s` 看完整解法

### AI 自动出题（两阶段流水线）
```
socratic -g
socratic -s physics -g
```
- **第一阶段（Idea Agent）**：AI 先做"出题规划"，分析已有缓存、确定具体考察点、避免重复出同类型题
- **第二阶段（Generator）**：基于 Idea Agent 的规划生成一道完整题目
- 含 3 层苏格拉底提示和常见错误分支
- 生成后缓存到本地，可重复使用
- 缓存不足时自动触发流水线补充

### 错题复习
```
socratic --review
socratic -s math --review
```
- 列出所有做错的题，按错误次数排序
- 逐一重新练习
- 记录"攻克"进度

### Book 互动章节
```
socratic --book 一元一次方程
socratic -s physics --book "牛顿第一定律"
```
- AI 生成完整学习章节
- 含概念讲解、要点总结、练习题
- 练习题自带苏格拉底引导

---

## 二、交互操作

### 答题时

| 输入 | 作用 |
|------|------|
| `你的答案` | 提交作答 |
| `h` / `提示` | 获取下一级苏格拉底引导 |
| `s` / `跳过` | 跳过此题，显示完整解法 |
| `q` / `qq` | 退出本次练习 |
| `Ctrl+C` | 强制中断 |
| 回车 | 在追问模式下跳过追问 |

### 继续/退出提示

| 输入 | 作用 |
|------|------|
| 回车 | 继续下一题 |
| `n` / `不` / `no` | 结束练习 |

---

## 三、助教人格

```bash
socratic                            # 默认标准
socratic -p gentle                  # 耐心型
socratic -p challenging              # 挑战型
socratic -p concise                 # 简洁型
```

| 风格 | 特点 |
|------|------|
| 🧑‍🏫 标准 | 苏格拉底式引导，平衡耐心与挑战 |
| 🌸 耐心 | 温柔鼓励，多给提示少给压力 |
| 🔥 挑战 | 高标准严要求，"不错，但这只是开始" |
| ⚡ 简洁 | 直奔主题，不多废话 |

---

## 四、知识库

答错时自动显示相关知识卡片：

```
📖 知识点：「一元一次方程」
  核心概念
  含有未知数的等式叫方程。解方程就是求未知数的值...
  常见误区
  移项忘记变号、去括号系数漏乘...
```

### 预生成知识卡片

```bash
socratic -s math --init-kb      # 生成数学全部知识卡片
socratic -s english --init-kb   # 生成英语
socratic -s physics --init-kb   # 生成物理
```

### 存储位置

```
~/socratic/data/knowledge/
├── math/
│   ├── 一元一次方程.md
│   ├── 全等三角形.md
│   └── ...
├── english/
│   └── ...
└── physics/
    └── ...
```

---

## 五、统计与进度

```bash
socratic -s math --stats        # 查看数学学习统计
socratic -s english --stats     # 查看英语统计
```

显示内容：
- 学习天数、连续天数
- 总答题数、首次正确率、最终掌握率
- 各主题掌握度图表
- 错题本攻克率

### 数据位置

```
~/socratic/data/
├── progress_math.json        # 数学进度
├── progress_english.json     # 英语进度
├── progress_physics.json     # 物理进度
├── knowledge/                # 知识库
│   ├── math/
│   ├── english/
│   └── physics/
└── generated/                # AI 生成题目缓存
    ├── math.json
    ├── english.json
    └── physics.json
```

---

## 六、浏览题库

```bash
socratic --list                     # 数学题库
socratic -s english --list          # 英语题库
socratic -s math --list             # 数学（等价）
socratic -s math --topic 方程 --list # 按主题过滤
```

---

## 七、科目与题目

| 科目 | 题目数 | 覆盖内容 |
|------|--------|----------|
| 🧮 数学 | 24 题 | 初一~初三：方程、几何、函数、概率、不等式 |
| 📖 英语 | 10 题 | 主谓一致、时态、介词、冠词、否定句、疑问句 |
| ⚛ 物理 | 10 题 | 重力、密度、运动、电路、光速、声速、比热容 |

题目由 AI 生成（`-g`）可无限扩充。Book 模式每次生成新的练习题。

---

## 八、快捷键一览

```
命令速查
═══════════════════════════════════════════
练习
  socratic                  自适应练习
  socratic --no-loop        每日一题
  socratic --solve          自由输题引导
  socratic -g               AI 出题
  socratic --review         错题复习
  socratic --book "主题"     互动章节

选项
  -s/--subject math|english|physics  指定科目
  -p/--persona default|gentle|challenging|concise  助教人格
  --grade 初一|初二|初三    指定年级
  --topic "主题"            按主题过滤
  --num N                   每轮 N 题
  --no-banner               简洁模式

信息
  --stats                   学习统计
  --list                    浏览题库
  --version                 版本号

知识库
  --init-kb                 预生成知识卡片

安装
  pip install -e .          安装/更新
  git pull                  从 GitHub 更新
═══════════════════════════════════════════
```

## 九、项目结构

```
~/socratic/
├── socratic/
│   ├── __init__.py     版本信息
│   ├── cli.py          命令行入口
│   ├── problems.py     题库（数学24+英语10+物理10）
│   ├── quiz.py         答题循环 + 追问模式
│   ├── adaptive.py     自适应难度
│   ├── book.py         Book 互动章节
│   ├── persona.py      助教人格
│   ├── generate.py     AI 出题
│   ├── solve.py        解题引导
│   ├── knowledge.py    RAG 知识库
│   ├── review.py       错题复习
│   ├── progress.py     进度持久化 + 统计
│   └── utils.py        颜色、LaTeX转纯文本、匹配
├── data/               学习数据（自动创建）
├── pyproject.toml      项目配置
└── README.md
```
