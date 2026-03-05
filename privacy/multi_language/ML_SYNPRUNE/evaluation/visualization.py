#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import ast
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
from sklearn.metrics import f1_score, roc_auc_score
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

def load_jsonl_dataset(path: str) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f]

def extract_variable_names(code: str) -> Dict[str, List[Tuple[int, int]]]:
    try:
        tree = ast.parse(code)
        variable_info: Dict[str, List[Tuple[int, int]]] = {}
        lines = code.split('\n')
        def push(name: str, abs_start: int, abs_end: int):
            variable_info[name] = variable_info.get(name, []) + [(abs_start, abs_end)]
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                var_name = node.id
                if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
                    if 0 <= node.lineno - 1 < len(lines):
                        start_pos = node.col_offset
                        abs_start = sum(len(lines[i]) + 1 for i in range(node.lineno - 1)) + start_pos
                        abs_end = abs_start + len(var_name)
                        push(var_name, abs_start, abs_end)
            elif isinstance(node, ast.FunctionDef):
                var_name = node.name
                if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
                    if 0 <= node.lineno - 1 < len(lines):
                        line = lines[node.lineno - 1]
                        start_pos = line.find("def ", 0, node.col_offset) + 4
                        if start_pos >= 4:
                            abs_start = sum(len(lines[i]) + 1 for i in range(node.lineno - 1)) + start_pos
                            abs_end = abs_start + len(var_name)
                            push(var_name, abs_start, abs_end)
            elif isinstance(node, ast.ClassDef):
                var_name = node.name
                if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
                    if 0 <= node.lineno - 1 < len(lines):
                        line = lines[node.lineno - 1]
                        start_pos = line.find("class ", 0, node.col_offset) + 6
                        if start_pos >= 6:
                            abs_start = sum(len(lines[i]) + 1 for i in range(node.lineno - 1)) + start_pos
                            abs_end = abs_start + len(var_name)
                            push(var_name, abs_start, abs_end)
        return variable_info
    except Exception:
        return {}

def get_closing_token_mask(tokenizer, text: str, input_ids: torch.Tensor) -> torch.Tensor:
    DATA_MODEL_SYMBOLS = {"]", "}", ")", ".", "'", '"'}
    EXPRESSIONS_KEYWORDS = {"in", "else", "is", "not"}
    EXPRESSIONS_SYMBOLS = {"]", "}", ")", ":"}
    SINGLE_STMT_KEYWORDS = {"as", "import", "from", "global", "nonlocal", "assert"}
    SINGLE_STMT_SYMBOLS = {","}
    COMPOUND_KEYWORDS = {"if", "for", "while", "try", "with", "class", "def", "elif", "else", "except", "finally", "match", "case", "async"}
    FUNC_ARG_TOKENS = {"self", "/", "*"}
    ARROW_TOKENS = {"->", "-", ">"}
    CLOSE_KEYWORDS = set().union(EXPRESSIONS_KEYWORDS, SINGLE_STMT_KEYWORDS, COMPOUND_KEYWORDS, FUNC_ARG_TOKENS)
    CLOSE_SYMBOLS = set().union(DATA_MODEL_SYMBOLS, EXPRESSIONS_SYMBOLS, SINGLE_STMT_SYMBOLS, ARROW_TOKENS, {":", ";", ","})
    mask = torch.ones(input_ids.shape[1] - 1, dtype=torch.bool)
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0][1:])
    encoding = tokenizer.encode_plus(
        text,
        return_offsets_mapping=True,
        add_special_tokens=True,
        max_length=len(input_ids[0]),
        truncation=True,
        padding="max_length"
    )
    offset_mapping = encoding['offset_mapping'][1:len(tokens)+1]
    variable_positions = extract_variable_names(text)
    all_var_positions = set()
    for positions in variable_positions.values():
        for start, end in positions:
            all_var_positions.add((start, end))
    for i, token in enumerate(tokens):
        if token == '[PAD]':
            mask[i] = False
            continue
        if token.strip() != token:
            mask[i] = False
            continue
        if i < len(offset_mapping):
            token_start, token_end = offset_mapping[i]
            for var_start, var_end in all_var_positions:
                if max(token_start, var_start) < min(token_end, var_end):
                    mask[i] = False
                    break
        bare = token.strip()
        if bare in CLOSE_KEYWORDS or bare in CLOSE_SYMBOLS:
            mask[i] = False
        elif bare == "_":
            mask[i] = False
        elif bare == "." and 0 < i < len(tokens) - 1:
            prev_token = tokens[i-1].strip()
            if prev_token == "self" or any(prev_token == var_name for var_name in variable_positions):
                mask[i] = False
    return mask

def safe_compute_scores(token_log_probs: torch.Tensor, mask: torch.Tensor, ratio: float) -> float:
    valid_probs = token_log_probs[mask]
    if len(valid_probs) == 0:
        return 0.0
    valid_probs = valid_probs - valid_probs.max()
    valid_probs = torch.exp(valid_probs)
    valid_probs = valid_probs / valid_probs.sum()
    k = min(int(len(valid_probs) * ratio), len(valid_probs))
    return 0.0 if k == 0 else torch.mean(torch.sort(valid_probs)[0][:k]).item()

def synprune_score_for_sample(model, tokenizer, raw: str, max_length: int = 512) -> float:
    enc = tokenizer.encode_plus(
        raw,
        max_length=max_length,
        truncation=True,
        return_tensors="pt",
        return_offsets_mapping=True,
        add_special_tokens=True,
        padding="max_length",
        pad_to_multiple_of=8
    )
    inp = enc["input_ids"].to(model.device)
    attention_mask = enc["attention_mask"].to(model.device)
    with torch.no_grad():
        logits = model(inp, labels=inp, attention_mask=attention_mask).logits
        mask = get_closing_token_mask(tokenizer, raw, inp)
        log_probs = F.log_softmax(logits[0, :-1], dim=-1)
        masked_log_probs = log_probs.clone()
        masked_log_probs[~mask] = float('-inf')
        masked_log_probs = F.log_softmax(masked_log_probs, dim=-1)
        ids_next = inp[0][1:].unsqueeze(-1)
        token_lp = masked_log_probs.gather(dim=-1, index=ids_next).squeeze(-1)
        return safe_compute_scores(token_lp, mask, 1.0)

def load_model(name: str, int8: bool, half: bool):
    int8_kwargs = {"load_in_8bit": True, "torch_dtype": torch.bfloat16} if int8 else {}
    half_kwargs = {"torch_dtype": torch.bfloat16} if half and not int8 else {}
    model = AutoModelForCausalLM.from_pretrained(
        name, return_dict=True, device_map="auto", **int8_kwargs, **half_kwargs
    )
    tokenizer = AutoTokenizer.from_pretrained(name)
    if tokenizer.pad_token is None:
        if tokenizer.eos_token is not None:
            tokenizer.pad_token = tokenizer.eos_token
        else:
            tokenizer.add_special_tokens({'pad_token': '[PAD]'})
            model.resize_token_embeddings(len(tokenizer))
    if getattr(model.config, "pad_token_id", None) is None and tokenizer.pad_token_id is not None:
        model.config.pad_token_id = tokenizer.pad_token_id
    return model, tokenizer

def make_breakpoint_thresholds(scores: np.ndarray) -> np.ndarray:
    uniq = np.sort(np.unique(scores))
    if len(uniq) == 1:
        return np.array([uniq[0] - 1e-12, uniq[0] + 1e-12], dtype=float)
    cuts = (uniq[:-1] + uniq[1:]) / 2.0
    return np.concatenate(([uniq[0] - 1e-12], cuts, [uniq[-1] + 1e-12])).astype(float)

def confusion_and_metrics(preds: np.ndarray, labels: np.ndarray):
    TP = int(np.sum((preds == 1) & (labels == 1)))
    FP = int(np.sum((preds == 1) & (labels == 0)))
    TN = int(np.sum((preds == 0) & (labels == 0)))
    FN = int(np.sum((preds == 0) & (labels == 1)))
    P = TP / (TP + FP + 1e-12)
    R = TP / (TP + FN + 1e-12)
    F1 = 2 * P * R / (P + R + 1e-12)
    FPR = FP / (FP + TN + 1e-12)
    TPR = R
    return TP, FP, TN, FN, P, R, F1, FPR, TPR

def pick_best_threshold(scores: np.ndarray, labels: np.ndarray):
    thr_cands = make_breakpoint_thresholds(scores)
    best = None
    for t in thr_cands:
        preds = (scores >= t).astype(int)
        TP, FP, TN, FN, P, R, F1, FPR, TPR = confusion_and_metrics(preds, labels)
        if (best is None) or (F1 > best["F1"]):
            best = dict(thr=float(t), TP=TP, FP=FP, TN=TN, FN=FN, P=P, R=R, F1=F1, FPR=FPR, TPR=TPR)
    return best, thr_cands

def build_weighted_warp(knots: np.ndarray, weights: np.ndarray):
    xs = np.asarray(knots, dtype=float)
    ws = np.asarray(weights, dtype=float)
    wnorm = ws / ws.sum()
    cum = np.concatenate([[0.0], np.cumsum(wnorm)])
    def warp(x):
        x = np.asarray(x, dtype=float)
        x_clipped = np.clip(x, xs[0], xs[-1])
        idx = np.searchsorted(xs, x_clipped, side="right") - 1
        idx = np.clip(idx, 0, len(xs) - 2)
        left = xs[idx]
        right = xs[idx + 1]
        t_local = (x_clipped - left) / (right - left + 1e-30)
        t = cum[idx] + wnorm[idx] * t_local
        return t
    return warp

def plot_f1_curve(
    scores: np.ndarray,
    labels: np.ndarray,
    thr_grid: np.ndarray,
    out_path: str,
    ticks: np.ndarray,
    weights: np.ndarray,
    scatter_x: Optional[np.ndarray] = None,
    scatter_step: int = 1,
    scatter_size: float = 10.0,
    scatter_alpha: float = 0.7,
):
    f1s = np.array([f1_score(labels, (scores >= thr).astype(int), zero_division=0) for thr in thr_grid])
    warp = build_weighted_warp(ticks, weights)
    t_grid = warp(thr_grid)
    t_ticks = warp(ticks)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(t_grid, f1s, linewidth=1.6)
    if scatter_x is not None and len(scatter_x) > 0:
        f1_scatter = np.array([f1_score(labels, (scores >= thr).astype(int), zero_division=0) for thr in scatter_x])
        t_scatter = warp(scatter_x)
        step = max(1, int(scatter_step))
        t_scatter = t_scatter[::step]
        f1_scatter = f1_scatter[::step]
        ax.scatter(t_scatter, f1_scatter, s=scatter_size, alpha=scatter_alpha, edgecolors="none", zorder=3)
    label_fs = 18
    tick_fs  = 16
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel(r"Threshold $\epsilon$", fontsize=label_fs)
    ax.set_ylabel("F1-score", fontsize=label_fs)
    ax.set_xticks(t_ticks)
    ax.set_xticklabels([f"{v:g}" for v in ticks])
    ax.tick_params(axis="x", which="both", labelsize=tick_fs, pad=10)
    ax.tick_params(axis="y", which="both", labelsize=tick_fs)
    ax.grid(True, which='major', linestyle='--', linewidth=0.8, alpha=0.6)
    ax.minorticks_on()
    try:
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    except Exception:
        pass
    ax.grid(True, which='minor', linestyle=':', linewidth=0.6, alpha=0.35)
    fig.tight_layout()
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()

def parse_floats_csv(s: str) -> np.ndarray:
    return np.array([float(x.strip()) for x in s.split(",") if x.strip() != ""], dtype=float)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="Path to the dataset .jsonl")
    ap.add_argument("--model", default="EleutherAI/pythia-2.8b")
    ap.add_argument("--max_length", type=int, default=512)
    ap.add_argument("--int8", action="store_true")
    ap.add_argument("--half", action="store_true")
    ap.add_argument("--out", default="", help="Save figure path (pdf/png). Empty => show window")
    ap.add_argument("--ticks", type=str, default="", help="Comma-separated tick values; empty => auto from scores")
    ap.add_argument("--weights", type=str, default="", help="Comma-separated segment weights; empty => uniform")
    ap.add_argument("--scatter", choices=["breakpoints", "plotgrid", "both", "none"], default="breakpoints")
    ap.add_argument("--scatter-step", type=int, default=1)
    ap.add_argument("--scatter-size", type=float, default=10.0)
    ap.add_argument("--scatter-alpha", type=float, default=0.7)
    args = ap.parse_args()
    data = load_jsonl_dataset(args.dataset)
    labels = np.array([int(d.get("label", 0)) for d in data], dtype=int)
    model, tokenizer = load_model(args.model, args.int8, args.half)
    model.eval()
    scores = []
    for d in data:
        s = synprune_score_for_sample(model, tokenizer, d["function"], max_length=args.max_length)
        scores.append(s)
    scores = np.array(scores, dtype=float)
    print(f"[SynPrune] AUROC={roc_auc_score(labels, scores):.3f}")
    print(f"#samples={len(scores)}  pos_ratio={np.mean(labels==1):.3f}")
    print(f"score min/max = {float(np.min(scores)):.6g} / {float(np.max(scores)):.6g}")
    print(f"unique score count = {len(np.unique(scores))}")
    best, thr_breaks = pick_best_threshold(scores, labels)
    print("---- Best threshold (F1) ----")
    print(f"threshold = {best['thr']:.12g}")
    print(f"F1={best['F1']:.4f}  P={best['P']:.4f}  R={best['R']:.4f}  FPR={best['FPR']:.4f}  TPR={best['TPR']:.4f}")
    print(f"TP={best['TP']}  FP={best['FP']}  TN={best['TN']}  FN={best['FN']}")
    thr_plot = thr_breaks
    if args.ticks.strip():
        ticks = parse_floats_csv(args.ticks)
    else:
        lo, hi = float(np.min(scores)), float(np.max(scores))
        if lo == hi:
            ticks = np.linspace(lo - 1e-6, hi + 1e-6, 8)
        else:
            ticks = np.linspace(lo, hi, 8)
    if args.weights.strip():
        weights = parse_floats_csv(args.weights)
    else:
        weights = np.ones(len(ticks) - 1, dtype=float)
    scatter_x = None
    if args.scatter != "none":
        cand = []
        if args.scatter in ("breakpoints", "both"):
            cand.append(thr_breaks)
        if args.scatter in ("plotgrid", "both"):
            cand.append(thr_plot)
        if cand:
            scatter_x = np.unique(np.concatenate(cand))
    if np.min(scores) < ticks[0] - 1e-12 or np.max(scores) > ticks[-1] + 1e-12:
        print("[WARN] score range lies outside tick domain; edges will be visually clipped.")
    plot_f1_curve(scores, labels, thr_plot, args.out, ticks, weights,
                  scatter_x=scatter_x,
                  scatter_step=args.scatter_step,
                  scatter_size=args.scatter_size,
                  scatter_alpha=args.scatter_alpha)

if __name__ == "__main__":
    main()
