<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Agent guidance

## Portable steering

The portable version of this repository's Kiro steering lives in
`.agents/skills/` as [Agent Skills](https://agentskills.io/specification).
Each kebab-case skill is generated from its mapped PascalCase source file in
`.kiro/steering/`.

- Do not edit generated `SKILL.md` files directly. Update the corresponding
  `.kiro/steering/<PascalCaseName>.md` source, then run
  `python tools/skills/MigrateKiroSteering.py --write`.
- Before completing a change to steering, run
  `python tools/skills/MigrateKiroSteering.py --check`.
- Read and follow every skill whose description matches the task before
  changing the associated files. See `.agents/README.md` for the complete
  source-to-skill mapping.

## Always-on project constraints

- Never commit, push, pull into, or otherwise write to `main`. Work only on a
  non-protected working branch.
- Deliver complete, verified work. Do not leave stubs, placeholders, or known
  failures behind.
- Format each changed source file with its project formatter and run focused
  verification before reporting completion.
- Use `uv` rather than `pip` for Python dependency management, except in the
  explicitly exempt `Parashell/` and `modules/` workspaces.
- New non-skill text files must start with the exact notice in `HEADER_NOTICE`.

## Skill routing

| When working on…                                                               | Activate these skills                                                                                                                             |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Any user-facing response or status update                                      | `chats`                                                                                                                                           |
| Any code or related text change                                                | `code-formatting`, `no-stubs`, `spdx-header`                                                                                                      |
| Any source-code structure, declaration, module, or import change               | `split-large-definitions`                                                                                                                         |
| Any file creation, rename, move, import, extension, or security-quality change | `repository-structure`                                                                                                                            |
| A reported error, stack trace, failed test, or broken behavior                 | `fix-errors-dont-ask`                                                                                                                             |
| Git history or a write-capable Git operation                                   | `git-never-touch-main`                                                                                                                            |
| Python dependencies, `pyproject.toml`, `uv.lock`, or Python CI                 | `python-package-manager`                                                                                                                          |
| GitHub Actions or runner configuration                                         | `pin-dependencies`                                                                                                                                |
| `pixi.toml`                                                                    | `pixi-lockfiles`                                                                                                                                  |
| MCP tool definitions or their Mintlify documentation                           | `compact-tool-descriptions`, `mcp-tool-doc-pages`                                                                                                 |
| CAD parsing, conversion, writing, or translation verification                  | `no-cad-runtime`, `no-donor-blocks`, `lossless-translation`                                                                                       |
| React, Next.js, UI components, pages, styles, or layouts                       | `frontend-stack`, `component-architecture`, `design-system-discipline`, `layout-system`, `no-unrequested-styling`, `react-doctor`, `shadcn-pages` |
| Public landing or marketing page metadata                                      | `page-title-separator`                                                                                                                            |
| HostControl services or contracts                                              | `hostcontrol-contract`                                                                                                                            |
| WorkOS token validation in `backend/**/*.py`                                   | `workos-token-verification`                                                                                                                       |
| Work that must be tracked in Linear                                            | `linear-issue-tracking`                                                                                                                           |

## Agent Skills SPDX exception

`SKILL.md` files must begin with their required YAML frontmatter to remain
Agent Skills-compatible. For `.agents/skills/**/SKILL.md`, use the required
`license: LicenseRef-PolyForm-Strict-1.0.0` frontmatter field instead of
placing the normal comment notice before the frontmatter. All other new files
continue to use the exact `HEADER_NOTICE` block.
