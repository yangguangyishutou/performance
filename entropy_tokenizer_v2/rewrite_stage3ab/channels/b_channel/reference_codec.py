"""
Reference-style compression protocol for small clusters (skeleton only).

Steps (future):
1. **representative selection** — pick centroid string / lowest-risk span.
2. **reference symbol emission** — mint stable marker + side table entry.
3. **intro cost accounting** — true tokens for table row.
4. **replacement rewrite** — substitute occurrences with reference token.

TODO: Integrate with ``metrics.accounting`` and B ``intro_tokens_true``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class ReferenceEmission:
    symbol: str
    representative: str
    member_spans: list[tuple[int, int]]
    intro_tokens_true: int = 0


@runtime_checkable
class ReferenceCodec(Protocol):
    def select_representative(self, members: list[str], ctx: dict[str, Any]) -> str:
        ...

    def emit(self, representative: str, ctx: dict[str, Any]) -> ReferenceEmission:
        ...

    def rewrite_text(self, text: str, emission: ReferenceEmission, ctx: dict[str, Any]) -> str:
        ...


class StubReferenceCodec:
    def select_representative(self, members: list[str], ctx: dict[str, Any]) -> str:
        del ctx
        return members[0] if members else ""

    def emit(self, representative: str, ctx: dict[str, Any]) -> ReferenceEmission:
        del ctx
        return ReferenceEmission(symbol="§stub", representative=representative, member_spans=[])

    def rewrite_text(self, text: str, emission: ReferenceEmission, ctx: dict[str, Any]) -> str:
        del emission, ctx
        return text
