# Contributing

One fixture per PR. Keep it small.

## Fixture format

```
NN. bad: "<raw user prompt, as messy as reality>"
    profile: <profile name, only when not default>
    context: <environment facts, only when relevant>
    fixed: "<the rewritten prompt>"
```

Or, for behavior tests (ambiguity, multi-intent, already-good):

```
NN. bad: "..."
    expected skill behavior: <what the skill does instead of a rewrite>
```

## Rules for a good fixture

- The bad prompt must look real. Typos, filler, mixed intent, urgency noise.
- The fixed prompt must obey the named profile. Check word counts.
- One fixture tests one idea. Do not bundle multi-intent + ambiguity.
- If the fixture fails against the current SKILL.md, say so in the PR body. The fixture doc is a spec, not a bug log.
- Numbering is append-only. Do not renumber old entries.

## Profiles that need more fixtures (open spots)

- globish: 1 -> needs API-error-message case
- cte: 2 -> needs migration-failure case
- tr: 2 -> needs customer-support case
- conventions: 1 -> needs llms.txt case

Thanks for helping hit 50.
