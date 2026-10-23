# Before / After examples

## ste80 (default)

Before: > hey can you maybe help me understand why my queries are slow, it's kind of confusing

Format: plain text.

```
Explain why these queries are slow.
Context: Postgres 16, `users` table has 2M rows, no index on `email`.
Name each cause in one bullet. Max 5 bullets.
For each cause give one fix with the exact SQL.
```

## cte

Before: > how do i set up the ci pipeline for the api

Format: plain text.

```
Write a procedure to set up CI for the API.
Structure: purpose, prerequisites, steps, verification, rollback.
One action per step. Warnings before steps that can fail.
Verification must include one command and its expected output.
```

## globish

Before: > write onboarding docs for our new hires in 3 countries

Format: plain text.

```
Write onboarding docs for new hires in 3 countries.
Use only common international English. No idioms. Max 15 words per sentence.
Dates as ISO (2026-10-23). Units explicit.
Structure: day 1 setup, tools, contacts, first task.
```

## diagram format

Before: > explain our auth flow

Format: diagram.

```
Explain our auth flow: login, token refresh, logout.
Give a Mermaid diagram. Sequence diagram, not flowchart.
List each request with method and path. Max 12 steps.
```
