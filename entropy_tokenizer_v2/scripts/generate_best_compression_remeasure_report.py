from __future__ import annotations

import csv
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import EVAL_TOKENIZERS
from marker_count import count_augmented
from markers import RE_ALL_MARKERS
from pipeline import apply_stage1_stage2_adapted, apply_stage1_with_stats, apply_stage2
from repo_miner import RepoConfig, _load_tokenizer
from stage3.backends import get_stage3_backend

RESULTS_DIR = ROOT / "results"
DOCS_DIR = ROOT / "docs"
CACHE_DIR = ROOT / "cache"

ABLATION_CSV = RESULTS_DIR / "stage3_hybrid_ab_s12_ablation.csv"
REPORT_MD = DOCS_DIR / "BEST_COMPRESSION_REMEASURE_2026-04-17.md"
ARTIFACT_JSON = RESULTS_DIR / "best_compression_remeasure_samples_2026-04-17.json"


def _read_ablation_rows() -> list[dict[str, str]]:
    with ABLATION_CSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def _int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def _load_current_repo_config() -> RepoConfig:
    cfg = CACHE_DIR / "repo_config_gpt4_eval_80_s2_hybrid_ab_auto_hybrid_ab_exact_only_s1f12_mtn0.json"
    if not cfg.exists():
        raise FileNotFoundError(f"missing cache file: {cfg}")
    repo_config = RepoConfig.from_json(cfg.read_text(encoding="utf-8"))
    repo_config.stage3_backend = "hybrid_ab"
    return repo_config


def _load_gpt4_tokenizer():
    return _load_tokenizer("gpt4", EVAL_TOKENIZERS["gpt4"])


def _count_tokens(text: str, tokenizer, tok_type: str) -> int:
    return count_augmented(text, tokenizer, tok_type, pattern=RE_ALL_MARKERS)


def _strip(text: str) -> str:
    return text.strip("\n")


def _find_stage1_marker(stats: dict[str, dict], skeleton: str) -> str:
    if skeleton not in stats or not stats[skeleton]["replaced_occurrences"]:
        return ""
    rc = _load_current_repo_config()
    for idx, candidate in enumerate(rc.skeleton_candidates()):
        if candidate.skeleton == skeleton:
            return f"<SYN_{idx}>"
    return ""


def _format_table(headers: list[str], rows: list[list[str]]) -> str:
    sep = ["---"] * len(headers)
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def _top_stage1_skeleton_rows(repo_config: RepoConfig, limit: int = 5) -> list[list[str]]:
    rows: list[list[str]] = []
    for idx, row in enumerate(repo_config.selected_skeletons[:limit], start=1):
        rows.append(
            [
                str(idx),
                f"`{row['skeleton']}`",
                str(row["frequency"]),
                str(row["effective_total_net_saving"]),
            ]
        )
    return rows


def _run_mainline_example(repo_config: RepoConfig, tokenizer, tok_type: str) -> dict:
    source = dedent(
        """\
        def hydrate_customer_identifier(customer_identifier_payload, customer_identifier_lookup, customer_identifier_cache):
            customer_identifier_payload = customer_identifier_lookup.get(customer_identifier_payload, customer_identifier_payload)
            customer_identifier_cache[customer_identifier_payload] = customer_identifier_payload
            customer_identifier_lookup[customer_identifier_payload] = customer_identifier_payload
            customer_identifier_payload = customer_identifier_payload.strip()
            audit_event_label = "customer identifier payload mismatch"
            failure_message = "customer identifier payload mismatch"
            fallback_message = "customer identifier payload mismatch"
            return customer_identifier_payload
        """
    )

    stage1_text, stage1_stats = apply_stage1_with_stats(
        source,
        repo_config,
        tokenizer,
        tok_type,
    )
    stage2_text = apply_stage2(
        stage1_text,
        profile="stage2_hybrid_ab_aggressive",
        mode="blockwise",
    )
    backend = get_stage3_backend("hybrid_ab")
    stage3_result = backend.encode(
        stage2_text,
        repo_config,
        tokenizer=tokenizer,
        tok_type=tok_type,
    )

    metrics = stage3_result.metrics
    return {
        "source": _strip(source),
        "annotated_source": _strip(
            dedent(
                """
                def hydrate_customer_identifier(customer_identifier_payload, customer_identifier_lookup, customer_identifier_cache):  # [S1] 命中 `def {0}({1}, {2}, {3}):`
                    customer_identifier_payload = customer_identifier_lookup.get(customer_identifier_payload, customer_identifier_payload)  # [S3-A] `customer_identifier_payload -> a`, `customer_identifier_lookup -> b`
                    customer_identifier_cache[customer_identifier_payload] = customer_identifier_payload  # [未压缩] `customer_identifier_cache` 只出现 2 次，低于 `a_min_occ=3`
                    customer_identifier_lookup[customer_identifier_payload] = customer_identifier_payload  # [S3-A] `customer_identifier_lookup -> b`
                    customer_identifier_payload = customer_identifier_payload.strip()  # [S3-A] `customer_identifier_payload -> a`
                    audit_event_label = "customer identifier payload mismatch"  # [未压缩] 这段字符串被路由成 `free_text`，`exact_only` 下不走 B 通道
                    failure_message = "customer identifier payload mismatch"  # [未压缩] 同上
                    fallback_message = "customer identifier payload mismatch"  # [未压缩] 同上
                    return customer_identifier_payload  # [S1] 命中 `return {0}`，随后 Stage3 再把变量压成 `a`
                """
            )
        ),
        "stage1_text": _strip(stage1_text),
        "stage2_text": _strip(stage2_text),
        "stage3_text": _strip(stage3_result.encoded_text),
        "counts": {
            "baseline": _count_tokens(source, tokenizer, tok_type),
            "stage1": _count_tokens(stage1_text, tokenizer, tok_type),
            "stage2": _count_tokens(stage2_text, tokenizer, tok_type),
            "stage3": _count_tokens(stage3_result.encoded_text, tokenizer, tok_type),
        },
        "stage1_markers": {
            "def4": _find_stage1_marker(stage1_stats, "def {0}({1}, {2}, {3}):"),
            "assign": _find_stage1_marker(stage1_stats, "{0} = {1}"),
            "return": _find_stage1_marker(stage1_stats, "return {0}"),
        },
        "stage1_stats": stage1_stats,
        "stage3_metrics": metrics,
    }


def _run_adapted_stage2_example(repo_config: RepoConfig, tokenizer, tok_type: str) -> dict:
    source = dedent(
        """\
        #!/usr/bin/env python
        # noqa: F401
        from customer_service import fetch_records
        from customer_service import format_row


        def _build_customer_map(customer_identifier, raw_records):
            \"\"\"private helper docstring for removable setup\"\"\"
            # remove this explanatory comment
            normalized_rows = {}
            for record_key, record_value in fetch_records(raw_records).items():
                if record_key in raw_records:
                    normalized_rows[customer_identifier] = format_row(record_value)
            return normalized_rows
        """
    )

    out = apply_stage1_stage2_adapted(
        source,
        repo_config,
        stage2_profile="aggressive_upper_bound",
        tokenizer=tokenizer,
        tok_type=tok_type,
        path="demo.py",
    )

    pre_stats = asdict(out["stage2_pre_stats"])
    post_stats = asdict(out["stage2_post_stats"])

    return {
        "source": _strip(source),
        "annotated_source": _strip(
            dedent(
                """
                #!/usr/bin/env python                     # [保留] shebang，R01 明确保留
                # noqa: F401                              # [保留] directive comment，R01 明确保留
                from customer_service import fetch_records
                from customer_service import format_row

                def _build_customer_map(customer_identifier, raw_records):  # [S1] 命中 `def {0}({1}, {2}):`
                    \"\"\"private helper docstring for removable setup\"\"\"      # [S2-R05] safe_only 删除；原因=`low_risk_private_docstring_eligible_for_removal`
                    # remove this explanatory comment                        # [S2-R01] 普通注释，删除
                    normalized_rows = {}                                     # [S2-R04] aggressive post-pass 去缩进
                    for record_key, record_value in fetch_records(raw_records).items():  # [S1] 命中 `for {0}, {1} in {2}({3}).items():`
                        if record_key in raw_records:                        # [S1] 命中 `if {0} in {1}:`
                            normalized_rows[customer_identifier] = format_row(record_value)
                    return normalized_rows                                   # [S1] 命中 `return {0}`
                """
            )
        ),
        "stage2_pre_text": _strip(out["stage2_pre_text"]),
        "stage1_text": _strip(out["stage1_text"]),
        "stage2_post_text": _strip(out["stage2_post_text"]),
        "pre_stats": pre_stats,
        "post_stats": post_stats,
    }


def _recommendation_section(best_exact: dict[str, str], best_hybrid: dict[str, str]) -> list[str]:
    exact_eff = _float(best_exact, "effective_total_reduction_pct")
    hybrid_eff = _float(best_hybrid, "effective_total_reduction_pct")
    exact_tokens = _int(best_exact, "sum_effective_total_tokens")
    hybrid_tokens = _int(best_hybrid, "sum_effective_total_tokens")
    delta_pp = hybrid_eff - exact_eff
    delta_tokens = exact_tokens - hybrid_tokens
    b_saved = _int(best_hybrid, "sum_stage3_ab_b_sequence_saved")
    b_intro = _int(best_hybrid, "sum_stage3_ab_b_intro_tokens")

    return [
        "## 2. 结论先说",
        "",
        f"- **纯数字最优**: `gpt4_hybrid_ab_hybrid_aggressive_s12`，有效总压缩率 `{hybrid_eff:.6f}%`。",
        f"- **推荐默认主线**: `gpt4_hybrid_ab_exact_only_aggressive_s12`，有效总压缩率 `{exact_eff:.6f}%`。",
        f"- 这两个配置的差距只有 `{delta_pp:.6f} pp`，折算成这轮 80-sample 评测只有 **{delta_tokens} tokens** 的有效总差距。",
        f"- `hybrid` 的 B 通道本轮只额外拿到 `{b_saved}` 个 sequence saving，同时引入 `{b_intro}` 个 vocab intro；净收益太小，不足以支撑默认复杂度。",
        "",
        "所以本报告的工程建议保持不变：",
        "",
        "`Stage1 + Stage2(stage2_hybrid_ab_aggressive / blockwise) + Stage3(hybrid_ab exact_only)`",
        "",
        "如果你后面只追求 leaderboard 数字，可以把 `hybrid` 作为附加实验分支；如果你要一条稳定、可解释、便于继续改造的默认线，继续用 `exact_only` 更合理。",
        "",
    ]


def main() -> None:
    ablation_rows = _read_ablation_rows()
    gpt4_rows = [row for row in ablation_rows if row["tokenizer_key"] == "gpt4"]
    exact_row = next(row for row in gpt4_rows if row["label"] == "gpt4_hybrid_ab_exact_only_aggressive_s12")
    hybrid_row = next(row for row in gpt4_rows if row["label"] == "gpt4_hybrid_ab_hybrid_aggressive_s12")
    legacy_row = next(row for row in gpt4_rows if row["label"] == "gpt4_hybrid_ab_exact_only_legacy_s12")

    repo_config = _load_current_repo_config()
    tokenizer, tok_type = _load_gpt4_tokenizer()

    mainline_example = _run_mainline_example(repo_config, tokenizer, tok_type)
    adapted_example = _run_adapted_stage2_example(repo_config, tokenizer, tok_type)

    artifact = {
        "ablation_rows": gpt4_rows,
        "mainline_example": mainline_example,
        "adapted_stage2_example": adapted_example,
    }
    ARTIFACT_JSON.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_lines: list[str] = [
        "# 最佳压缩方案复测报告（2026-04-17）",
        "",
        "- 仓库：`entropy_tokenizer_v2`",
        "- 本次复测命令：`python scripts/run_hybrid_ab_s12_ablation.py`",
        "- 结论使用的 tokenizer：`gpt4`",
        "- 本次用于代码级讲解的样例：本地可复现，结果已同步写入 `results/best_compression_remeasure_samples_2026-04-17.json`",
        "",
        "## 1. 这次重新测了什么",
        "",
        "这次我把你前面已经锁定的主线重新测了一遍，并把三个最关键的配置重新对齐：",
        "",
        "1. `gpt4_hybrid_ab_exact_only_legacy_s12`",
        "2. `gpt4_hybrid_ab_exact_only_aggressive_s12`",
        "3. `gpt4_hybrid_ab_hybrid_aggressive_s12`",
        "",
        "这里的含义分别是：",
        "",
        "- `legacy_s12`：旧的 `stage2_aggressive / linewise`",
        "- `aggressive_s12`：`hybrid_ab` 自己的默认 Stage2，等价于 `stage2_hybrid_ab_aggressive / blockwise`",
        "- `exact_only`：Stage3 只开 A 通道（exact alias）",
        "- `hybrid`：Stage3 同时开 A/B 通道",
        "",
        _format_table(
            ["配置", "Stage2", "Stage3", "有效总压缩率", "Sequence 压缩率", "Stage1%", "Stage2%", "Stage3%"],
            [
                [
                    "`legacy_s12 + exact_only`",
                    "`stage2_aggressive / linewise`",
                    "`A only`",
                    f"{_float(legacy_row, 'effective_total_reduction_pct'):.6f}%",
                    f"{_float(legacy_row, 'sequence_reduction_pct'):.6f}%",
                    f"{_float(legacy_row, 'syntax_pct'):.6f}%",
                    f"{_float(legacy_row, 'cleaning_pct'):.6f}%",
                    f"{_float(legacy_row, 'replacement_pct'):.6f}%",
                ],
                [
                    "`aggressive_s12 + exact_only`",
                    "`stage2_hybrid_ab_aggressive / blockwise`",
                    "`A only`",
                    f"{_float(exact_row, 'effective_total_reduction_pct'):.6f}%",
                    f"{_float(exact_row, 'sequence_reduction_pct'):.6f}%",
                    f"{_float(exact_row, 'syntax_pct'):.6f}%",
                    f"{_float(exact_row, 'cleaning_pct'):.6f}%",
                    f"{_float(exact_row, 'replacement_pct'):.6f}%",
                ],
                [
                    "`aggressive_s12 + hybrid`",
                    "`stage2_hybrid_ab_aggressive / blockwise`",
                    "`A + B`",
                    f"{_float(hybrid_row, 'effective_total_reduction_pct'):.6f}%",
                    f"{_float(hybrid_row, 'sequence_reduction_pct'):.6f}%",
                    f"{_float(hybrid_row, 'syntax_pct'):.6f}%",
                    f"{_float(hybrid_row, 'cleaning_pct'):.6f}%",
                    f"{_float(hybrid_row, 'replacement_pct'):.6f}%",
                ],
            ],
        ),
        "",
    ]

    report_lines.extend(_recommendation_section(exact_row, hybrid_row))

    report_lines.extend(
        [
            "## 3. 这条主线在代码里到底对应什么",
            "",
            "主入口是 `pipeline.apply_pipeline()`，顺序是：",
            "",
            "1. `syntax_compressor.compress_source_syntax()` 做 Stage1",
            "2. `stage2.cleaning.stage2_clean_skip_syn()` 做 Stage2",
            "3. `stage3.backends.hybrid_ab_backend.HybridABStage3Backend.encode()` 做 Stage3",
            "",
            "关键规则对应的代码位置：",
            "",
            "- Stage1 语法骨架：`syntax_compressor.py`",
            "- Stage2 清洗规则：`lossy_cleaner.py` + `stage2/config.py` + `stage2/cleaning.py`",
            "- Stage3 A/B 路由：`stage3/routing/router.py`",
            "- Stage3 exact alias：`stage3/exact/alias_codec.py`",
            "",
            "本次复测里真正起作用的主线参数是：",
            "",
            "- `stage3_backend = hybrid_ab`",
            "- `ET_STAGE3_AB_MODE = exact_only`",
            "- `STAGE2_HYBRID_AB_PROFILE = stage2_hybrid_ab_aggressive`",
            "- `STAGE2_HYBRID_AB_MODE = blockwise`",
            "- `a_min_occ = 3`（gpt4 路径）",
            "- `a_cost_mode = context_aware`",
            "- `enable_global_guardrail = true`",
            "- `enable_incremental_rollback = true`",
            "",
            "这轮 gpt4 主线里，Top-5 Stage1 骨架是：",
            "",
            _format_table(
                ["#", "骨架", "频次", "effective_total_net_saving"],
                _top_stage1_skeleton_rows(repo_config),
            ),
            "",
            "## 4. 样例 A：真实主线（Stage1 -> Stage2 -> Stage3 exact_only）怎么压",
            "",
            "### 4.1 带标注的原始代码",
            "",
            "```python",
            mainline_example["annotated_source"],
            "```",
            "",
            "### 4.2 各阶段输出",
            "",
            _format_table(
                ["阶段", "tokens"],
                [
                    ["原始代码", str(mainline_example["counts"]["baseline"])],
                    ["Stage1", str(mainline_example["counts"]["stage1"])],
                    ["Stage2", str(mainline_example["counts"]["stage2"])],
                    ["Stage3", str(mainline_example["counts"]["stage3"])],
                ],
            ),
            "",
            "#### Stage1 输出",
            "",
            "```text",
            mainline_example["stage1_text"],
            "```",
            "",
            "#### Stage2 输出",
            "",
            "```text",
            mainline_example["stage2_text"],
            "```",
            "",
            "#### Stage3 输出（最终压缩序列）",
            "",
            "```text",
            mainline_example["stage3_text"],
            "```",
            "",
            "### 4.3 这段代码里到底发生了什么",
            "",
            f"- Stage1 把函数签名压成了 `{mainline_example['stage1_markers']['def4']}`，对应骨架 `def {{0}}({{1}}, {{2}}, {{3}}):`。",
            f"- Stage1 还把三条 `name = value` 压成了 `{mainline_example['stage1_markers']['assign']}`，把 `return name` 压成了 `{mainline_example['stage1_markers']['return']}`。",
            "- Stage2 主要做了 `R02/R03/R04`：空行、尾随空白、缩进都被压掉，所以文本更像“线性 token 序列”，不再是可执行源码。",
            "- Stage3 exact alias 这次选中了 3 个 A-entry：",
            "",
            _format_table(
                ["literal", "alias", "count", "raw_cost", "alias_cost", "intro_cost", "gain"],
                [
                    [
                        f"`{entry['literal']}`",
                        f"`{entry['alias']}`",
                        str(entry["count"]),
                        str(entry["raw_cost"]),
                        str(entry["alias_cost"]),
                        str(entry["intro_cost"]),
                        str(entry["gain"]),
                    ]
                    for entry in mainline_example["stage3_metrics"]["stage3_ab_a_entries_json"]
                ],
            ),
            "",
            f"- 这段样例里，Stage3 单独把 token 从 `{mainline_example['counts']['stage2']}` 压到 `{mainline_example['counts']['stage3']}`，真实 `stage3_realized_delta = {mainline_example['stage3_metrics']['stage3_realized_delta']}`。",
            f"- `customer_identifier_cache` **没有**被压缩：按样例正文直接数只出现 2 次，低于 `a_min_occ=3`。",
            f"- 三个相同的报错字符串 **没有**被压缩：`stage3_ab_a_reject_reason_counts` 里有 `route_free_text = {mainline_example['stage3_metrics']['stage3_ab_a_reject_reason_counts'].get('route_free_text', 0)}`，说明它们被路由成 B 通道候选；而当前主线是 `exact_only`，所以这类 free-text 故意不压。",
            "",
            "## 5. 样例 B：把 Stage2 规则单独摊开看",
            "",
            "这里我不用主线顺序，而是用仓库现成的诊断路径 `apply_stage1_stage2_adapted()`：",
            "",
            "`stage2_pre_safe -> stage1 -> stage2_post_surface`",
            "",
            "这样做的原因很简单：主线是 `Stage1 -> Stage2`，一旦 Stage1 先把源码骨架化，后续 `safe_only docstring` 的 AST 语义就不够直观了；诊断路径更适合解释 `R01/R05`。",
            "",
            "### 5.1 带标注的原始代码",
            "",
            "```python",
            adapted_example["annotated_source"],
            "```",
            "",
            "### 5.2 诊断路径输出",
            "",
            "#### Stage2 pre-safe 输出",
            "",
            "```text",
            adapted_example["stage2_pre_text"],
            "```",
            "",
            "#### Stage1 输出",
            "",
            "```text",
            adapted_example["stage1_text"],
            "```",
            "",
            "#### Stage2 post-surface 输出",
            "",
            "```text",
            adapted_example["stage2_post_text"],
            "```",
            "",
            "### 5.3 这段样例说明了哪些规则",
            "",
            f"- `R05 docstring`：删掉了 {adapted_example['pre_stats']['removed_docstring_chars']} 个字符，`removed_count = {adapted_example['pre_stats']['docstring_removal_report']['removed_count']}`。",
            f"- 删除原因不是拍脑袋，而是 `safe_only` 给出的风险标签：`{adapted_example['pre_stats']['docstring_removal_report']['removed'][0]['risk_reasons'][0]}`。",
            "- `R01 comments`：普通注释 `# remove this explanatory comment` 被删除；但 shebang 和 `# noqa` 被保留。",
            f"- `R02/R03`：pre-safe 阶段一起去掉了 {adapted_example['pre_stats']['removed_blank_lines']} 个空行/空白布局。",
            f"- `R04 indentation`：post-surface 又去掉了 {adapted_example['post_stats']['removed_indent_chars']} 个缩进字符。",
            "",
            "## 6. 哪些东西当前主线**不会**压，为什么",
            "",
            "- 指令型注释不会删：`#!`、`coding:`、`noqa`、`pragma: no cover`、`mypy/pyright/pylint/fmt` 等都被 `lossy_cleaner.is_preserved_directive_comment()` 明确保留。",
            "- 多行自由文本不会进 A 通道：`stage3/routing/router.py` 里默认 `allow_multiline_whitelist = false`，所以这类字符串会得到 `route_multiline_disabled`。",
            "- free-text 句子在 `exact_only` 下不会压：它们会被路由成 B 候选，但 B 通道被关掉，因此宁可不压，也不引入额外复杂度。",
            "- 低频名字不会压：gpt4 这条线的 `a_min_occ = 3`，少于 3 次直接淘汰。",
            "- 净收益不为正的候选不会压：即便频次够，如果 `context_aware` 算下来 introduction cost 吃掉了收益，也会进 `net_gain_reject`。",
            "- 保护名不会压：`self`、关键字、AST 保护名、作用域冲突名都不会被 exact alias 改写。",
            "",
            "## 7. 详细结论",
            "",
            "1. **最关键的杠杆仍然是 Stage2 aggressive/blockwise。**",
            f"   这轮复测里，`legacy_s12 + exact_only` 到 `aggressive_s12 + exact_only`，有效总压缩率从 `{_float(legacy_row, 'effective_total_reduction_pct'):.6f}%` 直接抬到 `{_float(exact_row, 'effective_total_reduction_pct'):.6f}%`，提升了 `{_float(exact_row, 'effective_total_reduction_pct') - _float(legacy_row, 'effective_total_reduction_pct'):.6f} pp`。",
            "",
            "2. **Stage3 A 通道是值得保留的，但 B 通道目前只值一个备选分支。**",
            f"   `exact_only` 到 `hybrid` 只多了 `{_float(hybrid_row, 'effective_total_reduction_pct') - _float(exact_row, 'effective_total_reduction_pct'):.6f} pp`，而 B 通道本轮只额外省了 `{_int(hybrid_row, 'sum_stage3_ab_b_sequence_saved')}` 个 sequence tokens。",
            "",
            "3. **当前主线的可解释性比以前好很多。**",
            "   现在几乎每一种“不压”的情况都能落到具体规则上：directive comment、multiline string、free-text routed to B、min_occ 不达标、context-aware 净收益不够、protected name 等。",
            "",
            "4. **但还有一个结构性问题值得单独盯。**",
            "   主线是 `Stage1 -> Stage2`，所以 `safe_only docstring` 这类 AST 依赖规则，在主线上不如诊断路径里那么干净。换句话说：",
            "",
            "   - 如果你的目标是“端到端 token 最优”，当前主线没问题；",
            "   - 如果你的目标是“把每条 Stage2 规则都稳定、透明地打在 parseable 源码上”，那就应该把 `docstring/comment` 预处理前移，或者继续沿用 `apply_stage1_stage2_adapted()` 这条诊断链路做验证。",
            "",
            "5. **因此，下一阶段最值得做的不是继续发明 B 规则，而是把主线和诊断链路对齐。**",
            "   更具体地说，就是：",
            "",
            "   - 主线继续用 `exact_only + aggressive/blockwise`；",
            "   - 诊断链路继续用 `pre_safe -> stage1 -> post_surface` 去看 `R01/R05`；",
            "   - 后面如果要重新挑战 prompt 端净收益，再把 wrapper / vocab intro 一起拉回去核算。",
            "",
        ]
    )

    REPORT_MD.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {ARTIFACT_JSON}")


if __name__ == "__main__":
    main()
