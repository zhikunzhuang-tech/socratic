"""RAG 知识库 — 按主题存取概念讲解"""
import subprocess as sp
import json as j
from pathlib import Path
from .utils import DATA_DIR, Color, latex_to_plain
from .problems import SUBJECTS

KNOWLEDGE_DIR = DATA_DIR / "knowledge"


def _subject_dir(subject: str) -> Path:
    return KNOWLEDGE_DIR / subject


def _topic_path(subject: str, topic: str) -> Path:
    # 清理文件名中的特殊字符
    safe_name = topic.replace("/", "·").replace("\\", "·").replace(" ", "")
    return _subject_dir(subject) / f"{safe_name}.md"


def get(subject: str, topic: str) -> str | None:
    """按主题名获取知识卡片"""
    path = _topic_path(subject, topic)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def search(subject: str, keywords: str) -> list[dict]:
    """关键词搜索知识条目，返回 [{topic, content, match_score}]"""
    results = []
    sdir = _subject_dir(subject)
    if not sdir.exists():
        return results
    kw_lower = keywords.lower()
    for f in sorted(sdir.glob("*.md")):
        topic = f.stem
        content = f.read_text(encoding="utf-8")
        score = 0
        if kw_lower in topic.lower():
            score += 10
        if kw_lower in content.lower():
            score += content.lower().count(kw_lower)
        if score > 0:
            results.append({"topic": topic, "content": content, "score": score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def auto_generate(subject: str, topic: str) -> str | None:
    """用 sgpt 生成知识条目并保存"""
    name = SUBJECTS[subject]["name"]
    prompt = (
        f"你是一位初中{name}老师。请为「{topic}」写一个知识卡片。\n"
        "包含以下四个部分，用 markdown 标题：\n"
        "## 核心概念\n## 关键方法\n## 常见误区\n## 典型例题\n\n"
        "每个部分 2-5 句话。语言简洁，面向初中生。"
        "只输出知识卡片内容，不要其他文字。"
    )
    try:
        result = sp.run(["sgpt", prompt], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        text = "\n".join(l for l in result.stdout.split("\n") if not l.startswith("Warning:"))
        text = latex_to_plain(text).strip()
        if not text:
            return None
        # 确保有标题
        if not text.startswith("#"):
            text = f"# {topic}\n\n{text}"
        # 保存
        path = _topic_path(subject, topic)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text
    except Exception:
        return None


def ensure(subject: str, topic: str) -> str | None:
    """获取知识条目，不存在则自动生成"""
    cached = get(subject, topic)
    if cached:
        return cached
    # 尝试搜索相关条目
    related = search(subject, topic)
    if related:
        return related[0]["content"]
    # 自动生成
    return auto_generate(subject, topic)


def show_knowledge(subject: str, topic: str):
    """显示知识卡片（精简版：只显示核心概念和常见误区）"""
    content = ensure(subject, topic)
    if not content:
        return

    lines = content.split("\n")
    # 提取关键部分
    show_lines = []
    capture = False
    for line in lines:
        if line.startswith("## 核心概念") or line.startswith("## 关键方法") or line.startswith("## 常见误区"):
            capture = True
            show_lines.append(line)
        elif line.startswith("## "):
            capture = False
        elif capture and line.strip():
            show_lines.append(line)

    if not show_lines:
        # fallback: 显示前 6 行
        show_lines = [l for l in lines if l.strip()][:6]

    print(f"\n{Color.DIM}📖 知识点：「{topic}」{Color.RESET}")
    for line in show_lines:
        if line.startswith("## "):
            print(f"  {Color.BOLD}{Color.YELLOW}{line}{Color.RESET}")
        else:
            print(f"  {Color.DIM}{line}{Color.RESET}")
    print(f"{Color.DIM}{'─' * 40}{Color.RESET}")
