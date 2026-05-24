"""Wiki-math adapter — reads ~/wiki-math for math question generation context."""
import re
from pathlib import Path

WIKI_MATH_DIR = Path.home() / "wiki-math"
CONCEPTS_DIR = WIKI_MATH_DIR / "concepts"

_GRADE_MAP = {"7": "初一", "8": "初二", "9": "初三"}


def _concepts_dir(root_dir: str | Path | None = None) -> Path:
    if root_dir:
        return Path(root_dir)
    return CONCEPTS_DIR


def is_available(root_dir: str | Path | None = None) -> bool:
    d = _concepts_dir(root_dir)
    return d.is_dir() and any(d.glob("*.md"))


def find_page(topic: str, root_dir: str | Path | None = None) -> Path | None:
    """Find wiki page matching a socratic topic name."""
    concepts = _concepts_dir(root_dir)
    exact = concepts / f"{topic}.md"
    if exact.exists():
        return exact
    # Fuzzy: match by YAML title field
    for f in concepts.glob("*.md"):
        fm = _parse_frontmatter(f)
        if fm and fm.get("title") == topic:
            return f
    # Broader fuzzy: topic is substring of filename or title
    for f in concepts.glob("*.md"):
        if topic in f.stem:
            return f
        fm = _parse_frontmatter(f)
        if fm and topic in fm.get("title", ""):
            return f
    return None


def _parse_frontmatter(path: Path) -> dict | None:
    """Parse YAML frontmatter from a wiki page."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    frontmatter = text[3:end].strip()
    result = {}
    list_key = None
    for line in frontmatter.split("\n"):
        if ":" in line and not line.strip().startswith("-"):
            list_key = None
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                result[key] = val
            else:
                list_key = key
                result[key] = []
        elif list_key and line.strip().startswith("-"):
            result[list_key].append(line.strip()[1:].strip())
    return result


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text


def _parse_wikilinks(text: str) -> list[str]:
    """Extract [[page names]] from wiki text."""
    return re.findall(r'\[\[([^\]]+)\]\]', text)


def _extract_section(text: str, heading: str) -> str:
    """Extract a section by heading, returns empty string if not found."""
    pattern = rf'^##\s+{re.escape(heading)}'
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            start = i
            break
    if start is None:
        return ""
    result = [lines[start]]
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        result.append(line)
    return "\n".join(result).strip()


def get_grade(topic: str, root_dir: str | Path | None = None) -> str | None:
    """Get textbook grade (初一/初二/初三) from wiki frontmatter."""
    page = find_page(topic, root_dir=root_dir)
    if not page:
        return None
    fm = _parse_frontmatter(page)
    if not fm:
        return None
    raw = fm.get("grade", "")
    return _GRADE_MAP.get(str(raw))


def get_topic_list(root_dir: str | Path | None = None) -> list[str]:
    """Get all available topic titles from wiki-math."""
    concepts = _concepts_dir(root_dir)
    topics = []
    for f in concepts.glob("*.md"):
        fm = _parse_frontmatter(f)
        if fm:
            title = fm.get("title", f.stem)
            topics.append(title)
        else:
            topics.append(f.stem)
    return sorted(topics)


def get_wiki_context(topic: str, max_related: int = 2,
                     root_dir: str | Path | None = None) -> str | None:
    """Build wiki context for AI question generation.

    Returns formatted markdown with the concept page content and related page excerpts.
    """
    page = find_page(topic, root_dir=root_dir)
    if not page:
        return None

    raw = page.read_text(encoding="utf-8")
    fm = _parse_frontmatter(page)
    body = _strip_frontmatter(raw)
    grade = _GRADE_MAP.get(str(fm.get("grade", ""))) if fm else None

    # Collect related pages from wikilinks
    wikilinks = _parse_wikilinks(body)
    related_snippets = []
    seen = {topic}
    for link in wikilinks:
        if len(related_snippets) >= max_related:
            break
        link_page = find_page(link, root_dir=root_dir)
        if not link_page or link in seen:
            continue
        seen.add(link)
        link_body = _strip_frontmatter(link_page.read_text(encoding="utf-8"))
        snippet = _extract_section(link_body, "定义")
        if not snippet:
            snippet = _extract_section(link_body, "关键公式")
        if snippet:
            snippet = snippet[:300]
            related_snippets.append(f"### 相关概念: {link}\n{snippet}")

    # Emphasize 常见错误 and 例题 sections
    errors = _extract_section(body, "常见错误")
    examples = _extract_section(body, "例题")

    # Build compact context
    parts = []
    if grade:
        parts.append(f"年级: {grade}")
    parts.append(body[:3000])

    if examples:
        examples_short = examples[:1500]
        parts.append(f"\n## 参考例题（出题时参考风格，但不要原样照搬）\n{examples_short}")
    if errors:
        errors_short = errors[:600]
        parts.append(f"\n## 常见错误（出题时确保 common_errors 覆盖这些）\n{errors_short}")
    if related_snippets:
        parts.append(f"\n## 关联概念（可融入题目背景）\n" + "\n".join(related_snippets))

    return "\n\n".join(parts)
