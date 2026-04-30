"""进度持久化"""
import json
from pathlib import Path
from datetime import date
from .utils import Color, DATA_DIR


def get_progress_path(subject: str) -> Path:
    return DATA_DIR / f"progress_{subject}.json"


def load_progress(subject: str) -> dict:
    path = get_progress_path(subject)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, KeyError):
            pass
    return {
        "total_attempts": 0, "correct_first_try": 0,
        "correct_eventually": 0, "days_done": [],
        "streak": 0, "last_date": str(date.today()),
        "problem_history": {}, "mastery": {}, "ability": 0.5,
    }


def save_progress(progress: dict, subject: str):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    get_progress_path(subject).write_text(
        json.dumps(progress, ensure_ascii=False, indent=2)
    )


def show_mastery_stats(progress: dict):
    mastery = progress.get("mastery", {})
    if not mastery:
        return
    print(f"\n{Color.BOLD}{Color.CYAN}📈 主题掌握度{Color.RESET}")
    print(f"{'─' * 40}")
    for topic in sorted(mastery.keys(), key=lambda t: mastery[t]):
        score = mastery[topic]
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        pct = int(score * 100)
        c = Color.GREEN if pct >= 70 else Color.YELLOW if pct >= 40 else Color.RED
        print(f"  {c}{bar}{Color.RESET} {c}{pct:>2}%{Color.RESET}  {topic}")
    ability = progress.get("ability", 0.5)
    print(f"{'─' * 40}")
    print(f"  综合能力：{Color.BOLD}{int(ability * 100)}%{Color.RESET}")
    print(f"{'─' * 40}")


def show_stats(progress: dict, subject: str, subjects: dict):
    subj = subjects[subject]
    total = progress["total_attempts"]
    first = progress["correct_first_try"]
    rate = (first / total * 100) if total > 0 else 0
    days = len(progress["days_done"])
    print(f"\n{Color.BOLD}{Color.CYAN}📊 {subj['icon']} {subj['name']} 学习统计{Color.RESET}")
    print(f"{'━' * 40}")
    print(f"  📅 学习天数：{Color.BOLD}{days}{Color.RESET} 天")
    print(f"  🔥 连续天数：{Color.BOLD}{progress['streak']}{Color.RESET} 天")
    print(f"  📝 总答题数：{Color.BOLD}{total}{Color.RESET} 题")
    if total > 0:
        print(f"  ✅ 首次正确率：{Color.GREEN}{rate:.1f}%{Color.RESET} ({first}/{total})")
        ev = progress["correct_eventually"]
        print(f"  🎯 最终掌握率：{Color.GREEN}{(ev/total*100):.1f}%{Color.RESET} ({ev}/{total})")
    print(f"{'━' * 40}")
    show_mastery_stats(progress)
