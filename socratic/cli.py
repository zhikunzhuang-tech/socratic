"""socratic CLI 入口"""
import argparse
import sys
from datetime import date
from . import __version__
from .utils import Color
from .problems import SUBJECTS, SUBJECT_KEYS, SUBJECT_NAMES, ALL_PROBLEMS
from .progress import load_progress, show_stats
from .adaptive import pick_problems
from .quiz import run_quiz
from .solve import run_solve_mode
from .persona import get_persona, PERSONA_KEYS
from .cache import get_problems, get_all_problems


def select_subject(subjects: dict, show_review: bool = True) -> str:
    """交互式选择科目，返回科目key或 __review__ / __exit__。
    show_review=False 时隐藏「错题重做」选项并显示每科待复习错题数。"""
    keys = list(subjects.keys())
    # 错题模式下，提前加载每个科目的错题数（只统计题库中存在的题目）
    wrong_counts = {}
    if not show_review:
        for key in keys:
            p = load_progress(key)
            records = p.get("wrong_records", {})
            valid_ids = {prob["id"] for prob in ALL_PROBLEMS[key]}
            wrong_counts[key] = sum(
                1 for pid, recs in records.items()
                if pid in valid_ids
                for r in recs if not r["solved"]
            )

    print(f"\n{Color.BOLD}{Color.CYAN}🧠 苏格拉底互动学习{Color.RESET}")
    print(f"{Color.DIM}请选择要练习的科目：{Color.RESET}\n")
    for i, key in enumerate(keys, 1):
        s = subjects[key]
        count = len(ALL_PROBLEMS[key])
        wc = wrong_counts.get(key, -1)
        if wc >= 0:
            if wc > 0:
                wrong_hint = f"  {Color.RED}📕 {wc} 道待复习{Color.RESET}"
            else:
                wrong_hint = f"  {Color.DIM}暂无错题{Color.RESET}"
        else:
            wrong_hint = ""
        if key in ("math", "english", "physics", "chinese"):
            print(f"  {Color.BOLD}{i}.{Color.RESET} {s['icon']} {s['name']}  {Color.DIM}({s['grades']}，AI实时出题){Color.RESET}{wrong_hint}")
        else:
            print(f"  {Color.BOLD}{i}.{Color.RESET} {s['icon']} {s['name']}  {Color.DIM}({s['grades']}，{count} 题){Color.RESET}{wrong_hint}")
    if show_review:
        print(f"  {Color.BOLD}10.{Color.RESET} 📕 错题重做")
        print(f"  {Color.BOLD}11.{Color.RESET} 🚪 退出程序")
        exit_num = 11
        review_num = 10
    else:
        print(f"  {Color.BOLD}10.{Color.RESET} 🚪 返回")
        exit_num = 10
        review_num = None
    print(f"\n{Color.DIM}输入数字/科目名，回车默认数学{Color.RESET}")
    print(f"{Color.CYAN}{'─' * 40}{Color.RESET}")
    try:
        choice = input(f"{Color.BOLD}选择：{Color.RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "__exit__"
    if not choice:
        return "math"
    if choice.isdigit():
        idx = int(choice)
        if show_review and idx == review_num:
            return "__review__"
        if idx == exit_num:
            return "__exit__"
        idx = idx - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    if choice.lower() in ("q", "quit", "exit", "退出"):
        return "__exit__"
    if show_review and choice.lower() in ("r", "review", "错题", "错题重做"):
        return "__review__"
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
    parser.add_argument("--num", type=int, default=1, help="每轮题数（或使用 --generate 时批量生成 N 题）")
    parser.add_argument("--no-banner", action="store_true", dest="no_banner")
    parser.add_argument("--no-loop", action="store_true", dest="no_loop", help="单轮模式")
    parser.add_argument("--generate", "-g", action="store_true", help="AI 自动生成新题（配合 --num 5 批量生成）")
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
    parser.add_argument("--path", help="📋 学习路径模式，如 --path math --kb math_bsd 基于教材规划学习路径")
    parser.add_argument("--kb", help="使用知识库出题（kb名称）")
    parser.add_argument("--kb-create", dest="kb_create", help="创建知识库")
    parser.add_argument("--kb-add", dest="kb_add", nargs=2, metavar=("NAME", "FILE"), help="添加文档到知识库")
    parser.add_argument("--kb-list", dest="kb_list", action="store_true", help="列出知识库")
    parser.add_argument("--kb-show", dest="kb_show", help="查看知识库详情")
    parser.add_argument("--kb-delete", dest="kb_delete", help="删除知识库")

    args = parser.parse_args()

    if args.version:
        print(f"socratic v{__version__}")
        return

    # KB 管理命令
    if any([args.kb_create, args.kb_add, args.kb_list, args.kb_show, args.kb_delete]):
        from . import kb
        if args.kb_create:
            kb.kb_create(args.kb_create)
        elif args.kb_add:
            kb.kb_add(args.kb_add[0], args.kb_add[1])
        elif args.kb_list:
            kb.kb_list()
        elif args.kb_show:
            kb.kb_show(args.kb_show)
        elif args.kb_delete:
            kb.kb_delete(args.kb_delete)
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

    if subject == "__exit__":
        print(f"{Color.DIM}👋 再见！{Color.RESET}")
        sys.exit(0)
    if subject == "__review__":
        from .review import run_review_mode
        from .flash import run_flash_mode
        persona_name = args.persona or "gentle"
        if persona_name not in PERSONA_KEYS:
            persona_name = "gentle"
        persona = get_persona(persona_name)
        while True:
            print(f"\n{Color.BOLD}{Color.CYAN}📕 错题重做 — 选择科目{Color.RESET}")
            subject = select_subject(SUBJECTS, show_review=False)
            if subject == "__exit__":
                main()
                return
            flash = subject in ("biology", "geography", "claude", "hermes", "cmd")
            has_problems = run_review_mode(subject, SUBJECTS, ALL_PROBLEMS, persona, flash=flash)
            if has_problems:
                break
        main()
        return

    subj = SUBJECTS[subject]

    # 知识库
    if args.kb:
        from .kb import kb_get_content
        from .cache import set_kb_context
        kb_text = kb_get_content(args.kb)
        if kb_text:
            set_kb_context(kb_text)
            print(f"{Color.GREEN}📚 知识库「{args.kb}」已加载{Color.RESET}")
        else:
            print(f"{Color.RED}⚠ 知识库「{args.kb}」为空或不存在{Color.RESET}")

    # --path 学习路径模式
    if args.path:
        from .path import run_path
        kb_name = args.kb
        run_path(subject=args.path, kb_name=kb_name, subjects=SUBJECTS, all_problems=ALL_PROBLEMS)
        return

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
        from .review import run_review_mode
        flash = subject in ("biology", "geography")
        run_review_mode(subject, SUBJECTS, ALL_PROBLEMS, persona, flash=flash)
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
        main()
        return

    # 生物/地理/claude/hermes/常用命令 默认走闪卡模式（知识问答型，适合快速复习）
    if subject in ("biology", "geography", "claude", "hermes", "cmd") and not args.no_loop and not args.generate and not args.review and not args.book and not args.solve and not args.stats and not args.list:
        from .flash import run_flash_mode
        print(f"{Color.DIM}  该科目默认闪卡模式，加 --no-loop 进入标准模式{Color.RESET}")
        run_flash_mode(subject, SUBJECTS, ALL_PROBLEMS, persona)
        main()
        return

    # 按主题学习模式（闪卡类科目跳过，其余科目先选模块）
    if subject not in ("biology", "geography", "claude", "hermes", "cmd") and not args.topic and not args.generate and not args.review and not args.book and not args.solve and not args.stats and not args.list:
        topics = sorted(set(p["topic"] for p in ALL_PROBLEMS[subject]))
        if not topics:
            print(f"{Color.RED}⚠ 题库为空{Color.RESET}")
            sys.exit(1)
        print(f"\n{Color.BOLD}{Color.CYAN}📚 {subj['icon']} {subj['name']} — 选择学习模块{Color.RESET}")
        print(f"{Color.DIM}{'─' * 40}{Color.RESET}")
        for i, t in enumerate(topics, 1):
            count = sum(1 for p in ALL_PROBLEMS[subject] if p["topic"] == t)
            if subject in ("math", "english", "physics", "chinese"):
                print(f"  {Color.BOLD}{i}.{Color.RESET} {t}  {Color.DIM}(AI实时出题){Color.RESET}")
            else:
                print(f"  {Color.BOLD}{i}.{Color.RESET} {t}  {Color.DIM}({count} 题){Color.RESET}")
        print(f"\n{Color.DIM}输入数字/模块名，b/返回上层，回车默认第 1 个{Color.RESET}")
        try:
            choice = input(f"{Color.BOLD}选择：{Color.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = ""
        if not choice:
            args.topic = topics[0]
        elif choice.lower() in ("b", "back", "返回"):
            main()
            return
        elif choice.isdigit():
            idx = int(choice) - 1
            args.topic = topics[idx] if 0 <= idx < len(topics) else topics[0]
        else:
            matched = [t for t in topics if choice.lower() in t.lower()]
            args.topic = matched[0] if matched else topics[0]
        print(f"{Color.GREEN}✅ 模块：{args.topic}{Color.RESET}\n")

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
        if args.num > 1:
            # 批量生成模式
            print(f"\n{Color.CYAN}🤖 批量生成 {args.num} 道题目…{Color.RESET}")
            from .cache import save_cache, _generate as gen_fn
            all_p = get_all_problems(subject)
            topic = args.topic
            new_count = 0
            existing_qs = {p["question"] for p in all_p}
            for i in range(args.num):
                print(f"  [{i + 1}/{args.num}] ", end="", flush=True)
                new_p = gen_fn(subject, topic=topic)
                if new_p and new_p["question"] not in existing_qs:
                    all_p.append(new_p)
                    existing_qs.add(new_p["question"])
                    new_count += 1
                    print(f"{Color.GREEN}✓{Color.RESET}")
                elif new_p:
                    print(f"{Color.YELLOW}（重复，跳过）{Color.RESET}")
                else:
                    print(f"{Color.RED}✗{Color.RESET}")
            save_cache(subject, all_p)
            print(f"\n{Color.GREEN}✅ 成功生成 {new_count}/{args.num} 道新题{Color.RESET}")
            return

        # 单题生成模式
        print(f"\n{Color.CYAN}🤖 AI 生成模式 — 自动出全新题目{Color.RESET}")
        selected = get_problems(subject, count=args.num, topic=args.topic)
        # 检查是否真的拿到了新题（非种子题）
        if selected and selected[0]["id"].startswith("seed-"):
            print(f"{Color.YELLOW}⚠ 从缓存取到的是种子题，强制 AI 生成{Color.RESET}")
            from .cache import save_cache
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
        # 自适应模式：从缓存取题（不够时 AI 批量生成）
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
        print(f"  捷径：{Color.DIM}h/提示  |  a/答案  |  s/跳过  |  qq/退出{Color.RESET}")
        print(f"{Color.DIM}{'─' * 50}{Color.RESET}")

    run_quiz(selected, subject, SUBJECTS, ALL_PROBLEMS, loop_mode=loop_mode, persona=persona, topic=args.topic)
    main()


if __name__ == "__main__":
    main()
