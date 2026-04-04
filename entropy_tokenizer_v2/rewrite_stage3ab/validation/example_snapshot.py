"""Build ``StageSnapshot`` with true (and optional augmented) token counts."""

from __future__ import annotations

from rewrite_stage3ab.contracts.data_models import StageSnapshot
from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len


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
