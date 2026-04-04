"""Build ``StageSnapshot`` with true (and optional augmented) token counts + example export."""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.contracts.data_models import StageSnapshot
from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len
from rewrite_stage3ab.telemetry.ledger import LedgerEntry


def snapshot_from_text(
    stage_name: str,
    text: str,
    tokenizer_key: str,
    *,
    notes: str = "",
    include_augmented: bool = False,
) -> StageSnapshot:
    true_len = measure_true_token_len(text, tokenizer_key)
    aug = None
    if include_augmented:
        from rewrite_stage3ab.adapters.legacy_tokenizer_adapter import get_tokenizer_for_key
        from marker_count import count_augmented

        tok, typ = get_tokenizer_for_key(tokenizer_key)
        aug = count_augmented(text, tok, typ)
    return StageSnapshot(
        stage_name=stage_name,
        text=text,
        token_count_true=true_len,
        token_count_augmented=aug,
        notes=notes,
    )


def write_example_markdown(entries: list[LedgerEntry], path: Path | str) -> None:
    """Persist human-readable before/after snippets for reporting."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Rewrite Stage3 AB example ledger\n"]
    for i, e in enumerate(entries):
        lines.append(f"## {i + 1}. {e.kind} — `{e.source_id}`\n")
        if e.reason:
            lines.append(f"- reason: {e.reason}\n")
        lines.append("### before\n")
        lines.append("```text\n")
        lines.append((e.before_snippet or "(empty)") + "\n")
        lines.append("```\n")
        lines.append("### after\n")
        lines.append("```text\n")
        lines.append((e.after_snippet or "(empty)") + "\n")
        lines.append("```\n")
        if e.payload:
            lines.append(f"- payload: `{e.payload}`\n")
    p.write_text("".join(lines), encoding="utf-8")
