"""
只比 Stage-1（句法层）：同一批源码、同一套样本过滤规则。

- v2: 挖掘得到的 <SYN_i> 在计数时按 1 个 token（与全链路 marker_count 规则中仅处理 SYN 子集一致）。
- SimPy: transformer 输出后，使用扩展词表中的 SPECIAL_TOKENS 计数（与 simpy_eval_1m_tokens 一致）。

不做 Stage2/3；baseline 均为「原始源码 + 对应 tokenizer 的普通 encode」。

额外诊断：每文件平均节省 token、仅「含 >=1 <SYN_*>」子集上的平均节省、被替换 header 原文
在 baseline 中的 token 占比（语料级）、v2 覆盖率、SimPy 单文件 token 下降占比。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import bootstrap_v2

bootstrap_v2.ensure_with_simpy()

CODE_DIR = bootstrap_v2.CODE_DIR

import tiktoken
from transformers import AutoTokenizer

from config import EVAL_TOKENIZERS, HF_TOKEN
from marker_count import RE_SYN_ONLY, count_augmented, encode
from repo_miner import mine_from_sources, _load_tokenizer
from syntax_compressor import compress_source_syntax, sum_replaced_header_tokens
try:
    from spy import Transformer, SPECIAL_TOKENS
except Exception:  # pragma: no cover
    Transformer = None  # type: ignore
    SPECIAL_TOKENS = []  # type: ignore


def load_samples(sample_file: Path) -> list[str]:
    text = sample_file.read_text(encoding="utf-8", errors="replace")
    parts = re.split(r"<\|sample_\d+\|>\n", text)
    return [s for s in parts if s.strip()]


def normalize_code(code: str) -> str | None:
    lines = code.splitlines()
    if lines and lines[0].startswith("<"):
        code = "\n".join(lines[1:])
    if code.startswith("#!/"):
        return None
    return code


def build_gpt4_simpy_enc():
    if not SPECIAL_TOKENS:
        raise RuntimeError("SPECIAL_TOKENS unavailable (SimPy import failed)")
    base_enc = tiktoken.encoding_for_model("gpt-4")
    enc = tiktoken.Encoding(
        name="gpt4-spy-stage1",
        pat_str=base_enc._pat_str,
        mergeable_ranks=base_enc._mergeable_ranks,
        special_tokens={
            **base_enc._special_tokens,
            **{v: i + 100264 for i, v in enumerate(SPECIAL_TOKENS)},
        },
    )
    allowed_all = set(enc._special_tokens.keys())
    return enc, allowed_all


@dataclass
class V2Stage1Diag:
    n_files: int
    k_star: int
    baseline_tokens: int
    after_tokens: int
    reduction_pct: float
    """至少出现一次 <SYN_n> 的样本数"""
    files_with_any_syn: int
    """所有输出里 <SYN_n> 出现次数之和（可 > n_files）"""
    total_syn_markers: int
    avg_saved_tokens_per_file: float
    """仅统计至少出现一次 <SYN_n> 的文件上的 (baseline−after) 平均"""
    avg_saved_if_file_has_syn: float
    avg_syn_markers_per_file: float
    pct_files_with_syn: float
    """所有被替换 header 原文的 token 数之和（与 compress 站点一致）"""
    corpus_header_tokens_in_replacements: int
    """语料级：被替换 header token / 全语料 baseline token ×100"""
    pct_replaced_header_tokens_of_baseline: float


@dataclass
class SimPyStage1Diag:
    parse_ok: int
    parse_fail: int
    baseline_tokens: int
    after_tokens: int
    reduction_pct: float
    """parse 成功且该文件 after < baseline 的样本数"""
    files_with_token_drop: int
    avg_saved_tokens_per_ok_file: float
    pct_ok_files_with_drop: float


def eval_v2_stage1(samples: list[str], tok_key: str, cfg: dict, cache_name: str) -> V2Stage1Diag:
    repo = mine_from_sources(
        sources=samples,
        tokenizer_key=tok_key,
        tokenizer_cfg=cfg,
        cache_name=cache_name,
        cache=True,
        verbose=False,
    )
    skels = repo.skeleton_candidates()
    tok, tt = _load_tokenizer(tok_key, cfg)
    baseline = after = 0
    files_with_syn = 0
    total_syn_markers = 0
    sum_header_tok = 0
    saved_sum_if_syn = 0.0
    n = 0
    for raw in samples:
        c = normalize_code(raw)
        if c is None:
            continue
        b = len(encode(tok, tt, c))
        ht, _ = sum_replaced_header_tokens(c, skels, tok, tt)
        sum_header_tok += ht
        out = compress_source_syntax(c, skels)
        a = count_augmented(out, tok, tt, pattern=RE_SYN_ONLY)
        syn_hits = RE_SYN_ONLY.findall(out)
        if syn_hits:
            files_with_syn += 1
            total_syn_markers += len(syn_hits)
            saved_sum_if_syn += float(b - a)
        baseline += b
        after += a
        n += 1
    pct = (1.0 - after / baseline) * 100.0 if baseline else 0.0
    saved = baseline - after
    pct_hdr = 100.0 * sum_header_tok / baseline if baseline else 0.0
    return V2Stage1Diag(
        n_files=n,
        k_star=len(skels),
        baseline_tokens=baseline,
        after_tokens=after,
        reduction_pct=pct,
        files_with_any_syn=files_with_syn,
        total_syn_markers=total_syn_markers,
        avg_saved_tokens_per_file=saved / n if n else 0.0,
        avg_saved_if_file_has_syn=saved_sum_if_syn / files_with_syn if files_with_syn else 0.0,
        avg_syn_markers_per_file=total_syn_markers / n if n else 0.0,
        pct_files_with_syn=100.0 * files_with_syn / n if n else 0.0,
        corpus_header_tokens_in_replacements=sum_header_tok,
        pct_replaced_header_tokens_of_baseline=pct_hdr,
    )


def eval_simpy_stage1(samples: list[str], tok_key: str, meta: dict, transformer) -> SimPyStage1Diag:

    if meta["type"] == "tiktoken":
        enc = meta["enc"]
        allowed_all = meta["allowed_all"]

        def n_raw(t: str) -> int:
            return len(enc.encode(t, allowed_special=allowed_all))

        def n_spy(t: str) -> int:
            return len(enc.encode(t, allowed_special=set(enc._special_tokens.keys())))
    else:
        tok = AutoTokenizer.from_pretrained(
            meta["model_name"], trust_remote_code=True, token=HF_TOKEN
        )
        tok.add_special_tokens({"additional_special_tokens": transformer.special_tokens})

        def n_raw(t: str) -> int:
            return len(tok.encode(t))

        def n_spy(t: str) -> int:
            return len(tok.encode(t))

    baseline = spy_tokens = 0
    ok = fail = 0
    files_with_drop = 0
    per_file_saved_sum = 0
    for raw in samples:
        c = normalize_code(raw)
        if c is None:
            continue
        br = n_raw(c)
        baseline += br
        try:
            spy_code = transformer.parse(c)
        except Exception:
            fail += 1
            continue
        ok += 1
        ar = n_spy(spy_code)
        spy_tokens += ar
        delta = br - ar
        per_file_saved_sum += delta
        if ar < br:
            files_with_drop += 1

    pct = (1.0 - spy_tokens / baseline) * 100.0 if baseline else 0.0
    return SimPyStage1Diag(
        parse_ok=ok,
        parse_fail=fail,
        baseline_tokens=baseline,
        after_tokens=spy_tokens,
        reduction_pct=pct,
        files_with_token_drop=files_with_drop,
        avg_saved_tokens_per_ok_file=per_file_saved_sum / ok if ok else 0.0,
        pct_ok_files_with_drop=100.0 * files_with_drop / ok if ok else 0.0,
    )


def main():
    sample_path = CODE_DIR / "data" / "starcoder_1m_tokens.txt"
    if not sample_path.exists():
        raise FileNotFoundError(sample_path)

    samples = load_samples(sample_path)
    print("Loaded samples:", len(samples))

    simpy_transformer = None
    simpy_err = None
    if Transformer is not None:
        try:
            simpy_transformer = Transformer(ignore_error=True)
        except Exception as e:
            simpy_err = e
            print("\n[warn] SimPy Transformer 不可用（常见原因: tree-sitter 版本/C 扩展），将只输出 v2 Stage1:", e)

    simpy_meta = {}
    if simpy_transformer is not None:
        gpt_enc, gpt_allowed = build_gpt4_simpy_enc()
        simpy_meta = {
            "gpt4": {"type": "tiktoken", "enc": gpt_enc, "allowed_all": gpt_allowed},
            "codegen-350M-mono": {"type": "hf", "model_name": "Salesforce/codegen-350M-mono"},
            "santacoder": {"type": "hf", "model_name": "bigcode/santacoder"},
        }

    print("\n" + "=" * 88)
    print("  Stage-1 ONLY  |  v2 (<SYN_*>)  vs  SimPy  |  same filters as simpy_eval_1m_tokens.py")
    print("=" * 88)

    for tok_key in ("gpt4", "codegen-350M-mono", "santacoder"):
        cfg = EVAL_TOKENIZERS[tok_key]
        cache_name = f"starcoderdata_1m_{tok_key}"
        v2 = eval_v2_stage1(samples, tok_key, cfg, cache_name)
        print(f"\n  [{tok_key}]")
        print(
            f"    v2   : n={v2.n_files}  K*={v2.k_star}  baseline={v2.baseline_tokens:,}  "
            f"after_s1={v2.after_tokens:,}  reduction={v2.reduction_pct:.3f}%"
        )
        print(
            f"           avg_saved/file={v2.avg_saved_tokens_per_file:+.2f}  "
            f"avg_saved_if_has_syn={v2.avg_saved_if_file_has_syn:+.2f}  "
            f"syn_hits_total={v2.total_syn_markers}  avg_syn/file={v2.avg_syn_markers_per_file:.2f}  "
            f"coverage={v2.pct_files_with_syn:.1f}% files have >=1 <SYN_*"
        )
        print(
            f"           header_tok_in_sites={v2.corpus_header_tokens_in_replacements:,}  "
            f"= {v2.pct_replaced_header_tokens_of_baseline:.2f}% of corpus baseline "
            f"(replaced-header text token mass)"
        )
        if simpy_transformer is not None and tok_key in simpy_meta:
            sp = eval_simpy_stage1(
                samples, tok_key, simpy_meta[tok_key], simpy_transformer
            )
            print(
                f"    SimPy: ok={sp.parse_ok}  fail={sp.parse_fail}  "
                f"baseline={sp.baseline_tokens:,}  after={sp.after_tokens:,}  "
                f"reduction={sp.reduction_pct:.3f}%"
            )
            print(
                f"           avg_saved/ok_file={sp.avg_saved_tokens_per_ok_file:+.2f}  "
                f"{sp.pct_ok_files_with_drop:.1f}% ok files strictly drop tokens"
            )
        else:
            msg = "SimPy 未运行"
            if simpy_err:
                msg += f" ({simpy_err})"
            print(f"    {msg}")
    print("\n" + "=" * 88)


if __name__ == "__main__":
    main()
