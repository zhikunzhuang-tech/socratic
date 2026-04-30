"""socratic CLI 入口"""
import argparse
import sys
from datetime import date
from . import __version__
from .utils import Color
from .problems import SUBJECTS, SUBJECT_KEYS, SUBJECT_NAMES, ALL_PROBLEMS
from .progress import load_progress, show_stats, show_mastery_stats
from .adaptive import pick_problems
from .quiz import run_quiz
from .generate import generate_problem
from .solve import run_solve_mode


def select_subject(subjects: dict) -> str:
    """交互式选择科目"""
    keys = list(subjects.keys())
    print(f"\n{Color.BOLD}{Color.CYAN}🧠 苏格拉底互动学习{Color.RESET}")
    print(f"{Color.DIM}请选择要练习的科目：{Color.RESET}\n")
    for i, key in enumerate(keys, 1):
        s = subjects[key]
        count = len(ALL_PROBLEMS[key])
        print(f"  {Color.BOLD}{i}.{Color.RESET} {s['icon']} {s['name']}  {Color.DIM}({s['grades']}，{count} 题){Color.RESET}")
    print(f"\n{Color.DIM}输入数字或科目名，回车默认数学{Color.RESET}")
    print(f"{Color.CYAN}{'─' * 40}{Color.RESET}")
    try:
        choice = input(f"{Color.BOLD}选择：{Color.RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "math"
    if not choice:
        return "math"
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    choice_lower = choice.lower()
    for key in keys:
        if choice_lower == key or choice_lower == subjects[key]["name"]:
            return key
    return "math"


def show_problem_list(subject: str):
    problems = ALL_PROBLEMS.get(subject, [])
    subj = SUBJECTS[subject]
    print(f"\n{Color.BOLD}{Color.CYAN}📚 {subj['icon']} {subj['name']}题库{Color.RESET}")
    print(f"{'━' * 60}")
    current_grade = None
    for p in problems:
        if p["grade"] != current_grade:
            current_grade = p["grade"]
            print(f"\n{Color.BOLD}{Color.YELLOW}═══ {current_grade} ═══{Color.RESET}")
        diff_stars = "⭐" * p["difficulty"]
        qtext = p["question"].replace("\n", " ")[:55]
        print(f"  [{p['id']}] {p['topic']} {Color.DIM}{diff_stars}{Color.RESET}")
        print(f"    {Color.DIM}{qtext}{'…' if len(p['question'])>55 else ''}{Color.RESET}")
    print(f"\n{Color.DIM}共 {len(problems)} 道题{Color.RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="苏格拉底互动学习 — 用提问引导思考，覆盖多科目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  socratic                     # 交互选择科目
  socratic -s english          # 直接进入英语
  socratic --solve             # 自由输入题目，AI 苏格拉底引导
  socratic -g                  # AI 自动生成新题
  socratic -s math --stats     # 查看数学统计""",
    )
    parser.add_argument("--subject", "-s", default=None, help=f"科目：{', '.join(SUBJECT_KEYS)}")
    parser.add_argument("--stats", action="store_true", help="查看学习统计")
    parser.add_argument("--list", action="store_true", help="浏览题库")
    parser.add_argument("--grade", help="年级")
    parser.add_argument("--topic", help="主题")
    parser.add_argument("--num", type=int, default=1, help="每轮题数")
    parser.add_argument("--no-banner", action="store_true", dest="no_banner")
    parser.add_argument("--no-loop", action="store_true", dest="no_loop", help="单轮模式")
    parser.add_argument("--generate", "-g", action="store_true", help="AI 自动生成新题")
    parser.add_argument("--solve", action="store_true", help="自由输入题目，AI 苏格拉底引导解题")
    parser.add_argument("--version", "-v", action="store_true", help="显示版本")

    args = parser.parse_args()

    if args.version:
        print(f"socratic v{__version__}")
        return

    # 科目选择
    subject = args.subject
    if subject:
        subject = subject.lower()
        if subject in SUBJECT_NAMES:
            subject = SUBJECT_NAMES[subject]
        if subject not in SUBJECTS:
            print(f"{Color.RED}⚠ 不支持的科目：{subject}。可选：{', '.join(SUBJECT_KEYS)}{Color.RESET}")
            sys.exit(1)
    else:
        if args.stats or args.list:
            subject = "math"
        elif args.solve:
            subject = select_subject(SUBJECTS)
        else:
            subject = select_subject(SUBJECTS)

    subj = SUBJECTS[subject]
    problems_list = ALL_PROBLEMS[subject]

    # --solve 模式
    if args.solve:
        run_solve_mode(subject, SUBJECTS)
        return

    if args.stats:
        progress = load_progress(subject)
        show_stats(progress, subject, SUBJECTS)
        return

    if args.list:
        show_problem_list(subject)
        return

    if args.grade:
        grade_map = {"7": "初一", "8": "初二", "9": "初三",
                     "初一": "初一", "初二": "初二", "初三": "初三"}
        if args.grade in grade_map:
            args.grade = grade_map[args.grade]
        else:
            print(f"{Color.RED}⚠ 年级格式：初一、初二、初三 或 7、8、9{Color.RESET}")
            sys.exit(1)

    loop_mode = not args.no_loop

    # --generate 模式
    if args.generate:
        print(f"\n{Color.CYAN}🤖 AI 生成模式 — 自动出全新题目{Color.RESET}")
        new_p = generate_problem(subject, ALL_PROBLEMS, topic=args.topic)
        if new_p:
            selected = [new_p]
        else:
            print(f"{Color.YELLOW}⚠ AI 出题失败，从题库随机选题{Color.RESET}")
            selected = pick_problems(problems_list, count=args.num, grade=args.grade, topic=args.topic)
    elif not loop_mode:
        today_seed = int(date.today().strftime("%Y%m%d"))
        selected = pick_problems(problems_list, count=args.num, seed=today_seed,
                                 grade=args.grade, topic=args.topic)
    else:
        selected = pick_problems(problems_list, count=args.num,
                                 grade=args.grade, topic=args.topic)

    if not selected:
        g = f"（年级={args.grade}）" if args.grade else ""
        t = f"（主题={args.topic}）" if args.topic else ""
        print(f"{Color.RED}⚠ 没有匹配的题目 {g}{t}{Color.RESET}")
        sys.exit(1)

    if not args.no_banner:
        print(f"{Color.BOLD}{Color.CYAN}🧠 苏格拉底互动学习 — {subj['icon']} {subj['name']}{Color.RESET}")
        print(f"{Color.DIM}{'─' * 50}{Color.RESET}")
        print(f"  日期：{Color.BOLD}{date.today().strftime('%Y年%m月%d日')}{Color.RESET}")
        if loop_mode and not args.generate:
            print(f"  模式：{Color.BOLD}🎯 自适应{Color.RESET} — 根据强弱项动态选题")
        print(f"  规则：答错了我会用问题引导你，"
              f"\n        不直接给答案——自己找到的答案才记得牢！")
        print(f"  捷径：{Color.DIM}h/提示  |  s/跳过  |  qq/退出{Color.RESET}")
        print(f"{Color.DIM}{'─' * 50}{Color.RESET}")

    run_quiz(selected, subject, SUBJECTS, ALL_PROBLEMS, loop_mode=loop_mode)


if __name__ == "__main__":
    main()
