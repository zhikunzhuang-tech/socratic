"""--review 模式：错题复习"""
from .utils import Color, latex_to_plain
from .progress import load_progress, get_wrong_problems, save_progress, record_wrong_answer
from .adaptive import update_ability


def run_review_mode(subject: str, subjects: dict, all_problems: dict, persona: dict, flash: bool = False):
    """错题复习：按错误次数排序，逐一重做。flash=True 用闪卡模式（不输入答案）。"""
    subj = subjects[subject]
    progress = load_progress(subject)
    wrong_problems = get_wrong_problems(progress, all_problems[subject])

    if not wrong_problems:
        print(f"\n{Color.GREEN}🎉 没有错题！全部已攻克。{Color.RESET}")
        return

    records = progress.get("wrong_records", {})
    mode_tag = "⚡ 闪卡复习" if flash else "错题复习"
    print(f"\n{Color.BOLD}{Color.CYAN}📕 {mode_tag} — {subj['icon']} {subj['name']}{Color.RESET}")
    print(f"  共 {len(wrong_problems)} 道错题待复习")
    if flash:
        print(f"  模式：{Color.DIM}看题→回车看答案→自评对错（不输入答案）{Color.RESET}")
    else:
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

    print(f"\n{Color.BOLD}开始逐一复习？{Color.RESET} {Color.DIM}(回车开始, b/返回, q/退出){Color.RESET} ", end="")
    try:
        choice = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    if choice in ("b", "back", "返回"):
        from .cli import main
        main()
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

        last_wrong = [r for r in recs if not r["solved"]]
        if last_wrong:
            last = last_wrong[-1]
            print(f"  上次答成：{Color.YELLOW}{last['user_answer']}{Color.RESET} ({last['date']})")

        if flash:
            quit_early = not _review_flash_card(p, subject, progress)
        else:
            from .quiz import run_quiz
            run_quiz([p], subject, subjects, all_problems, loop_mode=False, persona=persona)
            quit_early = False

        # 检查是否攻克
        new_progress = load_progress(subject)
        new_recs = new_progress.get("wrong_records", {}).get(p["id"], [])
        new_solved = new_recs[-1]["solved"] if new_recs else False
        if new_solved:
            conquered += 1

        if quit_early:
            break

        reviewed += 1

        # 还有错题没复习完 → 询问是否继续
        if reviewed < len(wrong_problems):
            print(f"\n{Color.DIM}继续下一题？{Color.RESET} {Color.DIM}(回车继续 / q 退出){Color.RESET} ", end="")
            try:
                cont = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                cont = "q"
            if cont in ("q", "quit", "退出", "qq"):
                break

    # 总结
    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    print(f"{Color.BOLD}📕 复习完成！{Color.RESET}")
    print(f"  复习 {reviewed} 题，攻克 {Color.GREEN}{conquered}{Color.RESET} 题")
    if conquered < reviewed:
        print(f"  还有 {Color.RED}{reviewed - conquered}{Color.RESET} 题需要再练")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}\n")


def _review_flash_card(problem: dict, subject: str, progress: dict) -> bool:
    """单张错题闪卡：显示题目 → 回车看答案 → 自评对错。返回 True 继续，False 退出。"""
    q = latex_to_plain(problem["question"])
    for line in q.split("\n"):
        print(f"  {line}")

    print(f"\n{Color.DIM}（在心里默答，回车看答案 / q 退出）{Color.RESET}", end="")
    try:
        choice = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if choice in ("q", "quit", "退出", "qq"):
        return False

    answer = latex_to_plain(problem["answer"])
    print(f"\n{Color.BOLD}{Color.GREEN}✅ 答案：{Color.RESET} {answer}")

    while True:
        print(f"\n{Color.DIM}你答对了吗？{Color.RESET} {Color.BOLD}(y/n/q){Color.RESET} ", end="")
        try:
            eval_input = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False

        if eval_input in ("y", "yes", "对", "对了"):
            record_wrong_answer(progress, problem["id"], "", 0, solved=True)
            update_ability(progress, problem, 1, solved=True)
            save_progress(progress, subject)
            print(f"  {Color.GREEN}✓ 已攻克！{Color.RESET}")
            return True
        elif eval_input in ("n", "no", "不", "不对", "错"):
            record_wrong_answer(progress, problem["id"], "", 0, solved=False)
            update_ability(progress, problem, 1, solved=False)
            save_progress(progress, subject)
            print(f"  {Color.RED}✗ 继续加油{Color.RESET}")
            return True
        elif eval_input in ("q", "quit", "退出", "qq"):
            return False
