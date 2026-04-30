"""学习报告 — 周报/统计/趋势"""
from datetime import date, timedelta
from collections import defaultdict
from .utils import Color, DATA_DIR
from .progress import load_progress, show_mastery_stats


def run_report(subject: str, subjects: dict, all_problems: dict):
    """生成学习报告"""
    subj = subjects[subject]
    progress = load_progress(subject)
    name = subj["name"]
    icon = subj["icon"]

    total = progress["total_attempts"]
    first = progress["correct_first_try"]
    first_rate = (first / total * 100) if total > 0 else 0
    eventually = progress["correct_eventually"]
    ev_rate = (eventually / total * 100) if total > 0 else 0
    days = progress["days_done"]
    streak = progress["streak"]

    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    print(f"{Color.BOLD}{icon} {name} 学习报告{Color.RESET}")
    print(f"{Color.DIM}报告日期：{date.today().strftime('%Y年%m月%d日')}{Color.RESET}")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}")

    # ── 总体概览 ──
    print(f"\n{Color.BOLD}📊 总体概览{Color.RESET}")
    print(f"{'─' * 40}")
    print(f"  学习天数：{Color.BOLD}{len(days)}{Color.RESET} 天")
    print(f"  连续天数：{Color.BOLD}{streak}{Color.RESET} 天 🔥")
    print(f"  总答题数：{Color.BOLD}{total}{Color.RESET} 题")
    print(f"  首次正确率：{Color.GREEN if first_rate >= 60 else Color.YELLOW}{first_rate:.0f}%{Color.RESET} ({first}/{total})")
    print(f"  最终掌握率：{Color.GREEN if ev_rate >= 80 else Color.YELLOW}{ev_rate:.0f}%{Color.RESET} ({eventually}/{total})")

    # ── 本周趋势 ──
    _show_weekly_trend(progress)

    # ── 主题掌握度 ──
    show_mastery_stats(progress)

    # ── 错题攻克率 ──
    _show_conquest(progress)

    # ── 最近活动 ──
    _show_recent_activity(progress, all_problems[subject])

    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}\n")


def _show_weekly_trend(progress: dict):
    """显示最近7天的做题趋势"""
    days = progress["days_done"]

    # 从 wrong_records 统计每天的答题数
    records = progress.get("wrong_records", {})
    daily_count = defaultdict(lambda: {"total": 0, "correct": 0})
    for pid, recs in records.items():
        for r in recs:
            d = r["date"]
            daily_count[d]["total"] += 1
            if r["solved"]:
                daily_count[d]["correct"] += 1

    today = date.today()
    print(f"\n{Color.BOLD}📈 最近 7 天趋势{Color.RESET}")
    print(f"{'─' * 40}")

    has_data = False
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        day_name = ["一", "二", "三", "四", "五", "六", "日"][i]
        label = f"{'今天' if i == 0 else '昨天' if i == 1 else f'周{day_name}'}"
        count = daily_count.get(d, {})
        t = count.get("total", 0)
        c = count.get("correct", 0)
        rate = (c / t * 100) if t > 0 else 0

        if t > 0:
            has_data = True
            bar = "█" * min(t, 20) + "░" * (20 - min(t, 20))
            color = Color.GREEN if rate >= 70 else Color.YELLOW if rate >= 40 else Color.RED
            print(f"  {label} {color}{bar}{Color.RESET} {t}题 {color}{rate:.0f}%{Color.RESET}")
        else:
            print(f"  {label} {Color.DIM}暂无记录{Color.RESET}")

    if not has_data:
        print(f"  {Color.DIM}（本周暂无做题记录）{Color.RESET}")


def _show_conquest(progress: dict):
    """显示错题攻克情况"""
    records = progress.get("wrong_records", {})
    if not records:
        return

    total_wrong = 0
    conquered = 0
    for recs in records.values():
        for r in recs:
            if not r["solved"]:
                total_wrong += 1
            else:
                conquered += 1

    print(f"\n{Color.BOLD}📕 错题攻克率{Color.RESET}")
    print(f"{'─' * 40}")
    total = total_wrong + conquered
    if total > 0:
        pct = int(conquered / total * 100)
        bar_len = int(pct / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        c = Color.GREEN if pct >= 70 else Color.YELLOW if pct >= 40 else Color.RED
        print(f"  {c}{bar}{Color.RESET} {c}{pct}%{Color.RESET}")
        print(f"  已攻克 {Color.GREEN}{conquered}{Color.RESET} 题 / 待复习 {Color.RED}{total_wrong}{Color.RESET} 题")
    else:
        print(f"  {Color.DIM}暂无错题记录{Color.RESET}")


def _show_recent_activity(progress: dict, all_problems: list):
    """显示最近的答题活动"""
    records = progress.get("wrong_records", {})
    if not records:
        return

    # 收集所有活动并排序
    activities = []
    for pid, recs in records.items():
        for r in recs:
            p = next((x for x in all_problems if x["id"] == pid), None)
            if p:
                activities.append((r["date"], r["solved"], p["topic"], r.get("user_answer", "")))

    activities.sort(key=lambda x: x[0], reverse=True)
    recent = activities[:8]

    print(f"\n{Color.BOLD}📋 最近活动{Color.RESET}")
    print(f"{'─' * 40}")
    for date_str, solved, topic, answer in recent:
        icon = f"{Color.GREEN}✅{Color.RESET}" if solved else f"{Color.RED}❌{Color.RESET}"
        ans = f"（答：{answer[:15]}）" if answer and not solved else ""
        print(f"  {icon} {date_str[5:]} {topic} {Color.DIM}{ans}{Color.RESET}")
