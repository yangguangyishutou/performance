"""
Human-readable case ledger + optional JSONL stream of ``TelemetryEvent`` rows.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator, Literal

from rewrite_stage3ab.contracts.data_models import TelemetryEvent


@dataclass
class LedgerEntry:
    kind: Literal["a_rewrite", "b_cluster", "reject", "routing"]
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

    def append_routing(
        self,
        source_id: str,
        before: str,
        after: str,
        *,
        reason: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._rows.append(
            LedgerEntry(
                kind="routing",
                source_id=source_id,
                before_snippet=before,
                after_snippet=after,
                reason=reason,
                payload=payload or {},
            )
        )

    def __len__(self) -> int:
        return len(self._rows)

    def entries(self) -> list[LedgerEntry]:
        return list(self._rows)

    def iter_jsonl_dicts(self) -> Iterator[dict[str, Any]]:
        for e in self._rows:
            yield {**asdict(e)}


class JsonlTelemetryLedger:
    """Append-only JSONL of structured ``TelemetryEvent`` rows."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: TelemetryEvent) -> None:
        row = asdict(event)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def extend(self, events: list[TelemetryEvent]) -> None:
        for e in events:
            self.append(e)
