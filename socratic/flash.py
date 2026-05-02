"""闪卡模式 — 快速刷题，按回车看答案"""
from .utils import Color, latex_to_plain
from .progress import load_progress, save_progress, record_wrong_answer
from .adaptive import update_ability
from .cache import get_all_problems, get_problems
from datetime import date, timedelta
from collections import OrderedDict


def run_flash_mode(subject: str, subjects: dict, all_problems: dict, persona: dict):
    """闪卡刷题：显示题目→回车看答案→自评对错"""
    subj = subjects[subject]
    progress = load_progress(subject)

    # 生物/地理/常用命令：章节选择
    if subject in ("biology", "geography", "cmd"):
        all_probs = get_all_problems(subject)
        chapters = _get_chapters(all_probs)
        chapter = _select_chapter(chapters, progress, subj)
        if chapter is None:
            return
        if chapter == "__all__":
            problems = all_probs
        else:
            problems = [p for p in all_probs if p["topic"] == chapter]
    else:
        problems = get_problems(subject, count=50)
        import random as rnd
        rnd.shuffle(problems)

    if not problems:
        print(f"{Color.YELLOW}⚠ 没有题目。{Color.RESET}")
        return

    today = str(date.today())
    done_ids = set()
    round_num = 1
    correct_count = 0
    wrong_count = 0

    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    print(f"{Color.BOLD}⚡ 闪卡刷题 — {subj['icon']} {subj['name']}{Color.RESET}")
    print(f"{Color.DIM}  看题 → 心里默答 → 回车看答案 → 自评对错{Color.RESET}")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}")

    for problem in problems:
        if problem["id"] in done_ids:
            continue
        done_ids.add(problem["id"])

        print(f"\n{Color.BOLD}{Color.CYAN}{'─' * 50}{Color.RESET}")
        print(f"{Color.BOLD}📌 第 {round_num}/{len(problems)} 题 — {problem['topic']}{Color.RESET}")
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

        # 记录章节进度
        _update_chapter_progress(progress, problem["topic"], correct=(eval_input in ("y", "yes", "对", "对了")))
        save_progress(progress, subject)

    total = correct_count + wrong_count
    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    if total > 0:
        rate = int(correct_count / total * 100)
        print(f"{Color.BOLD}⚡ 刷题完成！{Color.RESET}")
        print(f"  刷了 {round_num - 1} 题")
        print(f"  {Color.GREEN}✓ 正确 {correct_count}{Color.RESET}  {Color.RED}✗ 错误 {wrong_count}{Color.RESET}  {Color.DIM}正确率 {rate}%{Color.RESET}")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}\n")


def _get_chapters(problems: list) -> OrderedDict:
    """获取按顺序的章节列表及题数"""
    chapters = OrderedDict()
    for p in problems:
        ch = p.get("topic", "其他")
        if ch not in chapters:
            chapters[ch] = 0
        chapters[ch] += 1
    return chapters


def _select_chapter(chapters: OrderedDict, progress: dict, subj: dict) -> str | None:
    """交互选择章节，显示进度条"""
    chap_prog = progress.get("chapter_progress", {})

    print(f"\n{Color.BOLD}{Color.CYAN}📖 选择章节 — {subj['icon']} {subj['name']}{Color.RESET}")
    print(f"{Color.DIM}  输入序号，或直接回车刷全部{Color.RESET}")
    print(f"{Color.DIM}{'─' * 50}{Color.RESET}")

    ch_list = list(chapters.items())
    # 分页显示
    page_size = 15
    total_pages = (len(ch_list) + page_size - 1) // page_size
    current_page = 0

    while True:
        start = current_page * page_size
        end = min(start + page_size, len(ch_list))
        page_items = ch_list[start:end]

        print(f"\n  {Color.BOLD}第 {current_page+1}/{total_pages} 页{Color.RESET}")
        for i, (ch, count) in enumerate(page_items, start + 1):
            ch_data = chap_prog.get(ch, {})
            done = ch_data.get("done", 0)
            pct = int(done / count * 100) if count > 0 else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            c = Color.GREEN if pct >= 80 else Color.YELLOW if pct > 0 else Color.DIM
            print(f"  {c}{i:>2}.{Color.RESET} {ch:<20} {c}{bar} {pct}%{Color.RESET}")

        print(f"\n  {Color.DIM}0 = 全部  |  n = 下一页  |  p = 上一页  |  回车 = 全部{Color.RESET}")
        try:
            choice = input(f"{Color.BOLD}选择：{Color.RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None

        if not choice:
            return "__all__"
        if choice == "0":
            return "__all__"
        if choice == "n" and current_page < total_pages - 1:
            current_page += 1
            continue
        if choice == "p" and current_page > 0:
            current_page -= 1
            continue
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(ch_list):
                return ch_list[idx][0]


def _update_chapter_progress(progress: dict, chapter: str, correct: bool):
    """更新章节进度"""
    chap_prog = progress.setdefault("chapter_progress", {})
    if chapter not in chap_prog:
        chap_prog[chapter] = {"done": 0, "correct": 0}
    chap_prog[chapter]["done"] += 1
    if correct:
        chap_prog[chapter]["correct"] += 1


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
        "要求：\n1. 解释为什么这个答案是对的\n2. 用生活中的例子或比喻帮助理解\n3. 不要超过5句话\n4. 语气像朋友聊天一样轻松"
    )
    try:
        SGPT = "sgpt"
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
