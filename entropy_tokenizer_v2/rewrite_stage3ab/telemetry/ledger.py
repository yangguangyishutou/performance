"""
Human-readable case ledger (before/after snippets, reject reasons).

Not wired to production logging this round — smoke tests append dummy rows only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class LedgerEntry:
    kind: Literal["a_rewrite", "b_cluster", "reject"]
    source_id: str
    before_snippet: str
    after_snippet: str
    reason: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


class ExampleLedger:
    def __init__(self) -> None:
        self._rows: list[LedgerEntry] = []

    def append_a_rewrite(
        self,
        source_id: str,
        before: str,
        after: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._rows.append(
            LedgerEntry(
                kind="a_rewrite",
                source_id=source_id,
                before_snippet=before,
                after_snippet=after,
                payload=payload or {},
            )
        )

    def append_b_cluster(
        self,
        source_id: str,
        before: str,
        after: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._rows.append(
            LedgerEntry(
                kind="b_cluster",
                source_id=source_id,
                before_snippet=before,
                after_snippet=after,
                payload=payload or {},
            )
        )

    def append_reject(self, source_id: str, reason: str, *, payload: dict[str, Any] | None = None) -> None:
        self._rows.append(
            LedgerEntry(
                kind="reject",
                source_id=source_id,
                before_snippet="",
                after_snippet="",
                reason=reason,
                payload=payload or {},
            )
        )

    def __len__(self) -> int:
        return len(self._rows)

    def entries(self) -> list[LedgerEntry]:
        return list(self._rows)
