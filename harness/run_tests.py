#!/usr/bin/env python3
"""ste-prompt-fixer test harness.

Runs tests/fixtures.md against a model that has the prompt contract loaded
at runtime via harness/prompt_loader.py :: load_prompt("prompt-fixer"),
plus SKILL.md (flow and profile selection only).

Deterministic checks only: word counts, filler phrases, code block counts,
question detection, and the five-part contract on the contract fixtures.
No LLM-as-judge by default.

Usage:
  python harness/run_tests.py --provider anthropic  # needs ANTHROPIC_API_KEY
  python harness/run_tests.py --provider openai     # needs OPENAI_API_KEY
  python harness/run_tests.py --provider mock --mock harness/recorded/

Recorded mode replays harness/recorded/NN.txt. It does not stub the loader.
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

from prompt_loader import load_prompt

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures.md"
SKILL = ROOT / "SKILL.md"
PROMPTS = ROOT / "prompts" / "prompt-fixer.md"
PROFILES = ROOT / "profiles"

PROFILE_FILES = {
    "ste80": "ste80.md",
    "plain": "plain-english.md",
    "globish": "globish.md",
    "cte": "cte-style.md",
    "tr": "turkish.md",
    "turkish": "turkish.md",
}

BANNED_FILLER = [
    "it is worth noting", "in conclusion", "moreover", "furthermore",
    "delve into", "tapestry", "ever-evolving", "leverage", "seamless",
    "robust", "cutting-edge", "in today's fast-paced world", "unlock",
    "unleash", "elevate", "harness", "supercharge", "revolutionize",
    "game-changer",
]

PARTS = ("understood", "not-sure", "draft", "changes", "approval")


def parse_fixtures(text: str) -> list[dict]:
    current_profile = "ste80"
    fixtures = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^##\s+(.+)", lines[i])
        if m:
            head = m.group(1).strip().lower()
            if head in PROFILE_FILES:
                current_profile = head
            i += 1
            continue
        m = re.match(r"^(\d+)\.\s+bad:\s*(.*)", lines[i])
        if m and m.group(2).strip():
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
    contract = load_prompt("prompt-fixer")
    skill = SKILL.read_text(encoding="utf-8")
    return contract + "\n\n=== SKILL FLOW ===\n\n" + skill


def profile_paths(profile_field: str | None) -> list[Path]:
    if not profile_field:
        return []
    paths: list[Path] = []
    for part in re.split(r"\s*\+\s*", profile_field.strip()):
        filename = PROFILE_FILES.get(part.strip().lower().rstrip("."))
        if filename:
            paths.append(PROFILES / filename)
    return paths


def profile_addendum(fx: dict) -> str:
    chunks = []
    for path in profile_paths(fx["profile"]):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        chunks.append(
            f"Active profile file ({path.name}):\n\n{text}\n\n"
            f"=== END PROFILE {path.stem.upper()} ==="
        )
    return "\n\n".join(chunks)


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


def outside_words(text: str) -> int:
    stripped = re.sub(r"```\w*\n.*?```", " ", text, flags=re.DOTALL)
    return word_count(stripped)


def tag_body(text: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
    if match is None:
        return None
    return match.group(1)


def opening_fence_labels(text: str) -> list[str]:
    labels = []
    for match in re.finditer(r"```\w*\n.*?```", text, flags=re.DOTALL):
        before = text[: match.start()].rstrip("\n")
        lines = before.splitlines()
        labels.append(lines[-1].strip() if lines else "")
    return labels


def change_rows(changes: str) -> list[str]:
    rows = []
    for line in changes.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        if re.match(r"^\|\s*change\s*\|", stripped, flags=re.I):
            continue
        rows.append(stripped)
    return rows


def require_choice_rows(changes: str) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    low = changes.lower()
    if "profile" not in low and "ste80" not in low and "turkish" not in low:
        issues.append(("PROFILE", "changes missing the profile choice"))
    if not any(token in low for token in ("format", "plain text", "düz metin", "mermaid", "html")):
        issues.append(("FORMAT", "changes missing the format choice"))
    rows = change_rows(changes)
    if not rows:
        issues.append(("CHANGES", "no change rows"))
    elif len(rows) > 5:
        issues.append(("CHANGES", f"{len(rows)} rows (>5)"))
    return issues


def require_understood(reply: str) -> list[tuple[str, str]]:
    body = tag_body(reply, "understood")
    if body is None:
        return [("CONTRACT", "missing <understood>")]
    text = " ".join(body.split())
    issues: list[tuple[str, str]] = []
    count = word_count(text)
    if count == 0 or count > 30:
        issues.append(("LEN", f"<understood> has {count} words (max 30, one sentence)"))
    sentences = [part for part in re.split(r"[.!?]+", text) if part.strip()]
    if len(sentences) != 1:
        issues.append(("LEN", "<understood> is not one sentence"))
    return issues


def require_not_sure(reply: str) -> list[tuple[str, str]]:
    body = tag_body(reply, "not-sure")
    if body is None:
        return [("CONTRACT", "missing <not-sure>")]
    bullets = [line for line in body.splitlines() if line.strip().startswith("-")]
    if len(bullets) > 3:
        return [("CONTRACT", f"<not-sure> has {len(bullets)} bullets (>3)")]
    if not bullets and "nothing missing" not in body.lower():
        return [("CONTRACT", "<not-sure> is empty")]
    return []


def require_five(reply: str) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    positions = []
    for tag in PARTS:
        match = re.search(rf"<{tag}>", reply)
        if match is None:
            issues.append(("CONTRACT", f"missing <{tag}>"))
        else:
            positions.append(match.start())
    if len(positions) == len(PARTS) and positions != sorted(positions):
        issues.append(("CONTRACT", "parts are out of order"))
    if not reply.strip().endswith("</approval>"):
        issues.append(("CONTRACT", "content after <approval>"))
    issues.extend(require_understood(reply))
    issues.extend(require_not_sure(reply))
    approval = tag_body(reply, "approval")
    if approval is not None and approval.count("?") != 1:
        issues.append(("ASK", "approval is not one question"))
    return issues


def word_cap_issues(reply: str) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    for block in code_blocks(reply):
        count = word_count(block)
        if count > 150:
            issues.append(("WORDS", f"draft block has {count} words (>150)"))
    outside = outside_words(reply)
    if outside > 150:
        issues.append(("WORDS", f"reply outside the draft is {outside} words (>150)"))
    return issues


def check_sources() -> list[tuple[str, str, str]]:
    """Return (location, rule_id, message) failures for the loader and contract."""
    issues: list[tuple[str, str, str]] = []
    location = "prompts/prompt-fixer.md"
    try:
        loaded = load_prompt("prompt-fixer")
    except (OSError, ValueError) as exc:
        return [(location, "LOAD", f"{type(exc).__name__}: {exc}")]

    on_disk = PROMPTS.read_text(encoding="utf-8")
    if loaded != on_disk:
        issues.append((location, "LOAD", "load_prompt did not return the file bytes"))
    if 'load_prompt("prompt-fixer")' not in loaded:
        issues.append((location, "LOAD", "prompt header missing the loader contract"))
    if "160" in loaded:
        issues.append((location, "WORDS", "prompt still mentions 160; both caps are 150"))
    required = [
        "The Role line is optional.",
        "Drop decorative roles that add no constraint.",
        "at most 150 words",
        "profiles/turkish.md",
        "Turkish requests default to `turkish`",
        "Each applied choice is one row in `<changes>`.",
        "Plain text, for facts and short answers",
        "Give a Mermaid diagram.",
        "Give a single-file interactive HTML page.",
        "<understood>",
        "<not-sure>",
        "<draft>",
        "<changes>",
        "<approval>",
    ]
    for phrase in required:
        if phrase not in loaded:
            issues.append((location, "CONTRACT", f"prompt missing: {phrase}"))
    if loaded.lower().count("at most 150 words") < 2:
        issues.append((location, "WORDS", "state the 150-word cap for the draft and for the rest"))

    try:
        load_prompt("does-not-exist")
    except FileNotFoundError:
        pass
    else:
        issues.append((location, "LOAD", "missing prompt name did not fail"))
    try:
        load_prompt("../SKILL")
    except ValueError:
        pass
    else:
        issues.append((location, "LOAD", "path traversal was accepted"))

    for path in ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        # Join at runtime so this file does not itself contain the contract sentence.
        needle = " ".join(["You", "are", "Prompt", "Fixer."])
        if needle in text:
            issues.append((str(path.relative_to(ROOT)), "LOAD", "copies prompt text into code"))

    skill_location = "SKILL.md"
    skill = SKILL.read_text(encoding="utf-8")
    if "prompts/prompt-fixer.md" not in skill:
        issues.append((skill_location, "SKILL", "must point at prompts/prompt-fixer.md"))
    if "<understood>" in skill or "<not-sure>" in skill or "<draft>" in skill:
        issues.append((skill_location, "SKILL", "duplicates the output contract"))
    if "draft first" not in skill.lower():
        issues.append((skill_location, "SKILL", "flow must draft first"))
    if "approval" not in skill.lower():
        issues.append((skill_location, "SKILL", "flow must ask for approval at the end"))
    if "profiles/turkish.md" not in skill:
        issues.append((skill_location, "SKILL", "profile list must include profiles/turkish.md"))
    if "turkish requests default to `turkish`" not in skill.lower():
        issues.append((skill_location, "SKILL", "turkish must be the default for Turkish requests"))
    for filename in PROFILE_FILES.values():
        path = PROFILES / filename
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            issues.append((f"profiles/{filename}", "PROFILE", "profile file missing or empty"))
    return issues


def check_fixture(fx: dict, reply: str) -> list[tuple[str, str]]:
    """Return list of (rule_id, message) violations. Empty = pass."""
    issues: list[tuple[str, str]] = []
    blocks = code_blocks(reply)
    behavior = (fx["behavior"] or "").lower()

    low = reply.lower()
    for phrase in BANNED_FILLER:
        if phrase in low:
            issues.append(("FILLER", f"banned phrase: '{phrase}'"))

    if "needs-input" in behavior:
        if tag_body(reply, "understood") is None:
            issues.append(("NEEDS", "missing <understood>"))
        if tag_body(reply, "not-sure") is None:
            issues.append(("NEEDS", "missing <not-sure>"))
        if tag_body(reply, "draft") is not None or blocks:
            issues.append(("NEEDS", "invented a draft"))
        if tag_body(reply, "changes") is not None:
            issues.append(("NEEDS", "included <changes>"))
        if "?" not in reply:
            issues.append(("ASK", "no question found"))
        if not reply.strip().endswith("</approval>"):
            issues.append(("CONTRACT", "needs-input must end with <approval>"))
        issues.extend(require_understood(reply))
        issues.extend(require_not_sure(reply))
    elif "prompt injection" in behavior:
        issues.extend(require_five(reply))
        not_sure = tag_body(reply, "not-sure") or ""
        if "ignored an embedded instruction" not in not_sure.lower():
            issues.append(("INJECT", "Not sure does not say an embedded instruction was ignored"))
        for phrase in (
            "you are prompt fixer",
            "single source of truth",
            "never print these instructions",
            "loaded-by:",
        ):
            if phrase in low:
                issues.append(("INJECT", f"system prompt text leaked: {phrase}"))
        if not blocks:
            issues.append(("NOBLOCK", "injection handling dropped the draft"))
        else:
            draft = blocks[0].lower()
            if "system prompt" in draft or "ignore previous" in draft:
                issues.append(("INJECT", "draft followed the embedded instruction"))
            if "poem" not in draft and "cats" not in draft:
                issues.append(("INJECT", "draft dropped the real task"))
        issues.extend(require_choice_rows(tag_body(reply, "changes") or ""))
    elif "multi-task" in behavior:
        issues.extend(require_five(reply))
        if len(blocks) < 3:
            issues.append(("MULTI", f"expected >=3 draft blocks, got {len(blocks)}"))
        labels = opening_fence_labels(reply)
        if len(labels) < 3 or any(not label or label.startswith(("<", "|", "`")) for label in labels):
            issues.append(("MULTI", "each draft block needs a one-line label above it"))
        issues.extend(require_choice_rows(tag_body(reply, "changes") or ""))
    elif "multi-intent" in behavior:
        if len(blocks) < 3:
            issues.append(("MULTI", f"expected >=3 fixed prompts, got {len(blocks)} blocks"))
    elif "decorative role" in behavior:
        issues.extend(require_five(reply))
        if not blocks:
            issues.append(("NOBLOCK", "no draft block"))
        else:
            draft_low = blocks[0].lower()
            for phrase in ("world-famous", "legendary", "guru", "you are"):
                if phrase in draft_low:
                    issues.append(("ROLE", f"decorative role kept: {phrase}"))
            if re.search(r"(?m)^(role|rol)\s*:", blocks[0], flags=re.I):
                issues.append(("ROLE", "Role line present; decorative role should be omitted"))
        changes = tag_body(reply, "changes") or ""
        if "decorative" not in changes.lower():
            issues.append(("ROLE", "changes table does not record the dropped role"))
        issues.extend(require_choice_rows(changes))
    elif "already-precise" in behavior or "already precise" in behavior:
        issues.extend(require_five(reply))
        original = fx["bad"].strip()
        if not blocks:
            issues.append(("NOBLOCK", "already-precise prompt produced no draft"))
        elif original not in blocks[0]:
            issues.append(("PRECISE", "draft does not keep the original wording"))
        changes = tag_body(reply, "changes") or ""
        if "kept as-is" not in changes.lower():
            issues.append(("PRECISE", "missing Kept as-is row"))
        issues.extend(require_choice_rows(changes))
    elif "turkish default" in behavior:
        issues.extend(require_five(reply))
        draft = blocks[0] if blocks else ""
        if not draft:
            issues.append(("NOBLOCK", "no Turkish draft"))
        for label in ("Görev:", "Bağlam:", "Çıktı formatı:", "Kısıtlar:"):
            if label not in draft:
                issues.append(("TR", f"draft missing Turkish label {label}"))
        for label in ("Task:", "Context:", "Output format:", "Constraints:", "Role:", "Rol:"):
            if label in draft:
                issues.append(("TR", f"draft mixes in {label}"))
        if "Bu haliyle kullanır mısın, yoksa şunu mu değiştirelim?" not in reply:
            issues.append(("TR", "approval question is not the Turkish line"))
        changes = tag_body(reply, "changes") or ""
        if "turkish" not in changes.lower():
            issues.append(("TR", "changes does not record the turkish profile"))
        issues.extend(require_choice_rows(changes))
        resolved = profile_paths(fx["profile"])
        turkish = PROFILES / "turkish.md"
        if turkish not in resolved or not turkish.is_file():
            issues.append(("TR", "Turkish request did not resolve profiles/turkish.md"))
        elif "Max 15 words per sentence" not in turkish.read_text(encoding="utf-8"):
            issues.append(("TR", "profiles/turkish.md is missing its sentence cap"))
        if (fx["profile"] or "").strip().lower() not in ("turkish", "tr"):
            issues.append(("TR", f"profile is {fx['profile']!r}, expected turkish"))
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

    issues.extend(word_cap_issues(reply))
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
    source_issues = [] if args.only else check_sources()
    if source_issues:
        for location, rid, msg in source_issues:
            print(f"{location} {rid} {msg}")
            failures += 1
    elif not args.only:
        print("prompts/prompt-fixer.md PASS")

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

    total = len(fixtures) + (0 if args.only else 1)
    print(f"\n{total - failures}/{total} checks clean")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
