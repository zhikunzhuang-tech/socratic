"""
学习路径 — AI 基于教材 + 掌握度规划学习步骤，逐章过关
"""
import json
import subprocess as sp
from pathlib import Path
from .utils import Color, DATA_DIR
from .cache import load_cache, get_problems, save_cache, get_all_problems
from .progress import load_progress, save_progress
from .quiz import run_quiz


def get_mastery_summary(subject: str) -> str:
    """获取掌握度摘要（供 AI 规划路径用）"""
    progress = load_progress(subject)
    mastery = progress.get("mastery", {})
    if not mastery:
        return "暂无掌握度数据"
    lines = []
    for t, v in sorted(mastery.items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {v*100:.0f}%")
    return "\n".join(lines)


def get_kb_chapters(kb_name: str | None) -> list:
    """从 KB 中提取章节信息"""
    if not kb_name:
        return []
    from .kb import kb_get_content
    text = kb_get_content(kb_name)
    if not text:
        return []
    # 提取 ## 标题作为章节名
    chapters = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("## ") and "第" in line and "章" in line:
            chapters.append(line[3:].strip())
    return chapters


def plan_path(subject: str, kb_name: str | None) -> list[dict]:
    """AI 规划学习路径"""
    chapters = get_kb_chapters(kb_name)
    mastery_summary = get_mastery_summary(subject)
    subj_name = {"math": "数学", "english": "英语", "physics": "物理", "chinese": "语文"}.get(subject, subject)

    prompt = f"""你是初中{subj_name}教师，正在为学生规划学习路径。

教材章节（按顺序）：
{chr(10).join(f'{i+1}. {c}' for i, c in enumerate(chapters[:20])) if chapters else '无教材章节'}

学生当前各主题掌握度：
{mastery_summary}

要求：
1. 按教材章节顺序规划路径
2. 掌握度低于 60% 的弱项章节多安排强化步骤
3. 掌握度高于 80% 的强项章节可以合并或跳过
4. 每个步骤包含：topic（章名）、difficulty（基础/进阶/强化）、questions（题数，弱项至少 3 题）

只输出 JSON 数组，不要 markdown，格式：
[{{"topic":"勾股定理","difficulty":"基础","questions":3}}, ...]
"""

    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return _plan_fallback(chapters)
        text = " ".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:")).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        plan = json.loads(text)
        if isinstance(plan, list) and len(plan) > 0:
            return plan
        return _plan_fallback(chapters)
    except Exception:
        return _plan_fallback(chapters)


def _plan_fallback(chapters: list) -> list[dict]:
    """降级：按教材顺序返回基础路径"""
    if not chapters:
        return [{"topic": "综合", "difficulty": "基础", "questions": 3}]
    return [{"topic": c.strip(), "difficulty": "基础", "questions": 3} for c in chapters[:8]]


def get_step_mastery(progress: dict, topic: str) -> float:
    """获取主题掌握度"""
    return progress.get("mastery", {}).get(topic, 0.5)


def update_step_mastery(progress: dict, topic: str, difficulty: int, solved: bool):
    """更新主题掌握度"""
    progress.setdefault("mastery", {})
    cur = progress["mastery"].get(topic, 0.5)
    if solved:
        gain = 0.12 / difficulty
        cur = min(1.0, cur + gain)
    else:
        loss = 0.08 * difficulty
        cur = max(0.0, cur - loss)
    progress["mastery"][topic] = round(cur, 3)


def run_path(subject: str, kb_name: str | None = None, **kwargs):
    """执行学习路径"""
    print(f"\n{Color.BOLD}{Color.CYAN}📋 学习路径 — {subject}{Color.RESET}")
    print(f"{Color.DIM}{'─' * 50}{Color.RESET}")

    # 检查是否已有进行中的路径
    progress = load_progress(subject)
    saved_path = progress.get("_path", {})
    current_step = saved_path.get("current_step", 0)
    saved_steps = saved_path.get("steps", [])

    if saved_steps and current_step < len(saved_steps):
        print(f"{Color.DIM}  检测到未完成的路径：第 {current_step + 1}/{len(saved_steps)} 步{Color.RESET}")
        try:
            choice = input(f"{Color.BOLD}  是否继续？(y/n, 回车继续){Color.RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "n"
        if choice and choice not in ("y", "yes", "是", ""):
            saved_steps = []
            current_step = 0

    # 规划新路径
    if not saved_steps:
        print(f"{Color.YELLOW}🤖 AI 正在规划学习路径…{Color.RESET}")
        plan = plan_path(subject, kb_name)
        if not plan:
            print(f"{Color.RED}⚠ 路径规划失败{Color.RESET}")
            return
        saved_steps = plan
        current_step = 0
        # 显示路径
        print(f"\n{Color.BOLD}📚 学习计划 ({len(plan)} 步){Color.RESET}")
        for i, step in enumerate(plan):
            tag = "🎯" if i == current_step else "⬜"
            print(f"  {tag} [{i+1}] {step['topic']} — {step['difficulty']}（{step['questions']} 题）")
        print()
        try:
            input(f"{Color.BOLD}按回车开始学习{Color.RESET} ")
        except (EOFError, KeyboardInterrupt):
            return

    # 逐步骤执行
    from .problems import SUBJECTS, ALL_PROBLEMS
    from .persona import get_persona

    persona = get_persona("gentle")
    subj = SUBJECTS.get(subject, {})

    while current_step < len(saved_steps):
        step = saved_steps[current_step]
        topic = step["topic"]
        difficulty = step.get("difficulty", "基础")
        target_questions = step.get("questions", 3)

        # 检查此章节掌握度
        mastery = get_step_mastery(progress, topic)
        mastery_pct = int(mastery * 100)
        passing = mastery >= 0.70
        diff_tag = "✅ 已达标" if passing else f"💪 需强化 ({mastery_pct}%)"
        level = {"基础": 1, "进阶": 2, "强化": 3}

        print(f"\n{Color.BOLD}{Color.CYAN}━━━ 第 {current_step + 1} 步：{topic}（{difficulty}）{diff_tag}{Color.RESET}")
        print(f"{Color.DIM}{'─' * 50}{Color.RESET}")

        if passing:
            # 已达标，快速通过
            print(f"{Color.GREEN}✅ 此章节已掌握，跳过{Color.RESET}")
            current_step += 1
            saved_path = {"steps": saved_steps, "current_step": current_step}
            progress["_path"] = saved_path
            save_progress(progress, subject)
            continue

        # 出题学习
        questions_done = 0
        max_attempts = target_questions * 3  # 防止死循环

        for attempt in range(max_attempts):
            if get_step_mastery(progress, topic) >= 0.70:
                # 达标了
                mastery = get_step_mastery(progress, topic)
                print(f"\n{Color.GREEN}🎉 {topic} 已达标！（掌握度 {int(mastery*100)}%）{Color.RESET}")
                break

            # 生成题目
            done_ids = set()
            try:
                problems = get_problems(subject, count=1, topic=topic, exclude_ids=done_ids)
            except Exception:
                problems = []

            if not problems:
                print(f"{Color.DIM}  暂时没有更多题目，跳过{Color.RESET}")
                break

            problem = problems[0]
            done_ids.add(problem["id"])

            # 答题（简化版：提问 → 答对/错 → 更新掌握度）
            print(f"\n{Color.BOLD}{Color.YELLOW}题目：{Color.RESET} {problem['question'][:80]}")
            try:
                user_input = input(f"{Color.BOLD}你的答案是？{Color.RESET} ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return

            if user_input in ("q", "quit", "退出", "qq"):
                # 保存进度并退出
                saved_path = {"steps": saved_steps, "current_step": current_step}
                progress["_path"] = saved_path
                save_progress(progress, subject)
                print(f"{Color.BOLD}{Color.CYAN}\n📋 已保存学习进度！下次继续第 {current_step + 1} 步{Color.RESET}")
                return

            # 判断对错（简化匹配）
            from .utils import normalize_answer
            correct = normalize_answer(user_input) == normalize_answer(problem["answer"])
            # 还检查 alternatives
            if not correct:
                for alt in problem.get("alternatives", []):
                    if normalize_answer(user_input) == normalize_answer(alt):
                        correct = True
                        break

            if correct:
                print(f"{Color.GREEN}✅ 正确！{Color.RESET}")
                update_step_mastery(progress, topic, level.get(difficulty, 1), True)
                questions_done += 1
            else:
                print(f"{Color.RED}❌ 不对，答案：{problem['answer']}{Color.RESET}")
                update_step_mastery(progress, topic, level.get(difficulty, 1), False)

            # 每轮保存
            save_progress(progress, subject)

        # 步骤完成
        current_step += 1
        saved_path = {"steps": saved_steps, "current_step": current_step}
        progress["_path"] = saved_path
        save_progress(progress, subject)

        # 询问是否继续
        if current_step < len(saved_steps):
            next_step = saved_steps[current_step]
            try:
                cont = input(f"\n{Color.BOLD}进入下一步「{next_step['topic']}」？(回车继续 / q 退出){Color.RESET} ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                cont = "q"
            if cont in ("q", "quit", "退出", "qq"):
                print(f"{Color.CYAN}📋 保存进度，下次继续第 {current_step + 1} 步{Color.RESET}")
                return

    # 全部完成
    print(f"\n{Color.BOLD}{Color.GREEN}🎉 学习路径全部完成！{Color.RESET}")
    # 清除路径状态
    if "_path" in progress:
        del progress["_path"]
        save_progress(progress, subject)
