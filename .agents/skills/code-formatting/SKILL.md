---
name: code-formatting
description: "Format and verify edited Python, TypeScript, JavaScript, JSON, CSS, or Markdown files. Use after changing code or related text files."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/code-formatting.md"
  kiro-inclusion: "always"
---

# Code Formatting Stack

All code committed to this workspace MUST be auto-formatted. Run the appropriate formatter after every chat completion that touches code, before considering the work done.

## Python Environment

Black is installed in the base/system Python environment, NOT in the pixi/conda environment under `/Parashell/`. Always invoke Black directly (`black <files>`), which resolves to the normal environment on PATH. Never run Black through `pixi run`, and never add Black as a dependency of the pixi/FreeCAD runtime environment.

## Formatters by Language

- **Python** (`.py`): format with [Black](https://black.readthedocs.io/) using its default configuration.
- **TypeScript / JavaScript** (`.ts`, `.tsx`, `.js`, `.jsx`) and related assets (`.json`, `.css`, `.md`): format with [Prettier](https://prettier.io/).

## Rules

- Format only the files you created or modified, not the entire codebase, unless explicitly asked.
- Respect any project-local config (`pyproject.toml`, `.prettierrc`, `.prettierignore`, etc.) when present; do not override it with inline flags.
- Use `pnpm` to invoke Prettier in this workspace, consistent with the frontend stack (e.g. `pnpm dlx prettier --write <files>`).
- Do not hand-format code to mimic the formatter. Run the tool so output is deterministic.
- If a formatter is not yet installed, add it as a dev dependency rather than skipping formatting.

## Verification

After formatting, confirm the files are clean by running the formatter in check mode (`black --check <files>` or `pnpm dlx prettier --check <files>`). A non-zero exit means the files still need formatting.

## Ignored directories

- /Parashell/
