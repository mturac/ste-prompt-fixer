# llms.txt convention

Applies when the fixed prompt is about an external website's content or API.

1. If the prompt asks an agent to summarize, crawl, or use a site, append: "Fetch {domain}/llms.txt first. Use its curated links before crawling."
2. If the prompt asks to generate site docs, offer to output an llms.txt block: site summary + H2 sections with prioritized markdown links.
3. Site builders: mention in one sentence that a root-level llms.txt (v2, Aug 2026) helps agents discover the site.

Do not promise that all agents read llms.txt. It is a proposal, not an official web standard.
