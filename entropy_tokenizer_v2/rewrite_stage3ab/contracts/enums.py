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
    """Stage2 → Stage3 resource routing (DAG edges materialized as per-asset actions)."""

    DELETE_NOW = "delete_now"
    RETAIN_FOR_B = "retain_for_b"
    RETAIN_AS_REFERENCE_CANDIDATE = "retain_as_reference_candidate"
    PASS_THROUGH = "pass_through"
    CLEAN_AFTER_B = "clean_after_b"
    # Legacy granular labels (still used in metadata.asset_kind)
    RETAIN_AS_DOCSTRING_ASSET = "retain_as_docstring_asset"
    RETAIN_AS_COMMENT_ASSET = "retain_as_comment_asset"


class TelemetryEventKind(str, Enum):
    """Telemetry categories for economics, AST, routing, and clusters."""

    STAGE_BOUNDARY = "stage_boundary"
    A_CANDIDATE_COLLECTED = "a_candidate_collected"
    A_CANDIDATE_REJECTED = "a_candidate_rejected"
    A_CANDIDATE_ACCEPTED = "a_candidate_accepted"
    A_ALIAS_APPLIED = "a_alias_applied"
    B_ASSET_COLLECTED = "b_asset_collected"
    B_CLUSTER_FORMED = "b_cluster_formed"
    B_CLUSTER_REJECTED = "b_cluster_rejected"
    B_CLUSTER_ACCEPTED = "b_cluster_accepted"
    B_REFERENCE_EMITTED = "b_reference_emitted"
    ROUTE_DECISION_MADE = "route_decision_made"
    DOCSTRING_DETECTED = "docstring_detected"
    COMMENT_DETECTED = "comment_detected"
    FINAL_STAGE_DELTA = "final_stage_delta"
    # Back-compat aliases
    CANDIDATE_COLLECTED = "a_candidate_collected"
    CANDIDATE_REJECTED = "a_candidate_rejected"
    CLUSTER_FORMED = "b_cluster_formed"
    CLUSTER_REJECTED = "b_cluster_rejected"
    ALIAS_APPLIED = "a_alias_applied"
    REFERENCE_EMITTED = "b_reference_emitted"
    ROUTING_DECISION = "route_decision_made"


class ClusterBackendId(str, Enum):
    """B-channel clustering backends."""

    LEXICAL_BASELINE = "lexical_baseline"
    MIXED_LEXICAL_CHAR = "mixed_lexical_char"
    HDBSCAN = "hdbscan"
    HDBSCAN_FUTURE = "hdbscan_future"
