"""闪卡模式 — 快速刷题，按回车看答案"""
from .utils import Color, latex_to_plain
from .progress import load_progress, save_progress, record_wrong_answer, show_mastery_stats
from .adaptive import update_ability
from .cache import get_all_problems, get_problems
from datetime import date, timedelta


def run_flash_mode(subject: str, subjects: dict, all_problems: dict, persona: dict):
    """闪卡刷题：显示题目→回车看答案→自评对错"""
    subj = subjects[subject]
    progress = load_progress(subject)
    today = str(date.today())
    done_ids = set()
    round_num = 1
    correct_count = 0
    wrong_count = 0

    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    print(f"{Color.BOLD}⚡ 闪卡刷题 — {subj['icon']} {subj['name']}{Color.RESET}")
    print(f"{Color.DIM}  看题 → 心里默答 → 回车看答案 → 自评对错{Color.RESET}")
    print(f"{Color.DIM}  适合考前快速过知识点{Color.RESET}")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}")

    # 获取题目
    problems = get_problems(subject, count=50)

    if not problems:
        # fallback
        problems = get_all_problems(subject)

    import random as rnd
    rnd.shuffle(problems)

    for problem in problems:
        if problem["id"] in done_ids:
            continue
        done_ids.add(problem["id"])

        print(f"\n{Color.BOLD}{Color.CYAN}{'─' * 50}{Color.RESET}")
        print(f"{Color.BOLD}📌 第 {round_num} 题 — {problem['topic']}{Color.RESET}")
        print(f"{'─' * 50}")

        # 显示题目
        q = latex_to_plain(problem["question"])
        for line in q.split("\n"):
            print(f"  {line}")

        # 按回车看答案
        print(f"\n{Color.DIM}（在心里默答，然后按回车看答案）{Color.RESET}", end="")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        # 显示答案
        answer = latex_to_plain(problem["answer"])
        print(f"\n{Color.BOLD}{Color.GREEN}✅ 答案：{Color.RESET} {answer}")

        # 自评
        print(f"\n{Color.DIM}你答对了吗？{Color.RESET} {Color.BOLD}(y/n/s=跳过/回车=下一题/q=退出){Color.RESET} ", end="")
        try:
            eval_input = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if eval_input in ("q", "quit", "退出", "qq"):
            break
        elif eval_input in ("y", "yes", "对", "对了"):
            correct_count += 1
            # 记录正确
            record_wrong_answer(progress, problem["id"], "", 0, solved=True)
            update_ability(progress, problem, 1, solved=True)
            print(f"  {Color.GREEN}✓ 已标记正确{Color.RESET}")
        elif eval_input in ("n", "no", "不", "不对", "错"):
            wrong_count += 1
            record_wrong_answer(progress, problem["id"], "", 0, solved=False)
            update_ability(progress, problem, 1, solved=False)
            print(f"  {Color.RED}✗ 已标记错误（可后用 --review 复习）{Color.RESET}")
        else:
            # 跳过，不记录
            pass

        round_num += 1

        # 进度保存
        if today not in progress["days_done"]:
            progress["days_done"].append(today)
            yesterday = date.today() - timedelta(days=1)
            if progress["last_date"] == str(yesterday):
                progress["streak"] += 1
            else:
                progress["streak"] = 1
            progress["last_date"] = today

        save_progress(progress, subject)

    # 结束统计
    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    total = correct_count + wrong_count
    if total > 0:
        rate = int(correct_count / total * 100)
        print(f"{Color.BOLD}⚡ 刷题完成！{Color.RESET}")
        print(f"  刷了 {round_num - 1} 题")
        print(f"  {Color.GREEN}✓ 正确 {correct_count}{Color.RESET}  {Color.RED}✗ 错误 {wrong_count}{Color.RESET}  {Color.DIM}正确率 {rate}%{Color.RESET}")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}\n")
