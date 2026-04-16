"""Generation backends for HumanEval experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class GenerationConfig:
    n: int = 1
    temperature: float = 0.0
    top_p: float = 1.0
    max_new_tokens: int = 256
    stop: list[str] | None = None
    seed: int | None = None


@dataclass(slots=True)
class GenerationResult:
    completions: list[str]
    usage: dict[str, Any] | None = None


def _clean_completion_text(text: str) -> str:
    out = (text or "").replace("\r\n", "\n")
    stripped = out.lstrip()
    if stripped.startswith("```"):
        first_nl = stripped.find("\n")
        if first_nl >= 0:
            body = stripped[first_nl + 1 :]
            fence = body.find("\n```")
            if fence >= 0:
                out = body[:fence]
            else:
                out = body
    return out.rstrip()


def _apply_stop_sequences(text: str, stop: list[str] | None) -> str:
    if not stop:
        return text
    out = text
    cut = None
    for marker in stop:
        if not marker:
            continue
        idx = out.find(marker)
        if idx >= 0 and (cut is None or idx < cut):
            cut = idx
    if cut is not None:
        out = out[:cut]
    return out.rstrip()


class OpenAIChatBackend:
    """OpenAI chat-completions backend."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or None,
            timeout=timeout,
        )
        self._encoder = None
        try:
            import tiktoken

            try:
                self._encoder = tiktoken.encoding_for_model(model)
            except KeyError:
                self._encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoder = None

    def count_tokens(self, text: str) -> int | None:
        if self._encoder is None:
            return None
        return len(self._encoder.encode(text or ""))

    def generate(self, prompt: str, cfg: GenerationConfig) -> GenerationResult:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "n": int(cfg.n),
            "temperature": float(cfg.temperature),
            "top_p": float(cfg.top_p),
            "max_tokens": int(cfg.max_new_tokens),
        }
        if cfg.stop:
            kwargs["stop"] = list(cfg.stop)
        if cfg.seed is not None:
            kwargs["seed"] = int(cfg.seed)
        resp = self.client.chat.completions.create(**kwargs)
        completions = []
        for choice in resp.choices:
            content = choice.message.content or ""
            completions.append(_clean_completion_text(content))
        usage = None
        if getattr(resp, "usage", None) is not None:
            try:
                usage = resp.usage.model_dump()
            except Exception:
                usage = {
                    "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
                    "completion_tokens": getattr(resp.usage, "completion_tokens", None),
                    "total_tokens": getattr(resp.usage, "total_tokens", None),
                }
        return GenerationResult(completions=completions, usage=usage)


class VLLMBackend:
    """Local vLLM backend. This requires a Linux/WSL runtime with vllm installed."""

    def __init__(
        self,
        *,
        model: str,
        tokenizer: str | None = None,
        trust_remote_code: bool = True,
        dtype: str = "auto",
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.9,
        max_model_len: int | None = None,
    ) -> None:
        try:
            from vllm import LLM
        except Exception as exc:  # pragma: no cover - env dependent
            raise RuntimeError(
                "vLLM is not available in this Python environment. "
                "Use WSL/Linux with vllm installed, or switch to the OpenAI backend."
            ) from exc

        llm_kwargs: dict[str, Any] = {
            "model": model,
            "trust_remote_code": trust_remote_code,
            "dtype": dtype,
            "tensor_parallel_size": int(tensor_parallel_size),
            "gpu_memory_utilization": float(gpu_memory_utilization),
        }
        if tokenizer:
            llm_kwargs["tokenizer"] = tokenizer
        if max_model_len is not None:
            llm_kwargs["max_model_len"] = int(max_model_len)
        self.model = model
        self._llm = LLM(**llm_kwargs)
        self._hf_tokenizer = None
        try:
            self._hf_tokenizer = self._llm.get_tokenizer()
        except Exception:  # pragma: no cover - env dependent
            try:
                from transformers import AutoTokenizer

                self._hf_tokenizer = AutoTokenizer.from_pretrained(
                    tokenizer or model,
                    trust_remote_code=trust_remote_code,
                )
            except Exception:
                self._hf_tokenizer = None

    def count_tokens(self, text: str) -> int | None:
        if self._hf_tokenizer is None:
            return None
        try:
            return len(self._hf_tokenizer.encode(text or "", add_special_tokens=False))
        except Exception:
            return None

    def generate(self, prompt: str, cfg: GenerationConfig) -> GenerationResult:
        from vllm import SamplingParams  # pragma: no cover - env dependent

        params = SamplingParams(
            n=int(cfg.n),
            temperature=float(cfg.temperature),
            top_p=float(cfg.top_p),
            max_tokens=int(cfg.max_new_tokens),
            stop=list(cfg.stop or []),
            seed=cfg.seed,
        )
        outputs = self._llm.generate([prompt], params)
        result = outputs[0]
        completions = [_clean_completion_text(x.text) for x in result.outputs]
        return GenerationResult(completions=completions, usage=None)


class TransformersBackend:
    """Local Transformers backend for single-GPU generation and LoRA adapters."""

    def __init__(
        self,
        *,
        model: str,
        tokenizer: str | None = None,
        adapter_path: str | None = None,
        trust_remote_code: bool = True,
        dtype: str = "auto",
        load_in_4bit: bool = True,
        device_map: str = "auto",
        max_model_len: int | None = None,
    ) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model = model
        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(
            tokenizer or model,
            trust_remote_code=trust_remote_code,
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        if max_model_len is not None:
            self._tokenizer.model_max_length = int(max_model_len)

        model_kwargs: dict[str, Any] = {
            "trust_remote_code": trust_remote_code,
        }
        if torch.cuda.is_available():
            model_kwargs["device_map"] = device_map
            if dtype != "auto":
                model_kwargs["torch_dtype"] = getattr(torch, dtype)
            elif load_in_4bit:
                try:
                    from transformers import BitsAndBytesConfig

                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_compute_dtype=torch.float16,
                    )
                except Exception:
                    model_kwargs["torch_dtype"] = torch.float16
            else:
                model_kwargs["torch_dtype"] = torch.float16
        else:
            model_kwargs["torch_dtype"] = torch.float32

        model_obj = AutoModelForCausalLM.from_pretrained(model, **model_kwargs)
        if adapter_path:
            from peft import PeftModel

            model_obj = PeftModel.from_pretrained(model_obj, adapter_path)
        model_obj.eval()
        self._model = model_obj

    def count_tokens(self, text: str) -> int | None:
        try:
            return len(self._tokenizer.encode(text or "", add_special_tokens=False))
        except Exception:
            return None

    def generate(self, prompt: str, cfg: GenerationConfig) -> GenerationResult:
        tok = self._tokenizer(prompt, return_tensors="pt")
        if hasattr(self._model, "device"):
            device = self._model.device
            tok = {k: v.to(device) for k, v in tok.items()}
        do_sample = float(cfg.temperature) > 0.0
        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": int(cfg.max_new_tokens),
            "do_sample": do_sample,
            "top_p": float(cfg.top_p),
            "num_return_sequences": int(cfg.n),
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }
        if do_sample:
            gen_kwargs["temperature"] = float(cfg.temperature)
        with self._torch.inference_mode():
            out = self._model.generate(**tok, **gen_kwargs)
        prompt_len = int(tok["input_ids"].shape[-1])
        completions: list[str] = []
        for seq in out:
            text = self._tokenizer.decode(seq[prompt_len:], skip_special_tokens=True)
            text = _clean_completion_text(text)
            text = _apply_stop_sequences(text, cfg.stop)
            completions.append(text)
        return GenerationResult(completions=completions, usage=None)


def build_backend(
    *,
    backend: str,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    vllm_tokenizer: str | None = None,
    hf_tokenizer: str | None = None,
    adapter_path: str | None = None,
    trust_remote_code: bool = True,
    dtype: str = "auto",
    load_in_4bit: bool = True,
    device_map: str = "auto",
    tensor_parallel_size: int = 1,
    gpu_memory_utilization: float = 0.9,
    max_model_len: int | None = None,
) -> Any:
    name = (backend or "").strip().lower()
    if name == "openai":
        return OpenAIChatBackend(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
    if name == "vllm":
        return VLLMBackend(
            model=model,
            tokenizer=vllm_tokenizer,
            trust_remote_code=trust_remote_code,
            dtype=dtype,
            tensor_parallel_size=tensor_parallel_size,
            gpu_memory_utilization=gpu_memory_utilization,
            max_model_len=max_model_len,
        )
    if name == "transformers":
        return TransformersBackend(
            model=model,
            tokenizer=hf_tokenizer,
            adapter_path=adapter_path,
            trust_remote_code=trust_remote_code,
            dtype=dtype,
            load_in_4bit=load_in_4bit,
            device_map=device_map,
            max_model_len=max_model_len,
        )
    raise ValueError(f"unknown backend: {backend}")
