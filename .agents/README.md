<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Portable agent skills

This directory is the Agent Skills-compatible copy of `.kiro/steering/`.
It uses the open [Agent Skills specification](https://agentskills.io/specification):
each task-scoped rule is a directory under `.agents/skills/` with a
schema-valid `SKILL.md` containing `name`, `description`, and Markdown
instructions.

The repository-root `AGENTS.md` is the small, always-on router. It makes the
portable skill set discoverable to agents that read `AGENTS.md`, while the
individual skill descriptions support progressive, task-specific activation.

## Maintenance

`.kiro/steering/` is the source of truth for the migrated rule bodies. To
refresh the copy after changing a source rule, run:

```bash
python tools/migrate_kiro_steering.py --write
python tools/migrate_kiro_steering.py --check
```

`--write` removes skill directories that are no longer represented by the
source mapping, while `--check` reports them. `--check` is also covered by
`tests/test_agent_skills_migration.py`, preventing the two trees from silently
drifting.

## Mapping

| Kiro steering source                          | Agent Skill                                         |
| --------------------------------------------- | --------------------------------------------------- |
| `.kiro/steering/chats.md`                     | `.agents/skills/chats/SKILL.md`                     |
| `.kiro/steering/code-formatting.md`           | `.agents/skills/code-formatting/SKILL.md`           |
| `.kiro/steering/compact-tool-descriptions.md` | `.agents/skills/compact-tool-descriptions/SKILL.md` |
| `.kiro/steering/component-architecture.md`    | `.agents/skills/component-architecture/SKILL.md`    |
| `.kiro/steering/design-system-discipline.md`  | `.agents/skills/design-system-discipline/SKILL.md`  |
| `.kiro/steering/fix-errors-dont-ask.md`       | `.agents/skills/fix-errors-dont-ask/SKILL.md`       |
| `.kiro/steering/frontend-stack.md`            | `.agents/skills/frontend-stack/SKILL.md`            |
| `.kiro/steering/git-never-touch-main.md`      | `.agents/skills/git-never-touch-main/SKILL.md`      |
| `.kiro/steering/hostcontrol-contract.md`      | `.agents/skills/hostcontrol-contract/SKILL.md`      |
| `.kiro/steering/identifier-markers.md`        | `.agents/skills/identifier-markers/SKILL.md`        |
| `.kiro/steering/layout-system.md`             | `.agents/skills/layout-system/SKILL.md`             |
| `.kiro/steering/linear-issue-tracking.md`     | `.agents/skills/linear-issue-tracking/SKILL.md`     |
| `.kiro/steering/lossless-translation.md`      | `.agents/skills/lossless-translation/SKILL.md`      |
| `.kiro/steering/mcp-tool-doc-pages.md`        | `.agents/skills/mcp-tool-doc-pages/SKILL.md`        |
| `.kiro/steering/naming-convention.md`         | `.agents/skills/naming-convention/SKILL.md`         |
| `.kiro/steering/no-cad-runtime.md`            | `.agents/skills/no-cad-runtime/SKILL.md`            |
| `.kiro/steering/no-donor-blocks.md`           | `.agents/skills/no-donor-blocks/SKILL.md`           |
| `.kiro/steering/no-stubs.md`                  | `.agents/skills/no-stubs/SKILL.md`                  |
| `.kiro/steering/no-unrequested-styling.md`    | `.agents/skills/no-unrequested-styling/SKILL.md`    |
| `.kiro/steering/page-title-separator.md`      | `.agents/skills/page-title-separator/SKILL.md`      |
| `.kiro/steering/pin-dependencies.md`          | `.agents/skills/pin-dependencies/SKILL.md`          |
| `.kiro/steering/pixi-lockfiles.md`            | `.agents/skills/pixi-lockfiles/SKILL.md`            |
| `.kiro/steering/python-package-manager.md`    | `.agents/skills/python-package-manager/SKILL.md`    |
| `.kiro/steering/rationale-comments.md`        | `.agents/skills/rationale-comments/SKILL.md`        |
| `.kiro/steering/react-doctor.md`              | `.agents/skills/react-doctor/SKILL.md`              |
| `.kiro/steering/shadcn-pages.md`              | `.agents/skills/shadcn-pages/SKILL.md`              |
| `.kiro/steering/spdx-header.md`               | `.agents/skills/spdx-header/SKILL.md`               |
| `.kiro/steering/workos-token-verification.md` | `.agents/skills/workos-token-verification/SKILL.md` |

The migration keeps each source body verbatim after removing only Kiro-specific
frontmatter. The Agent Skills frontmatter preserves the original Kiro inclusion
metadata under `metadata` for traceability.
