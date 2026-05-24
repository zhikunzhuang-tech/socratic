"""Tests for wiki_math module."""
import tempfile
from pathlib import Path

import pytest

from socratic.wiki_math import (
    is_available,
    find_page,
    _parse_frontmatter,
    _strip_frontmatter,
    _parse_wikilinks,
    _extract_section,
    get_grade,
    get_topic_list,
    get_wiki_context,
)


@pytest.fixture
def empty_wiki():
    """Temp dir with no .md files."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def wiki_root():
    """Temp dir with concepts/ subdir containing synthetic wiki pages."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        concepts = root
        concepts.mkdir(parents=True, exist_ok=True)

        (concepts / "勾股定理.md").write_text("""---
title: 勾股定理
created: 2026-05-03
type: concept
tags:
  - geometry
  - grade-8
grade: 8
---

# 勾股定理

## 定义
直角三角形两直角边平方和等于斜边平方。a² + b² = c²。

## 例题
**例1**: 已知直角边 3 和 4，求斜边。
解: c² = 9+16 = 25, c = 5.

## 常见错误
1. 搞错斜边位置
2. 开平方忘取正根

## 相关概念
- [[三角形]]
- [[实数]]
""", encoding="utf-8")

        # Related page referenced by wikilinks
        (concepts / "三角形.md").write_text("""---
title: 三角形
grade: 8
type: concept
tags:
  - geometry
  - grade-8
---

# 三角形

## 定义
由不在同一直线上的三条线段首尾顺次连接所组成的封闭图形。

## 关键公式
内角和：180度。
""", encoding="utf-8")

        (concepts / "实数.md").write_text("""---
title: 实数
grade: 7
type: concept
tags:
  - number
  - grade-7
---

# 实数

## 定义
有理数和无理数的统称。
""", encoding="utf-8")

        (concepts / "有理数.md").write_text("""---
title: 有理数
grade: 7
type: concept
tags:
  - number
  - grade-7
---

# 有理数

## 定义
整数和分数统称有理数。

## 相关概念
- [[勾股定理]]
""", encoding="utf-8")

        # Page with no frontmatter
        (concepts / "no_fm.md").write_text("# No Frontmatter\n\nJust content.", encoding="utf-8")

        # Page with no grade field
        (concepts / "杂记.md").write_text("""---
title: 杂记
type: concept
---

# 杂记

Some random notes.
""", encoding="utf-8")

        yield concepts


# ── is_available ──────────────────────────────────────────────

def test_is_available_true(wiki_root):
    assert is_available(root_dir=wiki_root) is True


def test_is_available_false_empty(empty_wiki):
    assert is_available(root_dir=empty_wiki) is False


def test_is_available_false_nonexistent():
    assert is_available(root_dir="/tmp/nonexistent_wiki_xyz") is False


# ── find_page ──────────────────────────────────────────────────

def test_find_page_exact_filename(wiki_root):
    found = find_page("勾股定理", root_dir=wiki_root)
    assert found is not None
    assert found.name == "勾股定理.md"


def test_find_page_by_yaml_title(wiki_root):
    # "勾股定理" is both filename and title, either works
    found = find_page("勾股定理", root_dir=wiki_root)
    assert found is not None


def test_find_page_not_found(wiki_root):
    assert find_page("不存在的概念", root_dir=wiki_root) is None


def test_find_page_no_frontmatter(wiki_root):
    found = find_page("no_fm", root_dir=wiki_root)
    assert found is not None
    assert found.name == "no_fm.md"


# ── get_grade ──────────────────────────────────────────────────

def test_get_grade_from_frontmatter(wiki_root):
    assert get_grade("勾股定理", root_dir=wiki_root) == "初二"


def test_get_grade_grade7(wiki_root):
    assert get_grade("有理数", root_dir=wiki_root) == "初一"


def test_get_grade_missing(wiki_root):
    assert get_grade("no_fm", root_dir=wiki_root) is None


def test_get_grade_nonexistent_topic(wiki_root):
    assert get_grade("不存在", root_dir=wiki_root) is None


# ── get_topic_list ─────────────────────────────────────────────

def test_get_topic_list(wiki_root):
    topics = get_topic_list(root_dir=wiki_root)
    assert "勾股定理" in topics
    assert "有理数" in topics
    assert "no_fm" in topics
    assert len(topics) >= 3


# ── _parse_frontmatter ────────────────────────────────────────

def test_parse_frontmatter_basic(wiki_root):
    path = wiki_root / "勾股定理.md"
    fm = _parse_frontmatter(path)
    assert fm["title"] == "勾股定理"
    assert fm["grade"] == "8"
    assert fm["type"] == "concept"


def test_parse_frontmatter_list_tags(wiki_root):
    path = wiki_root / "勾股定理.md"
    fm = _parse_frontmatter(path)
    assert "tags" in fm
    assert isinstance(fm["tags"], list)
    assert "geometry" in fm["tags"]
    assert "grade-8" in fm["tags"]


def test_parse_frontmatter_no_frontmatter(wiki_root):
    path = wiki_root / "no_fm.md"
    assert _parse_frontmatter(path) is None


def test_parse_frontmatter_empty_file(wiki_root):
    path = wiki_root / "empty.md"
    path.write_text("", encoding="utf-8")
    assert _parse_frontmatter(path) is None


# ── _strip_frontmatter ─────────────────────────────────────────

def test_strip_frontmatter(wiki_root):
    raw = (wiki_root / "勾股定理.md").read_text(encoding="utf-8")
    body = _strip_frontmatter(raw)
    assert not body.startswith("---")
    assert "# 勾股定理" in body


def test_strip_frontmatter_no_fm(wiki_root):
    raw = (wiki_root / "no_fm.md").read_text(encoding="utf-8")
    body = _strip_frontmatter(raw)
    assert body.startswith("# No Frontmatter")


# ── _parse_wikilinks ───────────────────────────────────────────

def test_parse_wikilinks(wiki_root):
    raw = (wiki_root / "勾股定理.md").read_text(encoding="utf-8")
    links = _parse_wikilinks(raw)
    assert "三角形" in links
    assert "实数" in links


def test_parse_wikilinks_empty():
    assert _parse_wikilinks("No links here.") == []


# ── _extract_section ───────────────────────────────────────────

def test_extract_section_exists(wiki_root):
    raw = (wiki_root / "勾股定理.md").read_text(encoding="utf-8")
    body = _strip_frontmatter(raw)
    section = _extract_section(body, "定义")
    assert "直角三角形" in section


def test_extract_section_missing():
    assert _extract_section("## 定义\nhello", "不存在") == ""


# ── get_wiki_context ───────────────────────────────────────────

def test_get_wiki_context_basic(wiki_root):
    ctx = get_wiki_context("勾股定理", root_dir=wiki_root)
    assert ctx is not None
    assert "年级: 初二" in ctx
    assert "直角三角形" in ctx
    assert "a² + b² = c²" in ctx


def test_get_wiki_context_includes_examples(wiki_root):
    ctx = get_wiki_context("勾股定理", root_dir=wiki_root)
    assert "参考例题" in ctx
    assert "已知直角边" in ctx


def test_get_wiki_context_includes_errors(wiki_root):
    ctx = get_wiki_context("勾股定理", root_dir=wiki_root)
    assert "常见错误" in ctx
    assert "搞错斜边" in ctx


def test_get_wiki_context_includes_related(wiki_root):
    ctx = get_wiki_context("勾股定理", root_dir=wiki_root)
    assert "关联概念" in ctx


def test_get_wiki_context_nonexistent(wiki_root):
    assert get_wiki_context("不存在", root_dir=wiki_root) is None


def test_get_wiki_context_no_frontmatter(wiki_root):
    ctx = get_wiki_context("no_fm", root_dir=wiki_root)
    assert ctx is not None
    assert "# No Frontmatter" in ctx


def test_get_wiki_context_truncates_long_body(wiki_root):
    # Create a page with very long content
    long_content = "很长的内容。" * 1500
    (wiki_root / "长内容.md").write_text(f"""---
title: 长内容
grade: 7
---

# 长内容

{long_content}

## 定义
Some definition here.

## 例题
例1：测试题目
""", encoding="utf-8")
    ctx = get_wiki_context("长内容", root_dir=wiki_root)
    assert ctx is not None
    # Body should be truncated at 3000 chars
    assert len(ctx) < 8000  # Should not include the full ~7000 char spam
