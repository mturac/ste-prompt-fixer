# ste-lint — lint LLM output like code

Apply to any answer the model produced. Flag violations, do not silently rewrite.

## Rules (each has a severity)

| id | rule | check | severity |
|----|------|-------|----------|
| LEN | sentence length | > 20 words (proc) / > 15 (explainer) | warn |
| PASS | passive | `\b(is|are|was|were|being|been)\s+\w+(ed|en)\s+by\b`, `should be \w+(ed|en)` | warn |
| FILLER | AI-slop phrases | see list below | error |
| NEST | genitive chains (TR) | 3+ consecutive genitive suffixes (non-fiction) | warn |
| ONE | one idea per sentence | sentence contains 2+ clauses with `, (and|but) ` | warn |
| TERM | term drift | same concept named 2+ ways | error |
| DATE | date format | dates not in ISO or DD.MM.YYYY | warn |

## Filler list (error on match)

EN: it is worth noting, in conclusion, moreover, furthermore, delve into, tapestry, ever-evolving, leverage, seamless, robust, cutting-edge, in today's fast-paced world, unlock, unleash, elevate, harness, supercharge, revolutionize, game-changer

try: son derece, buyuk olcude, etkili bir sekilde, bu yazida ele alinacaktir, dinamik cozum, yenilikci yaklasim

## Hook example (pre-commit / CI)

```bash
# lint README-ish md files against FILLER
grep -EIn "(worth noting|delve|tapestry|ever-evolving|in today's fast-paced world|game-changer)" docs/*.md && exit 1
```

Prettier config sample:

```yaml
# .ste-lint.yml
severity: { FILLER: error, LEN: warn }
max_sentence_words: 20
locale: [en, tr]
```

## Output style

Report like a linter: `file.md:12 LEN 26 words`. No lecture, no suggestions unless asked.
