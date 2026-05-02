"""科目配置 + 题库入口（题目通过 cache.py 动态获取）"""
from .cache import get_problems, get_all_problems, get_topics

SUBJECTS = {
    "math":    {"name": "数学", "icon": "🧮", "emoji": "📐", "grades": "初一~初三", "tag": "math"},
    "english": {"name": "英语", "icon": "📖", "emoji": "🔤", "grades": "初一~初三", "tag": "eng"},
    "physics": {"name": "物理", "icon": "⚛", "emoji": "🔬", "grades": "初二~初三", "tag": "phy"},
    "chinese": {"name": "语文", "icon": "📜", "emoji": "🖋", "grades": "初一~初三", "tag": "chn"},
    "biology": {"name": "生物", "icon": "🧬", "emoji": "🧬", "grades": "初二", "tag": "bio"},
    "geography": {"name": "地理", "icon": "🌍", "emoji": "🌏", "grades": "初二", "tag": "geo"},
    "claude":  {"name": "Claude Code", "icon": "🤖", "emoji": "🤖", "grades": "入门~高级", "tag": "claude"},
    "hermes":  {"name": "Hermes Agent", "icon": "⚡", "emoji": "⚡", "grades": "入门~高级", "tag": "hermes"},
    "cmd":     {"name": "常用命令", "icon": "💻", "emoji": "💻", "grades": "入门~熟练", "tag": "cmd"},
}
SUBJECT_KEYS = list(SUBJECTS.keys())
SUBJECT_NAMES = {v["name"]: k for k, v in SUBJECTS.items()}

# 兼容接口：ALL_PROBLEMS[subject] 返回科目所有题目
class _DynamicProblems:
    def __getitem__(self, subject):
        return get_all_problems(subject)
    def get(self, subject, default=None):
        try:
            return self[subject]
        except Exception:
            return default
    def keys(self):
        return SUBJECT_KEYS
    def __len__(self):
        return len(SUBJECT_KEYS)
    def __iter__(self):
        return iter(SUBJECT_KEYS)

ALL_PROBLEMS = _DynamicProblems()
