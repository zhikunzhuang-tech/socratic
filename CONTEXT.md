# Socratic — 苏格拉底互动学习

CLI 交互式多学科练习工具，答错不直接给答案，用提问引导思考。

## Language

**题目 (Problem / Question)**:
一道包含问题、答案、主题、难度等字段的可练习条目。
_Avoid_: 问题卡、考题

**主题 (Topic / Module)**:
同一科目下的知识模块分组，如 Linux 基础命令、vi 编辑器。选题时先选主题，再在里面练题。
_Avoid_: 模块、单元

**闪卡模式 (Flashcard mode)**:
看题 → 自己想答案 → 回车看正确答案 → 自评对错。适合记忆类科目（生物、地理、常用命令）。
_Avoid_: 卡片模式

**缓存题 (Cached question)**:
预先存入题库的题目，数据从 `data/cache/` 读取。出题确定、可控制质量。
_Avoid_: 静态题、预制题

**AI 出题 (AI-generated question)**:
运行时由 AI 实时生成的题目，不做长期缓存。灵活但偶有质量波动。数学/英语/物理/语文用纯 AI 出题。
_Avoid_: 动态题

**正向题 (Forward question)**:
给出命令名，问其作用。如 `"ls -la 的作用是什么？"` → `"列出所有文件详情"`。
_Avoid_: 正向卡片

**反向题 (Reverse question)**:
给出一段场景描述，问对应的命令。如 `"想查看所有文件（含隐藏）详情，用什么命令？"` → `"ls -la"`。
_Avoid_: 反向卡片

**难度 (Difficulty)**:
基础（⭐）— 最常用的日常命令。进阶（⭐⭐）— 稍复杂但常用的操作。
_Avoid_: 等级、星级

## Subjects

| Key | Name | Mode | Bank |
|-----|------|------|------|
| math | 数学 | AI 实时出题 | 无缓存 |
| english | 英语 | AI 实时出题 | 无缓存 |
| physics | 物理 | AI 实时出题 | 无缓存 |
| chinese | 语文 | AI 实时出题 | 无缓存 |
| biology | 生物 | 闪卡 | 缓存题 |
| geography | 地理 | 闪卡 | 缓存题 |
| claude | Claude Code | 标准问答 | 缓存+AI |
| hermes | Hermes Agent | 标准问答 | 缓存+AI |
| cmd | 常用命令 | 闪卡 | 缓存+AI，80题基础题库 |

## Relationships

- 一个**科目**下有多个**主题**
- 一个**主题**下有多个**题目**
- 每个**题目**有且仅有一个**难度**
- **缓存题**可以被 AI 出题补充
- **正向题**和**反向题**在题库中各占一半

## Flagged ambiguities

- "模块" 在之前同时指 **主题** 和 Python 源文件 — 已解决：学习内容分组叫 **主题**，Python 文件叫模块（用通用编程术语）。
