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

    problems = get_problems(subject, count=50)
    if not problems:
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

        q = latex_to_plain(problem["question"])
        for line in q.split("\n"):
            print(f"  {line}")

        print(f"\n{Color.DIM}（在心里默答，然后按回车看答案）{Color.RESET}", end="")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        answer = latex_to_plain(problem["answer"])
        print(f"\n{Color.BOLD}{Color.GREEN}✅ 答案：{Color.RESET} {answer}")

        # 自评 + AI 讲解循环
        while True:
            print(f"\n{Color.DIM}你答对了吗？{Color.RESET} {Color.BOLD}(y/n/e=讲解/s=跳过/q=退出){Color.RESET} ", end="")
            try:
                eval_input = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                eval_input = "q"

            if eval_input == "e":
                _show_explanation(subject, problem)
                continue
            if eval_input in ("q", "quit", "退出", "qq"):
                return
            if eval_input in ("y", "yes", "对", "对了"):
                correct_count += 1
                record_wrong_answer(progress, problem["id"], "", 0, solved=True)
                update_ability(progress, problem, 1, solved=True)
                print(f"  {Color.GREEN}✓ 已标记正确{Color.RESET}")
            elif eval_input in ("n", "no", "不", "不对", "错"):
                wrong_count += 1
                record_wrong_answer(progress, problem["id"], "", 0, solved=False)
                update_ability(progress, problem, 1, solved=False)
                print(f"  {Color.RED}✗ 已标记错误（可后用 --review 复习）{Color.RESET}")
            break

        round_num += 1

        if today not in progress["days_done"]:
            progress["days_done"].append(today)
            yesterday = date.today() - timedelta(days=1)
            progress["streak"] = (progress["streak"] + 1) if progress["last_date"] == str(yesterday) else 1
            progress["last_date"] = today

        save_progress(progress, subject)

    total = correct_count + wrong_count
    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    if total > 0:
        rate = int(correct_count / total * 100)
        print(f"{Color.BOLD}⚡ 刷题完成！{Color.RESET}")
        print(f"  刷了 {round_num - 1} 题")
        print(f"  {Color.GREEN}✓ 正确 {correct_count}{Color.RESET}  {Color.RED}✗ 错误 {wrong_count}{Color.RESET}  {Color.DIM}正确率 {rate}%{Color.RESET}")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}\n")


def _show_explanation(subject: str, problem: dict):
    """AI 讲解知识点"""
    import subprocess as sp
    from .problems import SUBJECTS

    name = SUBJECTS[subject]["name"]
    question = problem["question"][:200]
    answer = problem["answer"]
    topic = problem["topic"]

    print(f"\n{Color.CYAN}🤖 AI 正在讲解…{Color.RESET}")
    prompt = (
        f"你是一位初中{name}老师。请用简单易懂的语言讲解以下知识点。\n"
        f"题目：{question}\n答案：{answer}\n主题：{topic}\n\n"
        "要求：\n"
        "1. 解释为什么这个答案是对的\n"
        "2. 用生活中的例子或比喻帮助理解\n"
        "3. 不要超过5句话\n"
        "4. 语气像朋友聊天一样轻松"
    )
    try:
        SGPT = "/home/zzk/.local/bin/sgpt"
        result = sp.run([SGPT, prompt], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
            text = latex_to_plain(text)
            print(f"\n{Color.BOLD}{Color.GREEN}💡 讲解：{Color.RESET}")
            for line in text.split(". "):
                line = line.strip()
                if line:
                    print(f"  {line}{'.' if not line.endswith('.') else ''}")
        else:
            print(f"\n  {Color.DIM}知识点：{topic} → {answer}{Color.RESET}")
            print(f"  {Color.DIM}可翻看课本相关章节加深理解。{Color.RESET}")
    except Exception:
        print(f"\n  {Color.DIM}知识点：{topic} → {answer}{Color.RESET}")
    print(f"{Color.DIM}{'─' * 40}{Color.RESET}")
