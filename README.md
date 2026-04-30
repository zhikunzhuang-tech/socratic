# socratic 🧠

**苏格拉底互动学习** — CLI 交互式多学科练习工具

答错不直接给答案，用提问引导你思考。支持数学、英语、物理三科。

## 安装

```bash
cd ~/socratic
pip install -e .
```

## 用法

| 命令 | 说明 |
|------|------|
| `socratic` | 交互选择科目，自适应练题 |
| `socratic -s english` | 直接进入英语 |
| `socratic --solve` | 自由输入题目，AI 苏格拉底引导 |
| `socratic -g` | AI 自动生成新题 |
| `socratic -s math --stats` | 查看数学学习统计 |
| `socratic --version` | 显示版本 |

## 交互快捷键

| 按键 | 作用 |
|------|------|
| `你的答案` | 提交作答 |
| `h` / `提示` | 获取下一条苏格拉底引导 |
| `s` / `跳过` | 跳过此题，看完整解法 |
| `q` / `qq` | 退出 |

## 项目结构

```
~/socratic/
├── socratic/
│   ├── __init__.py      # 版本信息
│   ├── __main__.py      # python -m socratic
│   ├── cli.py           # 命令行入口
│   ├── problems.py      # 题库（数学24+英语10+物理10）
│   ├── quiz.py          # 交互答题循环
│   ├── adaptive.py      # 自适应难度系统
│   ├── generate.py      # AI 出题 (sgpt)
│   ├── solve.py         # 解题引导模式
│   ├── progress.py      # 进度持久化
│   └── utils.py         # 颜色、匹配工具
├── data/                # 学习进度 (自动创建)
└── pyproject.toml       # 项目配置
```
