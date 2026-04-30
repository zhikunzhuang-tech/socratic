"""自适应难度系统"""
from collections import defaultdict
import random as rnd

MASTERY_GAIN_FIRST = 0.12
MASTERY_GAIN_LATER = 0.05
MASTERY_LOSS = 0.10


def get_topic_mastery(progress: dict, topic: str) -> float:
    return progress.get("mastery", {}).get(topic, 0.5)


def set_topic_mastery(progress: dict, topic: str, score: float):
    score = max(0.0, min(1.0, score))
    progress.setdefault("mastery", {})[topic] = score


def update_ability(progress: dict, problem: dict, attempts: int, solved: bool):
    topic = problem["topic"]
    diff = problem["difficulty"]
    cur = get_topic_mastery(progress, topic)
    if solved:
        gain = MASTERY_GAIN_FIRST + diff * 0.03 if attempts == 1 else MASTERY_GAIN_LATER + diff * 0.01
        cur += gain
    else:
        cur -= MASTERY_LOSS / diff
    set_topic_mastery(progress, topic, cur)
    topics = progress.get("mastery", {})
    progress["ability"] = round(sum(topics.values()) / len(topics), 3) if topics else 0.5


def pick_problems(problems: list, count=1, grade=None, topic=None, exclude_ids=None, seed=None):
    filtered = problems
    if grade:
        filtered = [p for p in filtered if p["grade"] == grade]
    if topic:
        filtered = [p for p in filtered if topic in p["topic"] or topic in p["tags"]]
    if exclude_ids:
        filtered = [p for p in filtered if p["id"] not in exclude_ids]
    if not filtered:
        return []
    if seed is not None:
        rnd.seed(seed)
    return rnd.sample(filtered, min(count, len(filtered)))


def pick_adaptive_problem(problems: list, progress: dict, done_ids: set, grade=None, topic=None):
    candidates = problems
    if grade:
        candidates = [p for p in candidates if p["grade"] == grade]
    if topic:
        candidates = [p for p in candidates if topic in p["topic"] or topic in p["tags"]]
    if done_ids:
        candidates = [p for p in candidates if p["id"] not in done_ids]
    if not candidates:
        return None

    by_topic = defaultdict(list)
    for p in candidates:
        by_topic[p["topic"]].append(p)

    topic_scores = {t: get_topic_mastery(progress, t) for t in by_topic}
    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1])

    weights = [max(0.2, 1.0 - s) for _, s in sorted_topics]
    topic_list = [t for t, _ in sorted_topics]
    total_w = sum(weights)
    r = rnd.random() * total_w if total_w > 0 else rnd.random()
    cumsum = 0
    chosen = topic_list[0]
    for i, t in enumerate(topic_list):
        cumsum += weights[i]
        if r <= cumsum:
            chosen = t
            break

    pool = by_topic[chosen]
    mastery = get_topic_mastery(progress, chosen)
    if mastery < 0.35:
        pool = [p for p in pool if p["difficulty"] == 1] or pool
    elif mastery < 0.55:
        pool = [p for p in pool if p["difficulty"] <= 2] or pool
    elif mastery < 0.75:
        hard = [p for p in pool if p["difficulty"] >= 2]
        if hard:
            pool = hard
    else:
        hard = [p for p in pool if p["difficulty"] >= 2]
        if hard:
            pool = hard
    return rnd.choice(pool)
