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
from .solve import run_solve_mode
from .persona import get_persona, show_persona_menu, PERSONA_KEYS
from .cache import get_problems, get_all_problems


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
    parser.add_argument("--persona", "-p", default=None,
                        help=f"助教风格：{', '.join(PERSONA_KEYS)}")
    parser.add_argument("--book", type=str, nargs="?", const=True, default=None,
                        help="📖 AI 生成互动学习章节，如 --book 一元一次方程")
    parser.add_argument("--review", action="store_true",
                        help="📕 错题复习模式")
    parser.add_argument("--init-kb", action="store_true", dest="init_kb",
                        help="初始化知识库（为所有主题生成知识卡片）")
    parser.add_argument("--report", action="store_true",
                        help="📊 学习报告（周报/趋势/统计）")
    parser.add_argument("--flash", action="store_true",
                        help="⚡ 闪卡刷题（看题→回车看答案→自评对错，适合考前冲刺）")
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

    # 助教人格
    persona_name = args.persona
    if persona_name is None:
        persona_name = "gentle"  # 默认耐心风格
    elif persona_name not in PERSONA_KEYS:
        print(f"{Color.RED}⚠ 不支持的风格：{persona_name}。可选：{', '.join(PERSONA_KEYS)}{Color.RESET}")
        sys.exit(1)
    persona = get_persona(persona_name)

    # --book 模式
    if args.book is not None:
        from .book import run_book_mode
        topic = args.book if isinstance(args.book, str) else None
        run_book_mode(subject, SUBJECTS, ALL_PROBLEMS, persona, topic=topic)
        return

    # --review 错题复习
    if args.review:
        if subject in ("biology", "geography", "claude", "hermes"):
            from .flash import run_flash_mode
            run_flash_mode(subject, SUBJECTS, ALL_PROBLEMS, persona)
        else:
            from .review import run_review_mode
            run_review_mode(subject, SUBJECTS, ALL_PROBLEMS, persona)
        return

    # --init-kb 初始化知识库
    if args.init_kb:
        from .knowledge import auto_generate
        topics = set()
        for p in ALL_PROBLEMS.get(subject, []):
            topics.add(p["topic"])
        print(f"{Color.CYAN}📚 正在生成 {len(topics)} 个知识卡片…{Color.RESET}")
        for i, t in enumerate(sorted(topics), 1):
            print(f"  [{i}/{len(topics)}] {t}... ", end="", flush=True)
            result = auto_generate(subject, t)
            print(f"{Color.GREEN}✓{Color.RESET}" if result else f"{Color.RED}✗{Color.RESET}")
        print(f"{Color.GREEN}✅ 知识库初始化完成！{Color.RESET}")
        return

    # --solve 模式
    if args.solve:
        run_solve_mode(subject, SUBJECTS)
        return

    if args.stats:
        progress = load_progress(subject)
        show_stats(progress, subject, SUBJECTS)
        return

    if args.report:
        from .report import run_report
        run_report(subject, SUBJECTS, ALL_PROBLEMS)
        return

    if args.flash:
        from .flash import run_flash_mode
        run_flash_mode(subject, SUBJECTS, ALL_PROBLEMS, persona)
        return

    # 生物/地理/Claude/Hermes 默认走闪卡模式
    if subject in ("biology", "geography", "claude", "hermes") and not args.no_loop and not args.generate and not args.review and not args.book and not args.solve and not args.stats and not args.list:
        from .flash import run_flash_mode
        print(f"{Color.DIM}  生物/地理/Claude/Hermes 默认闪卡模式，加 --no-loop 进入标准模式{Color.RESET}")
        run_flash_mode(subject, SUBJECTS, ALL_PROBLEMS, persona)
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

    # --generate 模式：强制 AI 生成新题
    if args.generate:
        print(f"\n{Color.CYAN}🤖 AI 生成模式 — 自动出全新题目{Color.RESET}")
        # 直接通过 cache 系统生成（先清缓存计数，强制走 AI）
        selected = get_problems(subject, count=args.num, topic=args.topic)
        # 检查是否真的拿到了新题（非种子题）
        if selected and selected[0]["id"].startswith("seed-"):
            print(f"{Color.YELLOW}⚠ 从缓存取到的是种子题，强制 AI 生成{Color.RESET}")
            from .cache import save_cache, get_all_problems
            import socratic.cache as _c
            new_p = _c._generate(subject, topic=args.topic)
            if new_p:
                all_p = get_all_problems(subject)
                all_p.append(new_p)
                save_cache(subject, all_p)
                selected = [new_p]
                print(f"{Color.GREEN}✅ AI 新题已加入题库！{Color.RESET}")
            elif not selected:
                selected = pick_problems(get_all_problems(subject), count=args.num, grade=args.grade, topic=args.topic)
    elif not loop_mode:
        today_seed = int(date.today().strftime("%Y%m%d"))
        selected = pick_problems(get_all_problems(subject), count=args.num, seed=today_seed,
                                 grade=args.grade, topic=args.topic)
    else:
        # 自适应模式：从缓存取题
        selected = get_problems(subject, count=args.num, topic=args.topic)

    if not selected:
        g = f"（年级={args.grade}）" if args.grade else ""
        print(f"{Color.RED}⚠ 没有匹配的题目 {g}{Color.RESET}")
        sys.exit(1)

    if not args.no_banner:
        print(f"{Color.BOLD}{Color.CYAN}🧠 苏格拉底互动学习 — {subj['icon']} {subj['name']}{Color.RESET}")
        print(f"{Color.DIM}{'─' * 50}{Color.RESET}")
        print(f"  日期：{Color.BOLD}{date.today().strftime('%Y年%m月%d日')}{Color.RESET}")
        if loop_mode and not args.generate:
            print(f"  模式：{Color.BOLD}🎯 自适应{Color.RESET} — 根据强弱项动态选题")
        print(f"  规则：答错了我会用问题引导你，"
              f"\n        不直接给答案——自己找到的答案才记得牢！")
        print(f"  风格：{Color.BOLD}{persona['icon']} {persona['name']}{Color.RESET}")
        # 显示错题数
        p = load_progress(subject)
        wr = p.get("wrong_records", {})
        if wr:
            unsolved = sum(1 for recs in wr.values() for r in recs if not r["solved"])
            if unsolved > 0:
                print(f"  错题：{Color.RED}{unsolved} 道待复习{Color.RESET}  {Color.DIM}(socratic --review){Color.RESET}")
        print(f"  捷径：{Color.DIM}h/提示  |  s/跳过  |  qq/退出{Color.RESET}")
        print(f"{Color.DIM}{'─' * 50}{Color.RESET}")

    run_quiz(selected, subject, SUBJECTS, ALL_PROBLEMS, loop_mode=loop_mode, persona=persona)


if __name__ == "__main__":
    main()
