"""
知识库管理 — 上传教材/文档，AI 基于你的资料出题
存储路径: ~/socratic/data/kb/<name>/
"""
import os
import sys
from pathlib import Path
from .utils import DATA_DIR, Color

KB_DIR = DATA_DIR / "kb"


def kb_create(name: str):
    """创建知识库"""
    path = KB_DIR / name
    if path.exists():
        print(f"{Color.YELLOW}⚠ 知识库「{name}」已存在{Color.RESET}")
        return
    path.mkdir(parents=True, exist_ok=True)
    print(f"{Color.GREEN}✅ 知识库「{name}」创建成功{Color.RESET}")


def kb_add(name: str, filepath: str):
    """添加文档到知识库"""
    kb_path = KB_DIR / name
    if not kb_path.exists():
        print(f"{Color.RED}⚠ 知识库「{name}」不存在，请先创建{Color.RESET}")
        return

    src = Path(filepath)
    if not src.exists():
        print(f"{Color.RED}⚠ 文件不存在：{filepath}{Color.RESET}")
        return

    # 支持 pdf, md, txt
    if src.suffix.lower() not in (".pdf", ".md", ".txt"):
        print(f"{Color.YELLOW}⚠ 仅支持 PDF/Markdown/TXT，尝试读取文本...{Color.RESET}")

    try:
        if src.suffix.lower() == ".pdf":
            # PDF 提取文本
            try:
                from pymupdf import open as pdf_open
                doc = pdf_open(str(src))
                text = "\n".join(page.get_text() for page in doc)
                doc.close()
            except ImportError:
                print(f"{Color.RED}⚠ 需要安装 pymupdf：pip install pymupdf{Color.RESET}")
                return
        else:
            text = src.read_text(encoding="utf-8", errors="replace")

        dest = kb_path / (src.name.replace(".", "_") + ".txt")
        dest.write_text(text, encoding="utf-8")
        size = len(text)
        print(f"{Color.GREEN}✅ 已添加：{src.name} → kb/{name}/ ({size} 字符){Color.RESET}")
    except Exception as e:
        print(f"{Color.RED}⚠ 添加失败：{e}{Color.RESET}")


def kb_list():
    """列出所有知识库"""
    if not KB_DIR.exists():
        print(f"{Color.DIM}  暂无知识库{Color.RESET}")
        return

    kbs = sorted(d for d in KB_DIR.iterdir() if d.is_dir())
    if not kbs:
        print(f"{Color.DIM}  暂无知识库{Color.RESET}")
        return

    for kb in kbs:
        files = sorted(f for f in kb.iterdir() if f.suffix == ".txt")
        total = sum(f.stat().st_size for f in files)
        print(f"  📚 {kb.name}  ({len(files)} 个文档, {total // 1024}KB)")
        for f in files:
            print(f"     📄 {f.name}")


def kb_show(name: str):
    """查看知识库详情"""
    kb_path = KB_DIR / name
    if not kb_path.exists():
        print(f"{Color.RED}⚠ 知识库「{name}」不存在{Color.RESET}")
        return

    files = sorted(f for f in kb_path.iterdir() if f.suffix == ".txt")
    print(f"\n{Color.BOLD}📚 {name}{Color.RESET}  ({len(files)} 个文档)")
    for f in files:
        content = f.read_text(encoding="utf-8")
        preview = content[:200].replace("\n", " ")
        print(f"\n  {Color.BOLD}📄 {f.name}{Color.RESET}")
        print(f"  {Color.DIM}{preview}...{Color.RESET}")


def kb_get_content(name: str) -> str:
    """获取知识库全部文本（供 AI 出题使用）"""
    kb_path = KB_DIR / name
    if not kb_path.exists():
        return ""

    texts = []
    for f in sorted(kb_path.iterdir()):
        if f.suffix == ".txt":
            texts.append(f.read_text(encoding="utf-8"))
    return "\n\n".join(texts)


def kb_delete(name: str):
    """删除知识库"""
    import shutil
    kb_path = KB_DIR / name
    if not kb_path.exists():
        print(f"{Color.RED}⚠ 知识库「{name}」不存在{Color.RESET}")
        return
    shutil.rmtree(kb_path)
    print(f"{Color.GREEN}✅ 知识库「{name}」已删除{Color.RESET}")
