# Harness

Runs `tests/fixtures.md` against a model that has `SKILL.md` loaded.

## Quick start

```bash
# real model (needs API key)
ANTHROPIC_API_KEY=sk-ant-... python harness/run_tests.py --provider anthropic
OPENAI_API_KEY=sk-...     python harness/run_tests.py --provider openai --model gpt-4.1

# offline replay (CI-safe, no network)
python harness/run_tests.py --provider mock --mock harness/recorded/
# layout: harness/recorded/01.txt ... 20.txt = the recorded model reply per fixture
```

Run only some fixtures: `--only 13 14 20`.

## What it checks (deterministic, no LLM-as-judge)

| rule | check |
|------|-------|
| FILLER | banned phrases from `lint/ste-lint.md` absent in the reply |
| NOBLOCK / WORDS | fixed prompt produced, longest block <= 160 words |
| ASK / SILENTGUESS | ambiguous or contradictory entries get exactly one question, not a prompt |
| MULTI | multi-intent entries yield >= 3 fixed prompts |
| TOUCH | already-good prompts are not rewritten |

Output mimics ste-lint: `fixtures.md:20 ASK no clarifying question found`.
Exit code: 1 if any violation, 0 if clean.

## Recording mode

No recorder built yet. To make mock fixtures: run once against a model, save each reply to `<n>.txt`. A `--record` flag is a welcome PR.
