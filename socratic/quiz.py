"""苏格拉底式交互答题循环"""
from datetime import date, timedelta
from .utils import Color, answer_matches, get_socratic_hint, latex_to_plain
from .adaptive import update_ability, pick_problems, pick_adaptive_problem
from .progress import load_progress, save_progress, show_mastery_stats
from .generate import generate_problem, get_cached_generated
import random as rnd


def run_quiz(problems: list, subject: str, subjects: dict, all_problems: dict, loop_mode: bool = False, persona: dict | None = None):
    """苏格拉底式交互答题"""
    if persona is None:
        from .persona import get_persona
        persona = get_persona("default")
    progress = load_progress(subject)
    today = str(date.today())
    done_ids = set()
    round_num = 1

    while True:
        if not problems:
            hist_ids = set(progress.get("problem_history", {}).keys())
            all_ids = set(p["id"] for p in all_problems[subject])
            all_done = len(hist_ids) >= len(all_ids) and hist_ids.issuperset(all_ids)

            if all_done:
                pass
            elif loop_mode:
                remaining = len(all_problems[subject]) - len(done_ids)
                if remaining > 0:
                    a = pick_adaptive_problem(all_problems[subject], progress, done_ids)
                    problems = [a] if a else pick_problems(all_problems[subject], count=1, exclude_ids=done_ids)
                if not problems:
                    cached = get_cached_generated(subject)
                    remaining = [p for p in cached if p["id"] not in done_ids]
                    if remaining:
                        problems = [rnd.choice(remaining)]
                    else:
                        print(f"\n{Color.CYAN}🤖 题库用完了，AI 正在生成新题…{Color.RESET}")
                        weak = min(progress.get("mastery", {}).keys(), key=lambda t: progress["mastery"].get(t, 0.5)) if progress.get("mastery") else None
                        new_p = generate_problem(subject, all_problems, weak)
                        if new_p:
                            print(f"{Color.GREEN}✅ 新题已加入缓存！{Color.RESET}")
                            problems = [new_p]

            if not problems and not loop_mode:
                break
            if (not problems or all_done) and loop_mode:
                if round_num > 1 or all_done:
                    # All-done menu
                    subj = subjects[subject]
                    wrong_ids = [pid for pid, info in progress.get("problem_history", {}).items() if not info.get("solved")]
                    print(f"\n{Color.YELLOW}🎯 恭喜！{subj['name']}所有题目都做过了！{Color.RESET}")
                    print(f"  本轮完成 {round_num - 1} 题")
                    print(f"  还有 {Color.RED}{len(wrong_ids)} 道错题{Color.RESET}需要复习" if wrong_ids else f"  全部答对，{Color.GREEN}完美！🎉{Color.RESET}")
                    print(f"\n{Color.DIM}  选项：{Color.RESET}")
                    print(f"    r → 复习错题（{len(wrong_ids) if wrong_ids else '没有'}）")
                    print(f"    c → 清空进度重新开始")
                    print(f"    g → 🤖 AI 生成一道新题")
                    print(f"    s → 换一个科目")
                    print(f"    q → 退出")
                    try:
                        choice = input(f"\n{Color.BOLD}选择 (r/c/g/s/q)：{Color.RESET} ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        choice = "q"
                    if choice == "r" and wrong_ids:
                        wrong_problems = [p for p in all_problems[subject] if p["id"] in wrong_ids]
                        if wrong_problems:
                            print(f"{Color.YELLOW}📝 开始复习 {len(wrong_problems)} 道错题！{Color.RESET}")
                            problems = wrong_problems
                            continue
                    elif choice == "c":
                        progress = {"total_attempts": 0, "correct_first_try": 0, "correct_eventually": 0,
                                    "days_done": [], "streak": 0, "last_date": today,
                                    "problem_history": {}, "mastery": {}, "ability": 0.5}
                        save_progress(progress, subject)
                        done_ids.clear()
                        print(f"{Color.GREEN}✅ 进度已重置！从零开始吧 💪{Color.RESET}")
                        problems = pick_problems(all_problems[subject], count=1)
                        continue
                    elif choice == "g":
                        print(f"\n{Color.CYAN}🤖 AI 正在生成新题，请稍候…{Color.RESET}")
                        weak_topic = min(progress.get("mastery", {}).keys(), key=lambda t: progress["mastery"].get(t, 0.5)) if progress.get("mastery") else None
                        new_p = generate_problem(subject, all_problems, topic=weak_topic)
                        if new_p:
                            print(f"{Color.GREEN}✅ 新题生成成功！{Color.RESET}")
                            problems = [new_p]
                            continue
                        else:
                            print(f"{Color.RED}⚠ AI 出题失败。{Color.RESET}")
                            break
                    elif choice == "s":
                        from .cli import select_subject
                        new_subj = select_subject(subjects)
                        if new_subj and new_subj != subject:
                            return
                        break
                break

        if not problems:
            break

        problem = problems.pop(0)
        done_ids.add(problem["id"])
        subj = subjects[subject]

        print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
        if loop_mode:
            from .adaptive import get_topic_mastery
            mastery = get_topic_mastery(progress, problem["topic"])
            tm_pct = int(mastery * 100)
            tag = f"{Color.RED}💪 弱项{Color.RESET}" if tm_pct < 40 else f"{Color.YELLOW}📈 提升中{Color.RESET}" if tm_pct < 70 else f"{Color.GREEN}✅ 巩固{Color.RESET}"
            print(f"{Color.BOLD}{subj['emoji']} 第 {round_num} 题 — {problem['grade']} {problem['topic']}  {tag}{Color.RESET}")
        else:
            print(f"{Color.BOLD}{subj['emoji']} {subj['name']}每日一题 — {problem['grade']} {problem['topic']}{Color.RESET}")
        print(f"{Color.DIM}💡 答错我会用问题引导你，不直接给答案{Color.RESET}")
        print(f"{'─' * 50}")

        print(f"\n{Color.BOLD}{Color.YELLOW}题目：{Color.RESET}")
        q = latex_to_plain(problem["question"])
        if "\n" not in q and len(q) < 80:
            print(f"  {q}")
        else:
            for line in q.split("\n"):
                print(f"  {line}")

        concept = latex_to_plain(problem.get("concept_note", ""))
        if concept:
            print(f"\n{Color.DIM}📖 相关知识：{concept}{Color.RESET}")

        attempts = 0
        solved = False
        gave_up = False

        while not solved:
            print(f"\n{Color.BOLD}{Color.GREEN}你的答案是？{Color.RESET} ", end="")
            try:
                user_input = input()
            except (EOFError, KeyboardInterrupt):
                print()
                gave_up = True
                break

            ci = user_input.strip().lower()
            if not ci:
                print(f"\n  {Color.YELLOW}试试输入你的答案，不用怕错～{Color.RESET}")
                continue
            if ci in ("q", "quit", "退出", "qq"):
                if loop_mode:
                    print(f"\n{Color.BOLD}{Color.CYAN}结束。已做 {round_num - 1} 题，明天继续！💪{Color.RESET}")
                    return
                gave_up = True
                break
            if ci in ("h", "hint", "提示"):
                hint = get_socratic_hint(problem, "", attempts + 1)
                print(f"  {Color.CYAN}{hint or '这是最后一个提示了，再试一次？'}{Color.RESET}")
                attempts += 1
                continue
            if ci in ("s", "skip", "跳过"):
                gave_up = True
                break

            attempts += 1

            if answer_matches(user_input, problem):
                solved = True
                print(f"\n{Color.BOLD}{Color.GREEN}✅ 完全正确！{Color.RESET}")
                praise = persona['praise']['first'] if attempts == 1 else persona['praise']['later']
                print(f"  {Color.GREEN}{praise}{Color.RESET}")
                print(f"\n{Color.BOLD}{Color.BLUE}━━ 解题过程 ━━{Color.RESET}")
                for i, step in enumerate(problem["steps"], 1):
                    print(f"  {i}. {step}")
                print(f"{Color.BLUE}{'━' * 14}{Color.RESET}")
                if concept:
                    print(f"\n{Color.DIM}💡 记住：{concept}{Color.RESET}")
                # 追问模式：答对后 AI 追问"为什么"
                _run_follow_up(problem, subject, subj, persona)
            else:
                total_hints = len(problem.get("socratic_hints", []))
                print(f"\n{Color.RED}❌ 不对哦，再想想{Color.RESET}")
                hint = get_socratic_hint(problem, user_input, attempts)
                if hint:
                    print(f"  {persona['hint_prefix']}{hint}")
                else:
                    print(f"  {Color.YELLOW}{persona['nudge']}{Color.RESET}")
                if total_hints > 0:
                    used = min(attempts, total_hints)
                    print(f"  {Color.DIM}提示进度 {'🟡' * used}{'⚪' * (total_hints - used)}{Color.RESET}")
                print(f"  {Color.DIM}(输入 h 看提示 | s 跳过此题){Color.RESET}")

        if gave_up and not solved:
            print(f"\n{Color.MAGENTA}━━ 完整解法 ━━{Color.RESET}")
            for i, step in enumerate(problem["steps"], 1):
                print(f"  {i}. {step}")
            if concept:
                print(f"\n{Color.DIM}💡 记住：{concept}{Color.RESET}")
            print(f"\n  {Color.YELLOW}下次再试一次，你一定能自己解出来！💪{Color.RESET}")

        progress["total_attempts"] += 1
        if attempts == 1 and solved:
            progress["correct_first_try"] += 1
        if solved:
            progress["correct_eventually"] += 1
        update_ability(progress, problem, attempts, solved)

        pid = problem["id"]
        progress.setdefault("problem_history", {})
        if pid not in progress["problem_history"]:
            progress["problem_history"][pid] = {"attempts": 0, "solved": False}
        progress["problem_history"][pid]["attempts"] += attempts
        if solved:
            progress["problem_history"][pid]["solved"] = True

        if today not in progress["days_done"]:
            progress["days_done"].append(today)
            yesterday = date.today() - timedelta(days=1)
            if progress["last_date"] == str(yesterday):
                progress["streak"] += 1
            else:
                progress["streak"] = 1
            progress["last_date"] = today

        save_progress(progress, subject)
        round_num += 1

        if loop_mode and problems:
            print(f"\n{Color.DIM}─────────────────────────{Color.RESET}")
            print(f"{Color.BOLD}还要再来一题吗？{Color.RESET} {Color.DIM}(y/n, 回车继续){Color.RESET} ", end="")
            try:
                cont = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if cont in ("n", "no", "不", "不要"):
                break

    total = progress["total_attempts"]
    if total > 0:
        rate = progress["correct_first_try"] / total * 100
        print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
        print(f"{Color.BOLD}🎉 {subjects[subject]['name']}练习结束！{Color.RESET}")
        print(f"  共完成 {round_num - 1} 题 🔥")
        print(f"  累计首次正确率：{Color.GREEN}{rate:.0f}%{Color.RESET} ({progress['correct_first_try']}/{total})")
        print(f"  连续学习 {progress['streak']} 天 💪")
        if round_num > 5:
            show_mastery_stats(progress)
        print(f"{Color.CYAN}{'═' * 50}{Color.RESET}\n")


def _run_follow_up(problem: dict, subject: str, subj: dict, persona: dict | None = None):
    """答对后 AI 追问，加深理解"""
    import subprocess as sp
    from .utils import latex_to_plain as ltp
    if persona is None:
        from .persona import get_persona
        persona = get_persona("default")

    print(f"\n{Color.DIM}{'─' * 40}{Color.RESET}")
    print(f"{Color.BOLD}🧐 追问：{Color.RESET}{Color.DIM}答对了，但你真的理解了吗？(回车跳过){Color.RESET}")

    question = problem["question"][:200]
    answer = problem["answer"]
    topic = problem["topic"]

    prompt = (
        f"你是一位初中{subj['name']}老师。学生刚做对了一道关于{topic}的题。\n"
        f"题目：{question}\n正确答案：{answer}\n\n"
        f"{persona['system_extra']}\n\n"
        "请给学生出一个简短但深入的追问，要求：\n"
        "1. 问\"为什么这个方法是对的？\"或\"换个条件会怎样？\"\n"
        "2. 一句话，不要超过30个字\n"
        "3. 不要直接重复题目，要触类旁通\n"
        "4. 不要评价学生，只出题"
    )

    result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=20)
    if result.returncode != 0:
        return
    follow_q = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
    follow_q = ltp(follow_q)

    print(f"\n  {Color.CYAN}🤖 {follow_q}{Color.RESET}")
    print(f"\n{Color.BOLD}{Color.GREEN}你的思考：{Color.RESET} ", end="")
    try:
        student_answer = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if not student_answer:
        return
    if student_answer.lower() in ("q", "quit", "退出", "qq", "s", "skip", "跳过"):
        return

    # AI 评估学生的回答
    eval_prompt = (
        f"你是一位初中{subj['name']}老师。你的追问：{follow_q}\n"
        f"学生回答：{student_answer}\n\n"
        "请用一句话反馈：如果学生理解正确就表扬，如果有偏差就简单指出。最多两句话。"
    )
    result = sp.run(["sgpt", eval_prompt], capture_output=True, text=True, timeout=20)
    if result.returncode == 0:
        feedback = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        feedback = ltp(feedback)
        print(f"\n  {Color.GREEN}📝 {feedback}{Color.RESET}")

    print(f"{Color.DIM}{'─' * 40}{Color.RESET}")
