import json
from types import SimpleNamespace

from pathlib import Path

from eval.humaneval_utils import (
    HumanEvalTask,
    build_codebook_entries,
    build_prompt_text,
    load_humaneval_tasks,
    render_codebook_text,
)


def test_build_codebook_entries_merges_stage1_and_stage3_entries():
    repo_config = SimpleNamespace(
        skeleton_candidates=lambda: [SimpleNamespace(skeleton="def {0}({1}):")]
    )
    breakdown = SimpleNamespace(
        stage3_metrics={
            "stage3_ab_vocab_entries": [
                {"token": "__ab0", "definition": "user_name_long_identifier", "kind": "stage3_ab_a_alias"},
                {"token": "__ab0", "definition": "user_name_long_identifier", "kind": "stage3_ab_a_alias"},
            ]
        }
    )
    entries = build_codebook_entries(
        ["<SYN_0> foo bar\nfoo = __ab0\n"],
        [breakdown],
        repo_config,
    )
    assert [x["token"] for x in entries] == ["<SYN_0>", "__ab0"]
    text = render_codebook_text(entries)
    assert "<SYN_0> => def {0}({1}):" in text
    assert "__ab0 => user_name_long_identifier" in text


def test_build_codebook_entries_can_drop_static_stage1_entries():
    repo_config = SimpleNamespace(
        skeleton_candidates=lambda: [SimpleNamespace(skeleton="def {0}({1}):")]
    )
    breakdown = SimpleNamespace(
        stage3_metrics={
            "stage3_ab_vocab_entries": [
                {"token": "__ab0", "definition": "user_name_long_identifier", "kind": "stage3_ab_a_alias"},
            ]
        }
    )
    entries = build_codebook_entries(
        ["<SYN_0> foo bar\nfoo = __ab0\n"],
        [breakdown],
        repo_config,
        include_stage1=False,
        include_stage3=True,
    )
    assert entries == [
        {"token": "__ab0", "definition": "user_name_long_identifier", "kind": "stage3_ab_a_alias"}
    ]


def test_build_prompt_text_for_compressed_arm_includes_dictionary():
    task = HumanEvalTask(
        task_id="HumanEval/0",
        prompt="def foo(x):\n    pass\n",
        entry_point="foo",
    )
    prompt = build_prompt_text(
        task,
        support_text="# [Compressed Support 1]\n<SYN_0> foo x",
        compressed=True,
        codebook_text="<SYN_0> => def {0}({1}):",
    )
    assert "Compression dictionary:" in prompt
    assert "<SYN_0> => def {0}({1}):" in prompt
    assert "Task prompt:\ndef foo(x):" in prompt


def test_build_prompt_text_structured_mode_uses_tags_only():
    task = HumanEvalTask(
        task_id="HumanEval/0",
        prompt="def foo(x):\n    pass\n",
        entry_point="foo",
    )
    prompt = build_prompt_text(
        task,
        support_text="# [Compressed Support 1]\n__ab0 = 1",
        compressed=True,
        codebook_text="__ab0 => user_name_long_identifier",
        prompt_style="structured",
    )
    assert "<LANGV1_HUMANEVAL>" in prompt
    assert "<DYNAMIC_DICT>" in prompt
    assert "<COMPRESSED_SUPPORT>" in prompt
    assert "<TASK_PROMPT>" in prompt
    assert "Compression dictionary:" not in prompt
    assert "The support context may be compressed." not in prompt


def test_load_humaneval_tasks_from_local_jsonl(tmp_path: Path):
    rows = [
        {
            "task_id": "HumanEval/0",
            "prompt": "def foo(x):\n    pass\n",
            "entry_point": "foo",
            "canonical_solution": "    return x\n",
            "test": "def check(candidate):\n    assert candidate(1) == 1\n",
        }
    ]
    fp = tmp_path / "humaneval.jsonl"
    with fp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    tasks = load_humaneval_tasks(jsonl_path=fp)
    assert len(tasks) == 1
    assert tasks[0].task_id == "HumanEval/0"
    assert tasks[0].entry_point == "foo"
