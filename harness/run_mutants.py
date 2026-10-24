#!/usr/bin/env python3
"""Re-run review mutants M1-M6 against the harness. Each one must die.

M1  A recording with no provenance header is accepted.
M2  The CI workflow does not run the recorded harness.
M3  A Turkish reply keeps a sentence over 15 words.
M4  A decorative Role line in the draft is accepted.
M5  The OpenAI-compatible system prompt is a hardcoded string.
M6  The recorder invents a response id when the API omits one.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import run_tests as rt

ROOT = Path(__file__).resolve().parent.parent
RECORDED = ROOT / "harness" / "recorded"
HARNESS = [sys.executable, str(ROOT / "harness" / "run_tests.py")]


def run_recorded(directory: Path, only: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*HARNESS, "--provider", "recorded", "--recordings", str(directory), "--only", str(only)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def show(name: str, proc: subprocess.CompletedProcess[str]) -> int:
    print(f"===== {name} =====")
    print(proc.stdout, end="" if proc.stdout.endswith("\n") or not proc.stdout else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n")
    print(f"exit: {proc.returncode}")
    if proc.returncode == 0:
        print(f"{name} SURVIVED")
        return 1
    print(f"{name} DIED")
    return 0


def mutant_m1() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        shutil.copy(RECORDED / "21.txt", dest / "21.txt")
        text = (dest / "21.txt").read_text(encoding="utf-8")
        _meta, body = rt.split_recording(text)
        (dest / "21.txt").write_text(body, encoding="utf-8")
        return show("M1 headerless-recording", run_recorded(dest, 21))


def mutant_m2() -> int:
    broken = "name: harness\non:\n  pull_request:\njobs:\n  recorded:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo skip\n"
    print("===== M2 ci-without-harness =====")
    issues = rt.check_ci(broken)
    for rule_id, message in issues:
        print(f".github/workflows/harness.yml {rule_id} {message}")
    if not issues:
        print("M2 SURVIVED")
        return 1
    print("M2 DIED")
    return 0


def mutant_m3() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        shutil.copy(RECORDED / "24.txt", dest / "24.txt")
        text = (dest / "24.txt").read_text(encoding="utf-8")
        text = text.replace(
            "Görev: Müşteri destek ekibi için iade politikasını açıkla.",
            "Görev: Müşteri destek ekibi için iade politikasını tek bir çok uzun cümlede bütün koşullar süre kanal ve istisnalar ile birlikte anlat ve on beş kelime sınırını bilerek aş.",
        )
        (dest / "24.txt").write_text(text, encoding="utf-8")
        return show("M3 turkish-sentence-over-15", run_recorded(dest, 24))


def mutant_m4() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        shutil.copy(RECORDED / "26.txt", dest / "26.txt")
        text = (dest / "26.txt").read_text(encoding="utf-8")
        text = text.replace(
            "Task: Explain connection pooling.",
            " Role: Expert assistant.\nTask: Explain connection pooling.",
        )
        (dest / "26.txt").write_text(text, encoding="utf-8")
        return show("M4 decorative-role-line", run_recorded(dest, 26))


def mutant_m5() -> int:
    print("===== M5 hardcoded-system-prompt =====")
    contract = rt.load_prompt("prompt-fixer")
    real = rt.openai_compatible_payload(contract, "fix this", "demo-model")
    mutant = rt.openai_compatible_payload("You are a helpful assistant.", "fix this", "demo-model")
    real_system = real["messages"][0]["content"]
    mutant_system = mutant["messages"][0]["content"]
    print(f"real system is load_prompt: {real_system == contract}")
    print(f"mutant system is load_prompt: {mutant_system == contract}")
    if mutant_system == contract:
        print("M5 SURVIVED")
        return 1
    print("M5 DIED: openai-compatible system prompt is not load_prompt output")
    return 0


def mutant_m6() -> int:
    print("===== M6 invented-response-id =====")
    response = {"choices": [{"message": {"content": "hello"}}], "model": "demo-model"}
    try:
        written = rt.format_recording(response, "demo-model")
    except ValueError as exc:
        print(f"ValueError: {exc}")
        print("M6 DIED")
        return 0
    print(written)
    print("M6 SURVIVED")
    return 1


def main() -> int:
    failures = 0
    for mutant in (mutant_m1, mutant_m2, mutant_m3, mutant_m4, mutant_m5, mutant_m6):
        failures += mutant()
        print()
    print(f"{6 - failures}/6 mutants died")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
