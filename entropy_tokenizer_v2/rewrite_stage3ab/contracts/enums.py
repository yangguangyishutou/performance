"""Enumerations for stages, routing, telemetry, and future B backends."""

from __future__ import annotations

from enum import Enum, auto


class StageName(str, Enum):
    """Logical pipeline stage labels (extensible for AST-level sub-stages)."""

    RAW = "raw"
    STAGE1_SYNTAX = "stage1_syntax"
    STAGE2_CLEAN = "stage2_clean"
    STAGE3_PRE_AB = "stage3_pre_ab"
    STAGE3_AFTER_A = "stage3_after_a"
    STAGE3_AFTER_B = "stage3_after_b"
    STAGE3_FINAL = "stage3_final"


class RouteAction(str, Enum):
    """Future Stage2 → Stage3 resource routing (stub only this round)."""

    DELETE_NOW = "delete_now"
    RETAIN_FOR_B = "retain_for_b"
    RETAIN_AS_DOCSTRING_ASSET = "retain_as_docstring_asset"
    RETAIN_AS_COMMENT_ASSET = "retain_as_comment_asset"
    PASS_THROUGH = "pass_through"


class TelemetryEventKind(str, Enum):
    """High-level telemetry categories (expand for AST / economics / cluster)."""

    STAGE_BOUNDARY = "stage_boundary"
    CANDIDATE_COLLECTED = "candidate_collected"
    CANDIDATE_REJECTED = "candidate_rejected"
    CLUSTER_FORMED = "cluster_formed"
    CLUSTER_REJECTED = "cluster_rejected"
    ALIAS_APPLIED = "alias_applied"
    REFERENCE_EMITTED = "reference_emitted"
    ROUTING_DECISION = "routing_decision"


class ClusterBackendId(str, Enum):
    """Registered B-channel clustering backends (implementations are future work)."""

    LEXICAL_BASELINE = "lexical_baseline"
    MIXED_LEXICAL_CHAR = "mixed_lexical_char"
    HDBSCAN_FUTURE = "hdbscan_future"
