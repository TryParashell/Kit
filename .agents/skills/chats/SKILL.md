---
name: chats
description: "Apply the concise chat-response policy. Use when preparing any user-facing response, progress update, or completion summary."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/Chats.md"
  kiro-inclusion: "always"
---

# Chat Policy

Keep all chat responses highly concise.

## Core Rules

- Do not narrate your reasoning or thought process while solving a problem. Acknowledge briefly (e.g. "Working on it"), then act.
- When fixing a problem, report only after you are done: state the fix and the root cause in under 100 words.
- Do not over-explain. Omit background the user already knows.
- Default to the shortest response that fully answers the request. Add detail only when explicitly asked.

## Formatting

- Use prose for short answers; reserve bullet points for genuine lists or sequences.
- Show code or commands directly instead of describing them in words.
- Skip filler acknowledgments and restating the question.
