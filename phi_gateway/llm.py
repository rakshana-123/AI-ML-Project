"""LLM client for the round trip, with a real offline local option.

Provider priority (first available wins):
  1. Groq free tier      - set GROQ_API_KEY       (model GROQ_MODEL or llama-3.3-70b-versatile)
  2. any OpenAI-compatible endpoint - set OPENAI_API_KEY (+ OPENAI_BASE_URL)
  3. local Ollama        - running at http://localhost:11434 (model OLLAMA_MODEL or llama3.2)
  4. local HF model      - Qwen2.5-0.5B-Instruct (default; override with
                           LOCAL_LLM_ID), runs on CPU, no network after the
                           one-time download.  Set PHI_NO_LOCAL_LLM=1 to skip.
  5. MockLLM             - deterministic extractive summariser, no network

The mapping is never part of the prompt - callers only pass the masked note.
"""

from __future__ import annotations

import os
import re

import requests

GROQ_BASE = "https://api.groq.com/openai/v1"


class MockLLM:
    """Deterministic offline stand-in so the demo always runs.

    It picks the clinically-flavoured sentences from the note (the ones with
    diagnosis/plan vocabulary) - good enough to demonstrate rehydration.
    """

    name = "mock (offline deterministic)"

    def complete(self, prompt: str, max_sentences: int = 4, **kw) -> str:
        note = prompt.split("NOTE:", 1)[-1]
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", note)
                     if s.strip()]
        keywords = ("diagnos", "assessment", "plan", "presents", "symptom",
                    "treatment", "follow", "recommend", "impression",
                    "condition", "medication", "stable")
        picked = [s for s in sentences
                  if any(k in s.lower() for k in keywords)]
        if not picked:
            picked = sentences[:max_sentences]
        return "Summary: " + " ".join(picked[:max_sentences])


class _RestLLM:
    """OpenAI-compatible chat completion via plain requests."""

    def __init__(self, name, base_url, api_key, model, timeout=60):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.2},
            timeout=self.timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


class _OllamaLLM:
    def __init__(self, model, base_url="http://localhost:11434"):
        self.name = f"ollama:{model}"
        self.model = model
        self.base_url = base_url

    def complete(self, prompt: str) -> str:
        r = requests.post(f"{self.base_url}/api/chat",
                          json={"model": self.model, "stream": False,
                                "messages": [{"role": "user",
                                              "content": prompt}]},
                          timeout=120)
        r.raise_for_status()
        return r.json()["message"]["content"]


class LocalHFLLM:
    """A real open-weights LLM running locally on CPU via transformers.

    Default: Qwen2.5-0.5B-Instruct (~0.5B params, Apache-2.0).  Small enough
    to generate 3-4 sentence answers in seconds on a 12-core CPU, good
    enough at instruction following for the round-trip demo, and it needs
    no API key and no network after the one-time download.  Greedy decoding
    keeps answers deterministic across demo runs.
    """

    def __init__(self, model_id: str | None = None, max_new_tokens: int | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.model_id = model_id or os.environ.get(
            "LOCAL_LLM_ID", "Qwen/Qwen2.5-0.5B-Instruct")
        self.max_new_tokens = max_new_tokens or int(
            os.environ.get("PHI_LOCAL_LLM_MAX_TOKENS", "160"))
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id)
        self.model.eval()
        self.name = f"local:{self.model_id.split('/')[-1]} (CPU)"

    def complete(self, prompt: str, stream: bool = False, **kw) -> str:
        torch = self.torch
        import sys
        from transformers import TextStreamer
        messages = [{"role": "user", "content": prompt}]
        enc = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt",
            return_dict=True)
        streamer = TextStreamer(self.tokenizer, skip_prompt=True,
                                skip_special_tokens=True) if stream else None
        with torch.no_grad():
            out = self.model.generate(
                **enc,
                max_new_tokens=self.max_new_tokens, do_sample=False,
                temperature=None, top_p=None, top_k=None,
                pad_token_id=self.tokenizer.eos_token_id,
                streamer=streamer)
        text = self.tokenizer.decode(out[0][enc["input_ids"].shape[1]:],
                                     skip_special_tokens=True)
        return text.strip()


def get_llm():
    """Return the best available LLM client (never raises)."""
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return _RestLLM("groq", GROQ_BASE, key,
                        os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"))
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return _RestLLM("openai", base, key,
                        os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    try:  # local ollama?
        tags = requests.get("http://localhost:11434/api/tags", timeout=1.5)
        models = [m["name"] for m in tags.json().get("models", [])]
        if models:
            want = os.environ.get("OLLAMA_MODEL")
            model = next((m for m in models if m.startswith(want)), None) \
                if want else None
            return _OllamaLLM(model or models[0])
    except requests.RequestException:
        pass
    if not os.environ.get("PHI_NO_LOCAL_LLM"):
        try:
            return LocalHFLLM()
        except Exception as exc:      # no network / no disk - degrade quietly
            print(f"[llm] local model unavailable ({type(exc).__name__}: "
                  f"{exc}); falling back to offline mock")
    return MockLLM()
