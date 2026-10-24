# Harness

Runs `tests/fixtures.md` against a model whose system prompt is `prompts/prompt-fixer.md` loaded at runtime by `prompt_loader.load_prompt("prompt-fixer")`, plus `SKILL.md` for the flow and profile list.

## Quick start

```bash
# real model (needs API key)
ANTHROPIC_API_KEY=sk-ant-... python harness/run_tests.py --provider anthropic
OPENAI_API_KEY=sk-...     python harness/run_tests.py --provider openai --model gpt-4.1

# offline replay (CI-safe, no network). Same as --provider mock.
python harness/run_tests.py --provider recorded --recordings harness/recorded/

# real OpenAI-compatible call. The key is read from the named env var.
# Recordings store model, UTC timestamp, and response id from the API.
python harness/run_tests.py --provider openai-compatible \
  --base-url https://api.openai.com/v1 --model gpt-4.1 \
  --key-env OPENAI_API_KEY --record harness/recorded/
```

`harness/recorded/1.txt` through `26.txt` are the reply per fixture. Files that were not produced by the provider above are marked `status: unverified` and carry no model, timestamp, or response id.

Run only some fixtures: `--only 13 14 20`.

## What it checks (deterministic, no LLM-as-judge)

| rule | check |
|------|-------|
| FILLER | banned phrases from `lint/ste-lint.md` absent in the reply |
| NOBLOCK / WORDS | fixed prompt produced; each draft block <= 150 words; the rest of the reply <= 150 words |
| ASK / SILENTGUESS | ambiguous or contradictory entries get exactly one question, not a prompt |
| MULTI | multi-intent and multi-task entries yield >= 3 drafts; multi-task also needs a label on each block |
| TOUCH | already-good prompts are not rewritten |
| NEEDS | needs-input entries have no draft and no changes table |
| INJECT | embedded instructions are ignored, named in Not sure, and the real task is still drafted |
| TR | Turkish entries use Turkish labels, the Turkish approval line, `profiles/turkish.md`, and sentences of at most 15 words |
| PRECISE | already-precise entries keep the original wording and a Kept as-is row |
| ROLE | a `Role:` / `Rol:` label anywhere in the draft fails; the drop is a changes row |
| LOAD | `load_prompt("prompt-fixer")` returns the prompt file and Python does not inline it |
| PROVENANCE | a replay is `status: unverified`, or it has model, UTC timestamp, and response id |

Output mimics ste-lint: `fixtures.md:20 ASK no clarifying question found`.
Exit code: 1 if any violation, 0 if clean.

## Recording mode

`--provider openai-compatible` sends `load_prompt("prompt-fixer")` as the system message and writes `<record>/<n>.txt`:

```
model: <response model, else the requested model>
timestamp: <response created, else receipt time, UTC>
response_id: <response id>
```

The writer raises if the response has no id. It does not fill in a placeholder. CI runs `--provider recorded` on pull requests (`.github/workflows/harness.yml`).

Kill-check the review mutants with `python3 harness/run_mutants.py`.
