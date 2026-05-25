"""CSV 题库导入：将 CSV 转为种子题格式写入缓存。
CSV 格式：科目, 章节, 题目, 答案, 知识点
"""
import csv
import json
import sys
import time
from pathlib import Path
from .cache import load_cache, save_cache, CACHE_DIR
from .utils import DATA_DIR

SUBJECT_KEY = {
    "Claude Code": "claude",
    "claude": "claude",
    "Hermes Agent": "hermes",
    "hermes": "hermes",
    "hermes agent": "hermes",
    "常用命令": "cmd",
    "Linux": "cmd",
    "linux": "cmd",
    "cmd": "cmd",
}


def import_csv(csv_path: str, replace: bool = False) -> dict:
    """导入 CSV 文件，返回 {subject: count} 统计。

    replace=True 时替换全部缓存，否则追加（默认追加）。
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"错误：文件不存在 {csv_path}")
        sys.exit(1)

    # 自动检测编码
    content = path.read_bytes()
    if content[:3] == b"\xef\xbb\xbf":
        content = content[3:]
    encoding = "utf-8"
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        encoding = "gbk"

    reader = csv.reader(content.decode(encoding).splitlines())
    header = next(reader, None)
    if not header or len(header) < 4:
        print(f"错误：CSV 需要至少 4 列（科目, 章节, 题目, 答案, 知识点可选），实际 {len(header) if header else 0} 列")
        sys.exit(1)

    # 按科目分组
    questions_by_subject: dict[str, list] = {}
    for row in reader:
        if len(row) < 4:
            continue
        raw_subject = row[0].strip()
        if not raw_subject:
            continue
        subject = SUBJECT_KEY.get(raw_subject)
        if not subject:
            print(f"警告：未知科目 {raw_subject}，跳过")
            continue

        topic = row[1].strip() or "综合"
        question = row[2].strip()
        answer = row[3].strip()
        concept_note = row[4].strip() if len(row) > 4 and row[4].strip() else ""

        if not question or not answer:
            continue

        if subject not in questions_by_subject:
            questions_by_subject[subject] = []

        questions_by_subject[subject].append({
            "topic": topic,
            "question": question,
            "answer": answer,
            "concept_note": concept_note,
        })

    stats = {}
    tag = {"claude": "claude", "hermes": "hermes", "cmd": "cmd"}

    for subject, qs in questions_by_subject.items():
        existing = load_cache(subject)
        if replace:
            existing = []
        # 收集已有 ID 编号
        max_id = 0
        for p in existing:
            if p["id"].startswith(f"csv-{tag.get(subject, subject)}-"):
                try:
                    num = int(p["id"].rsplit("-", 1)[-1])
                    max_id = max(max_id, num)
                except ValueError:
                    pass
            elif "-" in p["id"]:
                try:
                    num = int(p["id"].rsplit("-", 1)[-1])
                    max_id = max(max_id, num)
                except ValueError:
                    pass

        imported = 0
        for q in qs:
            max_id += 1
            pid = f"csv-{tag.get(subject, subject)}-{max_id}"
            problem = {
                "id": pid,
                "topic": q["topic"],
                "grade": "入门",
                "difficulty": 1,
                "question": q["question"],
                "answer": q["answer"],
                "alternatives": [],
                "steps": [],
                "socratic_hints": [],
                "common_errors": {},
                "concept_note": q["concept_note"],
                "tags": [q["topic"]],
            }
            existing.append(problem)
            imported += 1

        save_cache(subject, existing)
        stats[subject] = imported

    return stats


def main():
    if len(sys.argv) < 2:
        print("用法：python -m socratic.import_csv <csv文件> [--replace]")
        print("  --replace  替换全部缓存（默认追加）")
        sys.exit(1)

    csv_path = sys.argv[1]
    replace = "--replace" in sys.argv
    stats = import_csv(csv_path, replace=replace)

    if not stats:
        print("未导入任何题目。")
        return

    total = sum(stats.values())
    print(f"\n导入完成：{total} 题")
    for subj, count in stats.items():
        cache = load_cache(subj)
        print(f"  {subj}: +{count} 题 → 共 {len(cache)} 题")


if __name__ == "__main__":
    main()
