"""Integration tests for wiki-math context injection in cache._generate()."""
import json
from unittest.mock import patch, MagicMock

import pytest

from socratic.cache import _generate


def _make_fake_sgpt_result(stdout: str, returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    return result


def _fake_idea_json(focus: str = "解方程步骤"):
    return json.dumps({"focus": focus, "question_type": "计算", "rationale": "考察基础"}, ensure_ascii=False)


def _fake_problem_json(answer: str = "5", grade: str = "初二"):
    return json.dumps({
        "question": "测试题",
        "answer": answer,
        "alternatives": [],
        "steps": ["步骤1", "步骤2"],
        "socratic_hints": ["提示1", "提示2", "提示3"],
        "common_errors": {"错1": "反馈1", "错2": "反馈2", "错3": "反馈3"},
        "concept_note": "核心概念",
    }, ensure_ascii=False)


# ── Grade mapping ──────────────────────────────────────────────

@patch("socratic.cache.sp.run")
@patch("socratic.cache.wiki_available", return_value=True)
@patch("socratic.cache.wiki_get_grade", return_value="初一下学期")  # Custom: 7 → 初一 but wiki says different
@patch("socratic.cache.get_wiki_context")
def test_math_uses_wiki_grade(mock_ctx, mock_grade, mock_avail, mock_run):
    """When wiki is available for math, grade comes from wiki, not difficulty."""
    mock_ctx.return_value = "wiki content"
    mock_run.side_effect = [
        _make_fake_sgpt_result(_fake_idea_json()),
        _make_fake_sgpt_result(_fake_problem_json()),
    ]

    result = _generate("math", topic="勾股定理")

    assert result is not None
    assert result["grade"] == "初一下学期"


@patch("socratic.cache.sp.run")
@patch("socratic.cache.wiki_available", return_value=False)
def test_math_without_wiki_falls_back_to_diff_grade(mock_avail, mock_run):
    """When wiki is not available, grade maps from difficulty."""
    # difficulty is random 1-3, so it's either 初一/初二/初三
    valid_grades = {"初一", "初二", "初三"}

    mock_run.side_effect = [
        _make_fake_sgpt_result(_fake_idea_json()),
        _make_fake_sgpt_result(_fake_problem_json()),
    ]

    result = _generate("math", topic="勾股定理")

    assert result is not None
    assert result["grade"] in valid_grades


# ── Context injection ─────────────────────────────────────────

@patch("socratic.cache.sp.run")
@patch("socratic.cache.wiki_available", return_value=True)
@patch("socratic.cache.wiki_get_grade", return_value="初二")
@patch("socratic.cache.get_wiki_context")
def test_math_injects_wiki_into_idea_prompt(mock_ctx, mock_grade, mock_avail, mock_run):
    """Wiki context is passed to Idea Agent when available."""
    mock_ctx.return_value = "===WIKI_CONTENT===勾股定理教材内容==="
    mock_run.side_effect = [
        _make_fake_sgpt_result(_fake_idea_json()),
        _make_fake_sgpt_result(_fake_problem_json()),
    ]

    _generate("math", topic="勾股定理")

    idea_call = mock_run.call_args_list[0]
    idea_prompt = idea_call[0][0][1]  # sp.run(["sgpt", prompt]) → prompt is args[0][1]
    assert "===WIKI_CONTENT===" in idea_prompt
    assert "人教版课本知识库" in idea_prompt


@patch("socratic.cache.sp.run")
@patch("socratic.cache.wiki_available", return_value=True)
@patch("socratic.cache.wiki_get_grade", return_value="初二")
@patch("socratic.cache.get_wiki_context")
def test_math_injects_wiki_into_gen_prompt(mock_ctx, mock_grade, mock_avail, mock_run):
    """Wiki context is passed to Generator when available."""
    mock_ctx.return_value = "===WIKI_CONTENT===二次函数内容==="
    mock_run.side_effect = [
        _make_fake_sgpt_result(_fake_idea_json("顶点坐标")),
        _make_fake_sgpt_result(_fake_problem_json()),
    ]

    _generate("math", topic="二次函数")

    gen_call = mock_run.call_args_list[1]
    gen_prompt = gen_call[0][0][1]
    assert "===WIKI_CONTENT===" in gen_prompt


# ── Non-math subjects unaffected ───────────────────────────────

@patch("socratic.cache.sp.run")
@patch("socratic.cache.wiki_available", return_value=True)
@patch("socratic.cache.get_wiki_context")
def test_non_math_ignores_wiki(mock_ctx, mock_avail, mock_run):
    """English subject should not get wiki context even if wiki is available."""
    mock_run.side_effect = [
        _make_fake_sgpt_result(_fake_idea_json()),
        _make_fake_sgpt_result(_fake_problem_json()),
    ]

    _generate("english", topic="主谓一致")

    idea_call = mock_run.call_args_list[0]
    idea_prompt = idea_call[0][0][1]
    assert "人教版课本知识库" not in idea_prompt
    mock_ctx.assert_not_called()


# ── User KB + wiki coexist ────────────────────────────────────

@patch("socratic.cache.sp.run")
@patch("socratic.cache.get_kb_context", return_value="用户上传的教材笔记")
@patch("socratic.cache.wiki_available", return_value=True)
@patch("socratic.cache.wiki_get_grade", return_value="初一")
@patch("socratic.cache.get_wiki_context")
def test_math_with_both_kb_and_wiki(mock_ctx, mock_grade, mock_avail, mock_kb, mock_run):
    """When both user KB and wiki exist, wiki takes priority and user KB is noted."""
    mock_ctx.return_value = "WIKI教材内容"
    mock_run.side_effect = [
        _make_fake_sgpt_result(_fake_idea_json()),
        _make_fake_sgpt_result(_fake_problem_json()),
    ]

    _generate("math", topic="一元一次方程")

    idea_call = mock_run.call_args_list[0]
    idea_prompt = idea_call[0][0][1]
    assert "WIKI教材内容" in idea_prompt
    assert "优先参考教材知识库" in idea_prompt
