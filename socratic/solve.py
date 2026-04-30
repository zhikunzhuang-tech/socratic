"""--solve 模式：自由输入题目，AI 苏格拉底引导"""
import subprocess as sp
from .utils import Color, latex_to_plain


def run_solve_mode(subject: str, subjects: dict):
    """自由输入题目，AI 苏格拉底引导解题"""
    subj = subjects[subject]
    print(f"\n{Color.BOLD}{Color.CYAN}🧠 苏格拉底解题引导 — {subj['icon']} {subj['name']}{Color.RESET}")
    print(f"{Color.DIM}输入你的题目，AI 会一步步引导你思考，而不是直接给答案{Color.RESET}")
    print(f"{Color.DIM}捷径：h 更多提示 | s 显示完整解法 | q 退出{Color.RESET}")
    print(f"{Color.CYAN}{'─' * 50}{Color.RESET}")

    print(f"\n{Color.BOLD}{Color.GREEN}📝 请输入你的题目：{Color.RESET} ", end="")
    try:
        user_question = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not user_question or user_question.lower() in ("q", "quit", "退出"):
        return

    system_prompt = (
        f"你是一位初中{subj['name']}苏格拉底式辅导老师。\n"
        "永远不要直接告诉学生答案。用提问引导学生自己发现解题思路。\n"
        f"学生的问题：{user_question}\n"
        "第一步：分析这道题属于什么知识点，然后给学生一个引导性的问题。"
    )

    print(f"\n{Color.CYAN}🤖 AI 辅导老师：{Color.RESET}")
    result = sp.run(["sgpt", system_prompt], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"{Color.RED}⚠ AI 响应失败。{Color.RESET}")
        return
    response = _clean_sgpt(result.stdout)
    print(f"  {response}")

    history = [("user", user_question), ("assistant", response)]
    showed_solution = False

    while True:
        print(f"\n{Color.BOLD}{Color.GREEN}你的回答（或 h/s/q）：{Color.RESET} ", end="")
        try:
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            print(f"  {Color.YELLOW}试试回答刚才的问题～{Color.RESET}")
            continue

        c = user_input.lower()
        if c in ("q", "quit", "退出", "qq"):
            break

        if c in ("s", "skip", "跳过"):
            showed_solution = True
            _show_solution(subj, user_question)
            break

        if c in ("h", "hint", "提示"):
            _show_hint(subj, user_question, history)
            history.append(("user", user_input))
            continue

        # 正常对话
        hist_text = "\n".join(
            f"{'学生' if r == 'user' else '老师'}: {c}" for r, c in history[-6:]
        )
        prompt = (
            f"你是一位初中{subj['name']}苏格拉底式辅导老师。\n"
            "永远不要直接说出答案。用提问引导学生。\n"
            f"学生的问题：{user_question}\n教学对话：\n{hist_text}\n"
            f"学生说：{user_input}\n"
            "如果正确→表扬，然后给下一道引导问题。如果不对→指出哪里需要重新思考，给一个新的引导性问题。"
        )
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            continue
        response = _clean_sgpt(result.stdout)
        print(f"\n{Color.CYAN}🤖 AI 辅导老师：{Color.RESET}")
        print(f"  {response}")
        history.append(("user", user_input))
        history.append(("assistant", response))

    if not showed_solution:
        print(f"\n{Color.YELLOW}💪 学习需要时间，下次再来攻克这道题！{Color.RESET}")
    print(f"{Color.CYAN}{'─' * 50}{Color.RESET}")


def _clean_sgpt(text: str) -> str:
    text = "\n".join(l for l in text.split("\n") if not l.startswith("Warning:")).strip()
    return latex_to_plain(text)


def _show_solution(subj: dict, question: str):
    prompt = (
        f"你是一位初中{subj['name']}老师。学生的问题：{question}\n"
        "请用清晰步骤给出完整解答：解题思路、分步过程、最终答案、知识点总结。"
    )
    result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print(f"\n{Color.MAGENTA}━━ 完整解法 ━━{Color.RESET}")
        print(f"  {_clean_sgpt(result.stdout)}")


def _show_hint(subj: dict, question: str, history: list):
    hist = " ".join(f"{r}: {c}" for r, c in history[-4:])
    prompt = (
        f"你是一位初中{subj['name']}苏格拉底式辅导老师。\n"
        f"学生的问题：{question}。对话：{hist}\n"
        "学生需要更多提示。给出更具体的引导，用类比或更小的步骤，但仍然不要直接说出答案。"
    )
    result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        hint = _clean_sgpt(result.stdout)
        print(f"\n{Color.CYAN}💡 AI 提示：{Color.RESET}")
        print(f"  {hint}")
