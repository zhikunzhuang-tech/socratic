"""AI 自动出题 (sgpt)"""
import json as j
import random as rnd
import subprocess as sp
import time
from pathlib import Path
from .utils import DATA_DIR

GENERATED_DIR = DATA_DIR / "generated"
SUBJECT_NAMES = {"math": "数学", "english": "英语", "physics": "物理"}
SUBJECT_TAGS = {"math": "math", "english": "eng", "physics": "phy"}


def get_cached_generated(subject: str) -> list:
    path = GENERATED_DIR / f"{subject}.json"
    if path.exists():
        try:
            return j.loads(path.read_text())
        except Exception:
            pass
    return []


def save_cached_generated(subject: str, problems: list):
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    (GENERATED_DIR / f"{subject}.json").write_text(j.dumps(problems, ensure_ascii=False, indent=2))


def get_available_topics(subject: str, all_problems: dict) -> list:
    topics = set()
    for p in all_problems.get(subject, []):
        topics.add(p["topic"])
    return sorted(topics)


def generate_problem(subject: str, all_problems: dict, topic: str | None = None) -> dict | None:
    """调用 sgpt 生成一道新题"""
    name = SUBJECT_NAMES.get(subject, "数学")
    tag = SUBJECT_TAGS.get(subject, "gen")

    if not topic:
        topics = get_available_topics(subject, all_problems)
        topic = topics[len(topics) // 2] if topics else "综合"

    timestamp = int(time.time())
    rnd.seed(timestamp)
    difficulty = rnd.choice([1, 2, 3])

    prompt = (
        f"你是一位中国初中{name}老师。请出一道针对初中生的{name}练习题。\n"
        f"主题：{topic}。难度：{'简单' if difficulty == 1 else '中等' if difficulty == 2 else '较难'}({difficulty}/3)。\n"
        "输出一行JSON（不要换行，不要markdown），格式：\n"
        f'{{"id":"{tag}-gen-{timestamp}","topic":"{topic}","grade":"{"初一" if difficulty<=1 else "初二" if difficulty<=2 else "初三"}","difficulty":{difficulty},'
        '"question":"题目","answer":"正确答案","alternatives":["备选1"],"steps":["步骤1","步骤2"],'
        '"socratic_hints":["提示1","提示2","提示3"],"common_errors":{"错1":"反馈1","错2":"反馈2","错3":"反馈3"},'
        '"tags":["自动生成"],"concept_note":"一句话总结"}\n'
        "注意：socratic_hints必须3条，common_errors至少3条。只输出JSON。"
    )

    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        problem = j.loads(text)
        required = ["id", "question", "answer", "steps", "socratic_hints", "common_errors"]
        if not all(f in problem for f in required):
            return None
        problem.setdefault("topic", topic)
        problem.setdefault("grade", "初二")
        problem.setdefault("difficulty", 2)
        problem.setdefault("alternatives", [])
        problem.setdefault("tags", [topic, "自动生成"])
        problem.setdefault("concept_note", "")
        # 清理 LaTeX（AI 生成的题目可能包含 \frac 等无效格式）
        from .utils import latex_to_plain
        problem["question"] = latex_to_plain(problem.get("question", ""))
        problem["answer"] = latex_to_plain(problem.get("answer", ""))
        problem["concept_note"] = latex_to_plain(problem.get("concept_note", ""))
        problem["steps"] = [latex_to_plain(s) for s in problem.get("steps", [])]
        problem["socratic_hints"] = [latex_to_plain(h) for h in problem.get("socratic_hints", [])]
        problem["common_errors"] = {k: latex_to_plain(v) for k, v in problem.get("common_errors", {}).items()}
        while len(problem.get("socratic_hints", [])) < 3:
            problem["socratic_hints"].append("再想想，你离答案很近了！")

        cached = get_cached_generated(subject)
        if not any(p["id"] == problem["id"] for p in cached):
            cached.append(problem)
            save_cached_generated(subject, cached)
        return problem
    except Exception:
        return None
