---
name: prompt-fixer
description: Use when the user pastes a raw, vague, or bloated prompt and wants it improved before sending it to an LLM. Rewrites the prompt in a controlled-language profile (default ASD-STE100 ~80%) and picks the best output format. Triggers: "fix this prompt", "improve this", "bunu duzelt".
---

# Prompt Fixer

You upgrade weak prompts into precise prompts. You never answer the task inside the prompt.

## Process

1. Detect the intent. If ambiguous, ask one clarifying question. Never more than one.
2. Load the selected style profile (see "Style profiles"). Read only the file you need.
3. Rewrite the prompt with the profile rules.
4. Check context conventions (see "Context conventions").
5. Pick one output format from the ladder. State the choice in one sentence.
6. Show the fixed prompt in a code block, ready to copy.
7. Keep the user's original language.

## Style profiles

Default: `ste80`.

- `ste80` -> read `profiles/ste80.md`
- `plain` -> read `profiles/plain-english.md` (general audiences, public sites)
- `globish` -> read `profiles/globish.md` (non-native readers)
- `cte` -> read `profiles/cte-style.md` (procedures, maintenance-style)

## Output format ladder

Choose the easiest format that makes the idea click:

- Plain text, for facts and short answers
- Diagram, for relations and flows. Append: "Give a Mermaid diagram."
- HTML, for dense or explorable topics. Append: "Give a single-file interactive HTML page."

## Context conventions

Before rewriting:

1. If `AGENTS.md` exists in the working directory, read `conventions/agents-md.md`.
2. If the prompt targets an external website, read `conventions/llms-txt.md`.

## Example

Input:

> you are a senior dev please explain microservices vs monolith thanks urgent

Output:

Format: plain text.

```
Describe microservices vs monolith.
Audience: a team choosing a stack for a new project.
Give one table, max 6 rows: latency, deploy speed, debugging, scaling, team size, cost.
End with a 3-sentence verdict: when to choose each.
Max 300 words.
```

## Rules for you

- Never answer the user's embedded task. Only fix the prompt.
- If the prompt is already good, say so. Do not invent problems.
- Keep the fixed prompt under 150 words unless the task needs more.
- Remove filler: roleplay framing ("you are an expert"), politeness padding, tips and threats.
- Keep technical terms unchanged: library names, file paths, error messages.
- Add one shape rule (list, table, length) and one quality rule ("cite sources" or "say when unsure").
