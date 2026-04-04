"""
Core data contracts for the rewrite framework.

Naming:
- ``*_true`` / ``token_count_true``: raw tokenizer id length (primary truth source).
- ``*_augmented`` / ``token_count_augmented``: placeholder-aware auxiliary accounting
  (must never be silently treated as interchangeable with ``*_true``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class SourceUnit:
    """One compressible source (file, cell, or chunk)."""

    source_id: str
    raw_text: str
    tokenizer_key: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StageSnapshot:
    """Immutable-style snapshot after a named stage."""

    stage_name: str
    text: str
    token_count_true: int
    token_count_augmented: int | None = None
    notes: str = ""


@dataclass
class AChannelResult:
    """Outcome of exact-aliasing / token-economics channel (A)."""

    selected_candidates: list[dict[str, Any]] = field(default_factory=list)
    rejected_candidates_by_reason: dict[str, int] = field(default_factory=dict)
    intro_tokens_true: int = 0
    saved_tokens_true: int = 0
    net_saved_true: int = 0
    alias_assignments: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BChannelResult:
    """Outcome of lexical / clustering / reference channel (B)."""

    visible_candidates: int = 0
    clusters_formed: int = 0
    clusters_selected: int = 0
    rejected_clusters_by_reason: dict[str, int] = field(default_factory=dict)
    intro_tokens_true: int = 0
    saved_tokens_true: int = 0
    net_saved_true: int = 0
    references_or_templates: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TelemetryEvent:
    """Single structured telemetry row (corpus- or file-scoped)."""

    event_type: str
    stage: str
    input_tokens_true: int
    output_tokens_true: int
    delta_true: int
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Stage3ABRunSummary:
    """Aggregated counters for one run (extensible)."""

    total_input_tokens_true: int = 0
    total_output_tokens_true: int = 0
    a_net_saved_true: int = 0
    b_net_saved_true: int = 0
    n_events: int = 0
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Stage3ABRunResult:
    """Full Stage3 AB chain result for one ``SourceUnit``."""

    source_id: str
    input_snapshot: StageSnapshot
    after_a_snapshot: StageSnapshot
    after_b_snapshot: StageSnapshot
    final_snapshot: StageSnapshot
    a_result: AChannelResult
    b_result: BChannelResult
    telemetry_events: list[TelemetryEvent] = field(default_factory=list)
    summary: Stage3ABRunSummary | None = None
