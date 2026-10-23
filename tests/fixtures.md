# Test fixtures — bad prompt -> fixed prompt

Goal: 50 entries. Seed set below. Add one per PR, keep the format.
Format per entry: `bad` / profile / `fixed`. Fixed prompts follow the profile rules.

## ste80

1. bad: "hey can u tell me about websocket vs sse thx"
   fixed: "Compare WebSocket and SSE. One table, 5 rows max, latency and use case columns. End with one verdict sentence. Max 200 words."

2. bad: "you are a 10x engineer explain kubernetes scheduling to me urgently"
   fixed: "Explain the Kubernetes scheduler. Audience: dev who knows pods, not nodes. Structure: one diagram idea, then 3 numbered steps of the scheduling flow. Max 250 words."

3. bad: "write something nice about our new api for the blog"
   fixed: "Describe the new API for a blog post. Audience: backend devs. List exactly 3 changes and each one's user benefit. No superlatives. Max 150 words."

## cte

4. bad: "migrate db somewhere safer pls"
   fixed: "Write a procedure to migrate the Postgres DB to the new host. Include: prerequisites, steps with one action each, verification command, rollback. Warning before any data-touching step."

5. bad: "how do i undo a bad deploy"
   fixed: "Write a rollback procedure for a bad deploy on our CI. Steps with verbs first. Verification: one command + expected output. Rollback of the rollback: none assumed; say so."

## globish

6. bad: "onboarding doc for indonesia + vietnam hires eng stuff"
   fixed: "Write onboarding docs for hires in Indonesia and Vietnam. Common international English only, 1500-word ceiling. No idioms. Max 15 words/sentence. Dates ISO. Structure: day 1 setup, tools, contacts, first task."

## plain

7. bad: "changelog blurb for v2.3 nothing fancy"
   fixed: "Write the changelog for v2.3. Max 20 words per sentence. Everyday words; define any jargon inline. One line per change: what it is, who benefits."

## tr

8. bad: "sitemiz icin super dinamik yenilikci blog yazisi hazirlaa"
   fixed: "Blog yazisi icin giris metni yaz. Turkce. En fazla 15 kelime/cumle. 'Son derece' ve 'dinamik' gibi bos sifatlar yok. Sayilar rakamla. Teknik terimler Ingilizce kalsin. Max 200 kelime."

9. bad: "kodum bozuk bi bak"
   fixed: "Kodu incele. Hatanin nedenini tek cumlede soyle once. Sonra en fazla 3 cozum adimi, emir kipiyle. Kod bloklarina dokunma, sadece isaret et. Turkce."

## format: diagram

10. bad: "explain the auth thing"
    fixed: "Explain our auth flow: login, refresh, logout. Mermaid sequence diagram, not flowchart. Each request: method + path. Max 12 steps."

## format: html

11. bad: "make me understand entropy"
    fixed: "Explain entropy for a dev who knows probability basics. Single-file interactive HTML. One draggable demo. Text follows ste80: max 15 words per sentence."

## conventions: AGENTS.md present

12. bad: "fix the flaky test"
    context: repo AGENTS.md says `pnpm test:unit`, no new deps.
    fixed: "Fix the flaky test in `api/user.test.ts`. Follow AGENTS.md: run `pnpm test:unit`, add no new dependencies. First state the root cause in one sentence, then the minimal diff."

## ambiguous (ask one question)

13. bad: "make it faster"
    expected skill behavior: ask one question — "What is 'it', and what metric defines faster?" Do not guess.

14. bad: "summarize this" (no attachment)
    expected skill behavior: ask one question naming the missing input.
