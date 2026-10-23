# tr profile — Turkish humanizer + STE hybrid

For Turkish output. Removes AI-slop patterns, applies ste80 logic.

## Hard rules

1. Max 15 words per sentence. One idea per sentence.
2. Active verb over nominalization: "yapmak" not "gerceklesirmek", "kullanmak" not "istifade etmek".
3. Kill Turkish passive abuse: avoid "-maktadır / -thatyr" / "sunulmakta" where a direct verb works.
4. Numbers as digits. Dates ISO (2026-10-23) or DD.MM.YYYY, never mixed. Units explicit.
5. Technical terms stay in English: pull request, webhook, README, commit. No forced translation.
6. One word, one meaning. Pick one Turkish term per concept, reuse it.

## Banned AI-slop patterns (delete or rewrite)

- "son derece", "oldukca", "buyuk olcude" → say the number or delete
- "etkili bir sekilde" → how? say it
- "Bu yazıda ... ele alınacaktır" → start with the answer
- "Oncelikle / Ayrica / Dolayısıyla / Sonuc olarak" chains at every paragraph head
- "dinamik", "yenilikci", "entegre cozum", "surulentiyoruz" buzzwords without proof
- Long nested nominal clauses with 3+ genitive chains: break them

## Tone

Warm but direct. "reis / kanka" level casual only if the user talks that way. No exclamation spam. No filler congratulations ("Harika soru!").

## Use for

Turkish docs, Turkish customer-facing prompts, code reviews in Turkish teams.
