"""--review 模式：错题复习"""
from .utils import Color
from .progress import load_progress, get_wrong_problems, record_wrong_answer
from .quiz import run_quiz


def run_review_mode(subject: str, subjects: dict, all_problems: dict, persona: dict):
    """错题复习：按错误次数排序，逐一重做"""
    subj = subjects[subject]
    progress = load_progress(subject)
    wrong_problems = get_wrong_problems(progress, all_problems[subject])

    if not wrong_problems:
        print(f"\n{Color.GREEN}🎉 没有错题！全部已攻克。{Color.RESET}")
        return

    records = progress.get("wrong_records", {})
    print(f"\n{Color.BOLD}{Color.CYAN}📕 错题复习 — {subj['icon']} {subj['name']}{Color.RESET}")
    print(f"  共 {len(wrong_problems)} 道错题待复习")
    print(f"  按错误次数从多到少排序")
    print(f"{Color.DIM}{'─' * 50}{Color.RESET}")

    # 显示错题列表
    for i, p in enumerate(wrong_problems, 1):
        recs = records.get(p["id"], [])
        wrong_count = sum(1 for r in recs if not r["solved"])
        last_wrong = [r for r in recs if not r["solved"]]
        last_ans = last_wrong[-1]["user_answer"][:40] if last_wrong else ""
        status = f"{Color.RED}错{wrong_count}次{Color.RESET}"
        if last_ans:
            status += f"，上次答：{last_ans}"
        print(f"  {i}. [{p['topic']}] {p['question'][:50]}…  {status}")

    print(f"\n{Color.BOLD}开始逐一复习？{Color.RESET} {Color.DIM}(回车开始, q退出){Color.RESET} ", end="")
    try:
        choice = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    if choice in ("q", "quit", "退出", "n", "no"):
        return

    # 逐一复习
    reviewed = 0
    conquered = 0
    for p in wrong_problems:
        recs = records.get(p["id"], [])
        wrong_count = sum(1 for r in recs if not r["solved"])

        print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
        print(f"{Color.BOLD}📕 错题复习 ({reviewed + 1}/{len(wrong_problems)}){Color.RESET}")
        print(f"  之前错了 {Color.RED}{wrong_count} 次{Color.RESET}，加油攻克它！")

        # 显示上次错误的答案
        last_wrong = [r for r in recs if not r["solved"]]
        if last_wrong:
            last = last_wrong[-1]
            print(f"  上次答成：{Color.YELLOW}{last['user_answer']}{Color.RESET} ({last['date']})")

        # 用 run_quiz 处理单题
        run_quiz([p], subject, subjects, all_problems, loop_mode=False, persona=persona)

        # 检查是否攻克
        new_progress = load_progress(subject)
        new_recs = new_progress.get("wrong_records", {}).get(p["id"], [])
        new_solved = new_recs[-1]["solved"] if new_recs else False
        if new_solved:
            conquered += 1

        reviewed += 1

    # 总结
    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    print(f"{Color.BOLD}📕 复习完成！{Color.RESET}")
    print(f"  复习 {reviewed} 题，攻克 {Color.GREEN}{conquered}{Color.RESET} 题")
    if conquered < reviewed:
        print(f"  还有 {Color.RED}{reviewed - conquered}{Color.RESET} 题需要再练")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}\n")
