# Harness

Runs `tests/fixtures.md` against a model whose system prompt is `prompts/prompt-fixer.md` loaded at runtime by `prompt_loader.load_prompt("prompt-fixer")`, plus `SKILL.md` for the flow and profile list.

## Quick start

```bash
# real model (needs API key)
ANTHROPIC_API_KEY=sk-ant-... python harness/run_tests.py --provider anthropic
OPENAI_API_KEY=sk-...     python harness/run_tests.py --provider openai --model gpt-4.1

# offline replay (CI-safe, no network)
python harness/run_tests.py --provider mock --mock harness/recorded/
# layout: harness/recorded/1.txt ... 26.txt = the recorded model reply per fixture
```

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
| TR | Turkish entries use Turkish labels, the Turkish approval line, and `profiles/turkish.md` |
| PRECISE | already-precise entries keep the original wording and a Kept as-is row |
| ROLE | decorative roles are omitted and the drop is a changes row |
| LOAD | `load_prompt("prompt-fixer")` returns the prompt file and Python does not inline it |

Output mimics ste-lint: `fixtures.md:20 ASK no clarifying question found`.
Exit code: 1 if any violation, 0 if clean.

## Recording mode

No recorder built yet. To make mock fixtures: run once against a model, save each reply to `<n>.txt`. A `--record` flag is a welcome PR.
