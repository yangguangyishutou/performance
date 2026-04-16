"""Generate HumanEval completions from prepared prompts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.humaneval_backends import GenerationConfig, build_backend
from eval.humaneval_utils import (
    default_details_output_path,
    default_samples_output_path,
    load_jsonl,
    write_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HumanEval completions with OpenAI API, vLLM, or Transformers.")
    parser.add_argument("--input", type=Path, required=True, help="Prepared JSONL from humaneval_prepare.py")
    parser.add_argument("--backend", choices=("openai", "vllm", "transformers"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter-path", default=None)
    parser.add_argument("--arm", choices=("raw", "compressed"), default="compressed")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--stop", action="append", default=None)
    parser.add_argument("--tag", default="")
    parser.add_argument("--output", type=Path, default=None, help="samples.jsonl for HumanEval scoring")
    parser.add_argument("--details-output", type=Path, default=None, help="Detailed generation JSONL")
    parser.add_argument("--openai-api-key", default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--openai-base-url", default=os.getenv("OPENAI_BASE_URL"))
    parser.add_argument("--vllm-tokenizer", default=os.getenv("ET_VLLM_TOKENIZER"))
    parser.add_argument("--hf-tokenizer", default=os.getenv("ET_HF_TOKENIZER"))
    parser.add_argument("--tensor-parallel-size", type=int, default=int(os.getenv("ET_VLLM_TP_SIZE", "1")))
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=float(os.getenv("ET_VLLM_GPU_MEMORY_UTILIZATION", "0.9")),
    )
    parser.add_argument("--dtype", default=os.getenv("ET_VLLM_DTYPE", "auto"))
    parser.add_argument("--device-map", default=os.getenv("ET_HF_DEVICE_MAP", "auto"))
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--max-model-len", type=int, default=None)
    args = parser.parse_args()

    rows = load_jsonl(args.input)
    backend = build_backend(
        backend=args.backend,
        model=args.model,
        api_key=args.openai_api_key,
        base_url=args.openai_base_url,
        vllm_tokenizer=args.vllm_tokenizer,
        hf_tokenizer=args.hf_tokenizer,
        adapter_path=args.adapter_path,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        dtype=args.dtype,
        load_in_4bit=not args.no_4bit,
        device_map=args.device_map,
        max_model_len=args.max_model_len,
    )
    gen_cfg = GenerationConfig(
        n=args.n,
        temperature=args.temperature,
        top_p=args.top_p,
        max_new_tokens=args.max_new_tokens,
        stop=args.stop,
        seed=args.seed,
    )

    samples: list[dict] = []
    details: list[dict] = []
    prompt_key = "prompt_compressed" if args.arm == "compressed" else "prompt_raw"
    for idx, row in enumerate(rows, start=1):
        prompt = str(row[prompt_key])
        result = backend.generate(prompt, gen_cfg)
        prompt_tokens = None
        try:
            prompt_tokens = backend.count_tokens(prompt)
        except Exception:
            prompt_tokens = None
        details.append(
            {
                "task_id": row["task_id"],
                "arm": args.arm,
                "backend": args.backend,
                "model": args.model,
                "prompt_tokens": prompt_tokens,
                "usage": result.usage,
                "n_completions": len(result.completions),
            }
        )
        for completion in result.completions:
            samples.append({"task_id": row["task_id"], "completion": completion})
        print(
            f"[generate] {idx}/{len(rows)} {row['task_id']} "
            f"prompt_tokens={prompt_tokens if prompt_tokens is not None else 'na'} "
            f"n={len(result.completions)}"
        )

    output = args.output or default_samples_output_path(arm=args.arm, backend=args.backend, tag=args.tag)
    details_output = args.details_output or default_details_output_path(
        arm=args.arm,
        backend=args.backend,
        tag=args.tag,
    )
    write_jsonl(output, samples)
    write_jsonl(details_output, details)
    print(output)
    print(details_output)


if __name__ == "__main__":
    main()
