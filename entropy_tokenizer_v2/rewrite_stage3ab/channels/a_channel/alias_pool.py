"""
Alias pool abstraction: legal ids, tokenizer-friendly picks, scope safety.

Three layers (all stubbed):
1. Legal identifier pool provider (language / style rules).
2. Single-token preferred alias provider (tiktoken/HF aware).
3. Scope-aware conflict checker (AST-backed later).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LegalIdentifierPool(Protocol):
    def iter_legal_names(self, max_n: int) -> list[str]:
        ...


@runtime_checkable
class SingleTokenAliasProvider(Protocol):
    def prefer_single_token(self, base: str, tokenizer_key: str) -> str:
        """Pick a surface form that tends to encode short under *tokenizer_key*."""
        ...


@runtime_checkable
class ScopeConflictChecker(Protocol):
    def is_safe(self, name: str, scope_id: str, ctx: dict[str, Any]) -> bool:
        ...


class StubLegalIdentifierPool:
    def iter_legal_names(self, max_n: int) -> list[str]:
        return [f"x{i}" for i in range(min(max_n, 8))]


class StubSingleTokenAliasProvider:
    def prefer_single_token(self, base: str, tokenizer_key: str) -> str:
        del tokenizer_key
        return base[:1] or "_"


class StubScopeConflictChecker:
    def is_safe(self, name: str, scope_id: str, ctx: dict[str, Any]) -> bool:
        del scope_id, ctx
        return bool(name)
