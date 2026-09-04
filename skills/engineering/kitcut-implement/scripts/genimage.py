#!/usr/bin/env python3
"""genimage — image-generation adapter for kitcut-implement.

Used ONLY when an artifact edit added an image resource with no evidence
payload; existing assets are always copied from evidence/ instead.

Provider selection via env:
  KIT_IMAGE_PROVIDER = openai | gemini | none (default: none)
  KIT_IMAGE_ENDPOINT = override API endpoint (tests point this at a mock)
  OPENAI_API_KEY     = key for the openai provider

Exit codes: 0 ok · 3 provider unavailable · 4 missing key · 5 provider error
Output: single JSON object on stdout. stdlib only.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.request


def fail(code: int, msg: str) -> int:
    print(json.dumps({"error": msg}))
    return code


def openai_generate(prompt: str, size: str, out: str) -> int:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return fail(4, "OPENAI_API_KEY not set")
    endpoint = os.environ.get("KIT_IMAGE_ENDPOINT",
                              "https://api.openai.com/v1/images/generations")
    body = json.dumps({"model": "gpt-image-1", "prompt": prompt, "size": size}).encode()
    req = urllib.request.Request(
        endpoint, data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read())
        b64 = payload["data"][0]["b64_json"]
    except Exception as exc:  # noqa: BLE001 — adapter must report, not crash
        return fail(5, f"provider error: {exc}")
    raw = base64.b64decode(b64)
    with open(out, "wb") as f:
        f.write(raw)
    print(json.dumps({"out": out, "bytes": len(raw), "provider": "openai"}))
    return 0


def gemini_generate(prompt: str, size: str, out: str) -> int:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return fail(4, "GEMINI_API_KEY not set")
    model = os.environ.get("KIT_IMAGE_MODEL", "gemini-2.5-flash-image")
    base = os.environ.get("KIT_IMAGE_ENDPOINT",
                          "https://generativelanguage.googleapis.com/v1beta")
    endpoint = f"{base}/models/{model}:generateContent?key={key}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()
    req = urllib.request.Request(endpoint, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload = json.loads(resp.read())
        b64 = next(p["inlineData"]["data"]
                   for c in payload.get("candidates", [])
                   for p in c.get("content", {}).get("parts", [])
                   if "inlineData" in p)
    except Exception as exc:  # noqa: BLE001 — adapter must report, not crash
        return fail(5, f"provider error: {exc}")
    raw = base64.b64decode(b64)
    with open(out, "wb") as f:
        f.write(raw)
    print(json.dumps({"out": out, "bytes": len(raw), "provider": "gemini"}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="genimage", description=__doc__)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--ref", help="reference image path (provider support varies)")
    args = ap.parse_args(argv)

    provider = os.environ.get("KIT_IMAGE_PROVIDER", "none").lower()
    if provider in ("", "none"):
        return fail(3, "provider unavailable: set KIT_IMAGE_PROVIDER=openai and its API key")
    if provider == "openai":
        return openai_generate(args.prompt, args.size, args.out)
    if provider == "gemini":
        return gemini_generate(args.prompt, args.size, args.out)
    return fail(3, f"provider unavailable: unknown provider {provider!r}")


if __name__ == "__main__":
    sys.exit(main())
