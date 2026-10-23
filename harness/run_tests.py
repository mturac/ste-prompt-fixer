#!/usr/bin/env python3
"""ste-prompt-fixer test harness.

Runs tests/fixtures.md against a model that has SKILL.md loaded.
Deterministic checks only: word counts, filler phrases, code block counts,
question detection. No LLM-as-judge by default.

Usage:
  python harness/run_tests.py --provider anthropic  # needs ANTHROPIC_API_KEY
  python harness/run_tests.py --provider openai     # needs OPENAI_API_KEY
  python harness/run_tests.py --provider mock --mock t/sample/

Mock mode: file <mock_dir>/NN.txt holds the recorded model reply for fixture NN.
Exit code: 0 all pass, 1 any failure. Output mimics ste-lint.md format.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures.md"
SKILL = ROOT / "SKILL.md"
PROFILES = ROOT / "profiles"

BANNED_FILLER = [
    "it is worth noting", "in conclusion", "moreover", "furthermore",
    "delve into", "tapestry", "ever-evolving", "leverage", "seamless",
    "robust", "cutting-edge", "in today's fast-paced world", "unlock",
    "unleash", "elevate", "harness", "supercharge", "revolutionize",
    "game-changer",
]


def parse_fixtures(text: str) -> list[dict]:
    current_profile = "ste80"
    fixtures = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^##\s+(.+)", lines[i])
        if m:
            head = m.group(1).strip().lower()
            if head in ("ste80", "plain", "globish", "cte", "tr"):
                current_profile = head
            i += 1
            continue
        m = re.match(r"^(\d+)\.\s+bad:\s*(.+)", lines[i])
        if m:
            fx = {
                "n": int(m.group(1)),
                "bad": m.group(2).strip().strip('"'),
                "profile": current_profile,
                "context": None,
                "fixed": None,
                "behavior": None,
            }
            i += 1
            while i < len(lines) and re.match(r"^\s{3,}\S", lines[i]):
                kv = re.match(
                    r"^\s+(profile|context|fixed|expected skill behavior):\s*(.*)",
                    lines[i],
                )
                if kv:
                    key = {
                        "profile": "profile",
                        "context": "context",
                        "fixed": "fixed",
                        "expected skill behavior": "behavior",
                    }[kv.group(1)]
                    fx[key] = kv.group(2).strip().strip('"')
                i += 1
            fixtures.append(fx)
            continue
        i += 1
    return fixtures


def build_system_prompt() -> str:
    return SKILL.read_text(encoding="utf-8")


def profile_addendum(fx: dict) -> str:
    name = fx["profile"]
    path = PROFILES / f"{name}.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return f'Active profile file:\n\n{text}\n\n=== END PROFILE {name.upper()} ==='


def user_message(fx: dict) -> str:
    parts = [f"User prompt to fix:\n\n{fx['bad']}"]
    if fx["context"]:
        parts.append(f"Context: {fx['context']}")
    return "\n\n".join(parts)


def call_anthropic(system: str, user: str, model: str) -> str:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(
            {
                "model": model,
                "max_tokens": 1024,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        ).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as r:
        body = json.loads(r.read())
    return "".join(b.get("text", "") for b in body.get("content", []))


def call_openai(system: str, user: str, model: str) -> str:
    api_key = os.environ["OPENAI_API_KEY"]
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as r:
        body = json.loads(r.read())
    return body["choices"][0]["message"]["content"]


def code_blocks(text: str) -> list[str]:
    return re.findall(r"```\w*\n(.*?)```", text, flags=re.DOTALL)


def word_count(text: str) -> int:
    return len(text.split())


def check_fixture(fx: dict, reply: str) -> list[tuple[str, str]]:
    """Return list of (rule_id, message) violations. Empty = pass."""
    issues: list[tuple[str, str]] = []
    blocks = code_blocks(reply)
    behavior = (fx["behavior"] or "").lower()

    low = reply.lower()
    for phrase in BANNED_FILLER:
        if phrase in low:
            issues.append(("FILLER", f"banned phrase: '{phrase}'"))

    if "multi-intent" in behavior:
        if len(blocks) < 3:
            issues.append(("MULTI", f"expected >=3 fixed prompts, got {len(blocks)} blocks"))
        for blk in blocks:
            if word_count(blk) > 150:
                issues.append(("WORDS", f"fixed prompt block has {word_count(blk)} words (>150)"))
    elif "ask one question" in behavior or "contradictory" in behavior:
        if "?" not in reply:
            issues.append(("ASK", "no clarifying question found"))
        joined = " ".join(blocks)
        if word_count(joined) > 20:
            issues.append(("SILENTGUESS", "gave a fixed prompt instead of asking"))
    elif "already good" in behavior:
        if "already good" not in low:
            issues.append(("TOUCH", "did not state the prompt is already good"))
        if blocks:
            issues.append(("TOUCH", "rewrote a prompt that was already good"))
    elif fx["fixed"]:
        if not blocks:
            issues.append(("NOBLOCK", "no fixed prompt code block produced"))
        else:
            longest = max(blocks, key=word_count)
            if word_count(longest) > 160:
                issues.append(("WORDS", f"fixed prompt has {word_count(longest)} words (>160 cap)"))
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="ste-prompt-fixer harness")
    ap.add_argument("--provider", choices=["anthropic", "openai", "mock"], required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--mock", metavar="DIR", help="replay dir: <dir>/NN.txt per fixture")
    ap.add_argument("--only", nargs="*", type=int, help="fixture numbers to run")
    args = ap.parse_args()

    fixtures = parse_fixtures(FIXTURES.read_text(encoding="utf-8"))
    if args.only:
        fixtures = [f for f in fixtures if f["n"] in args.only]

    if args.provider == "mock" and not args.mock:
        print("--provider mock requires --mock DIR")
        return 2

    model = args.model or ("claude-sonnet-4-5" if args.provider == "anthropic" else "gpt-4.1")
    caller = call_anthropic if args.provider == "anthropic" else call_openai
    system = build_system_prompt()

    failures = 0
    for fx in fixtures:
        try:
            if args.provider == "mock":
                reply = Path(args.mock, f"{fx['n']}.txt").read_text(encoding="utf-8")
            else:
                sys_prompt = system + "\n\n" + profile_addendum(fx)
                reply = caller(sys_prompt, user_message(fx), model)
        except Exception as e:  # noqa: BLE001
            print(f"fixtures.md:{fx['n']} CALL {type(e).__name__}: {e}")
            failures += 1
            continue
        issues = check_fixture(fx, reply)
        if issues:
            for rid, msg in issues:
                print(f"fixtures.md:{fx['n']} {rid} {msg}")
                failures += 1
        else:
            print(f"fixtures.md:{fx['n']} PASS")

    total = len(fixtures)
    print(f"\n{total - failures}/{total} checks clean")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
