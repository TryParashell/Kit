---
name: compact-tool-descriptions
description: "Write compact agent-facing tool descriptions. Use when adding or editing an MCP or agent tool schema, manifest, or tool documentation."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/compact-tool-descriptions.md"
  kiro-inclusion: "always"
---
# compact tool descriptions

Tool descriptions are loaded into agent context and must stay tiny

- keep every tool description lowercase
- use one sentence with 15 words or fewer
- omit ending punctuation
- avoid special symbols unless required by an identifier
- prefer verb noun phrasing such as create sketch
- do not include examples argument details warnings or workflow notes
- move operational guidance into docs outside loaded tool descriptions
