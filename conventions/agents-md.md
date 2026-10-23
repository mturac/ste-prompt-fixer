# AGENTS.md convention

If the working directory has an `AGENTS.md`, the fixed prompt must respect it.

1. Read it. Extract: build steps, test commands, code style, boundaries, PR rules.
2. If the raw prompt conflicts with a rule in AGENTS.md, rewrite the prompt to follow the rule. Note the change in one sentence.
3. If the prompt targets a coding agent (Codex, Cursor, Claude Code), append a line so the agent's answer follows AGENTS.md. Example: "Follow the repo AGENTS.md: tests with `pnpm test`, no new deps without a note."
4. If no AGENTS.md exists and the user maintains a repo, offer in one sentence to draft an AGENTS.md skeleton.

Do not silently drop repo rules. Surface conflicts instead.
