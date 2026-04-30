"""--book 模式：AI 生成互动学习章节"""
import subprocess as sp
from .utils import Color, latex_to_plain
from .quiz import run_quiz


def run_book_mode(subject: str, subjects: dict, all_problems: dict, persona: dict, topic: str | None = None):
    """AI 生成互动学习章节，含概念讲解 + 嵌入式 quiz"""
    subj = subjects[subject]
    name = subj["name"]

    if not topic:
        print(f"\n{Color.BOLD}{Color.GREEN}📖 要学习什么主题？{Color.RESET} ", end="")
        try:
            topic = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

    print(f"\n{Color.BOLD}{Color.CYAN}📖 AI 正在生成「{topic}」互动学习章节…{Color.RESET}")
    print(f"{Color.DIM}这需要几秒钟，请稍候{Color.RESET}")

    # Step 1: Generate chapter content + quiz questions
    prompt = (
        f"你是一位初中{name}老师。请为「{topic}」生成一套互动学习材料。\n\n"
        "输出严格的 JSON（一行，不要换行），格式：\n"
        '{\n'
        '  "title": "章节标题",\n'
        '  "summary": "50字以内的概述",\n'
        '  "sections": [\n'
        '    {"heading": "小节1标题", "content": "概念讲解，包含公式和例子，50-100字"},\n'
        '    {"heading": "小节2标题", "content": "进一步讲解，50-100字"}\n'
        '  ],\n'
        '  "key_points": ["要点1", "要点2", "要点3"],\n'
        '  "quiz": [\n'
        '    {\n'
        '      "question": "题目1",\n'
        '      "answer": "正确答案",\n'
        '      "alternatives": ["备选格式1"],\n'
        '      "steps": ["步骤1", "步骤2"],\n'
        '      "socratic_hints": ["提示1", "提示2", "提示3"],\n'
        '      "common_errors": {"错1": "反馈1", "错2": "反馈2"},\n'
        '      "concept_note": "一句话核心概念"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "要求：\n"
        f"- 2-3 个小节，讲清{topic}的核心概念\n"
        "- quiz 包含 2-3 道练习题，难度递进\n"
        "- 每道题必须有 socratic_hints（3条）和 common_errors（至少2条）\n"
        "- 只输出 JSON，不要其他文字"
    )

    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=45)
        if result.returncode != 0:
            print(f"{Color.RED}⚠ AI 生成失败。{Color.RESET}")
            return
        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        import json as j
        chapter = j.loads(text)
    except Exception as e:
        print(f"{Color.RED}⚠ 解析失败：{e}{Color.RESET}")
        return

    # Display the chapter
    title = latex_to_plain(chapter.get("title", topic))
    summary = latex_to_plain(chapter.get("summary", ""))
    key_points = [latex_to_plain(kp) for kp in chapter.get("key_points", [])]
    sections = chapter.get("sections", [])
    quiz_problems = chapter.get("quiz", [])

    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 50}{Color.RESET}")
    print(f"{Color.BOLD}📖 {title}{Color.RESET}")
    if summary:
        print(f"  {Color.DIM}{summary}{Color.RESET}")
    print(f"{'─' * 50}")

    for sec in sections:
        heading = latex_to_plain(sec.get("heading", ""))
        content = latex_to_plain(sec.get("content", ""))
        print(f"\n{Color.BOLD}{Color.YELLOW}▎{heading}{Color.RESET}")
        for line in content.split(". "):
            line = line.strip()
            if line:
                print(f"  {line}{'.' if not line.endswith('.') else ''}")

    if key_points:
        print(f"\n{Color.BOLD}📌 要点总结{Color.RESET}")
        for kp in key_points:
            print(f"  • {kp}")

    if quiz_problems:
        print(f"\n{Color.BOLD}{Color.GREEN}🧪 练习题 ({len(quiz_problems)} 道){Color.RESET}")
        print(f"{Color.DIM}输入答案进行练习，答完全部题目后章节结束{Color.RESET}")
        print(f"{Color.CYAN}{'─' * 50}{Color.RESET}")

        # Clean up LaTeX in quiz problems
        valid_quiz = []
        for q in quiz_problems:
            if "question" not in q or "answer" not in q:
                continue
            for field in ["question", "answer", "concept_note"]:
                if field in q:
                    q[field] = latex_to_plain(q[field])
            if "alternatives" in q:
                q["alternatives"] = [latex_to_plain(a) for a in q["alternatives"]]
            if "steps" in q:
                q["steps"] = [latex_to_plain(s) for s in q["steps"]]
            if "socratic_hints" in q:
                q["socratic_hints"] = [latex_to_plain(h) for h in q["socratic_hints"]]
            if "common_errors" in q:
                q["common_errors"] = {latex_to_plain(k): latex_to_plain(v) for k, v in q["common_errors"].items()}
            # Generate IDs
            import time
            q.setdefault("id", f"book-{int(time.time() * 1000)}-{quiz_problems.index(q)}")
            q.setdefault("grade", "初二")
            q.setdefault("difficulty", 2)
            q.setdefault("topic", topic)
            q.setdefault("tags", [topic, "章节"])
            valid_quiz.append(q)

        # Use valid quiz problems
        quiz_problems = valid_quiz
        if not quiz_problems:
            print(f"{Color.YELLOW}⚠ 没有生成有效的练习题，跳过练习环节。{Color.RESET}")
        else:
            run_quiz(quiz_problems, subject, subjects, all_problems, loop_mode=False, persona=persona)

    print(f"\n{Color.BOLD}{Color.CYAN}📖「{title}」学习完成！{Color.RESET}")
    print(f"{Color.CYAN}{'═' * 50}{Color.RESET}\n")
