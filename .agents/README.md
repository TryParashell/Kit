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
python tools/skills/MigrateKiroSteering.py --write
python tools/skills/MigrateKiroSteering.py --check
```

`--write` removes skill directories that are no longer represented by the
source mapping, while `--check` reports them. `--check` is also covered by
`tests/steering/AgentSkillsMigrationTests.py`, preventing the two trees from silently
drifting.

## Mapping

| Kiro steering source                        | Agent Skill                                         |
| ------------------------------------------- | --------------------------------------------------- |
| `.kiro/steering/Chats.md`                   | `.agents/skills/chats/SKILL.md`                     |
| `.kiro/steering/CodeFormatting.md`          | `.agents/skills/code-formatting/SKILL.md`           |
| `.kiro/steering/CompactToolDescriptions.md` | `.agents/skills/compact-tool-descriptions/SKILL.md` |
| `.kiro/steering/ComponentArchitecture.md`   | `.agents/skills/component-architecture/SKILL.md`    |
| `.kiro/steering/DesignSystemDiscipline.md`  | `.agents/skills/design-system-discipline/SKILL.md`  |
| `.kiro/steering/FixErrorsDontAsk.md`        | `.agents/skills/fix-errors-dont-ask/SKILL.md`       |
| `.kiro/steering/FrontendStack.md`           | `.agents/skills/frontend-stack/SKILL.md`            |
| `.kiro/steering/GitNeverTouchMain.md`       | `.agents/skills/git-never-touch-main/SKILL.md`      |
| `.kiro/steering/HostcontrolContract.md`     | `.agents/skills/hostcontrol-contract/SKILL.md`      |
| `.kiro/steering/IdentifierMarkers.md`       | `.agents/skills/identifier-markers/SKILL.md`        |
| `.kiro/steering/LayoutSystem.md`            | `.agents/skills/layout-system/SKILL.md`             |
| `.kiro/steering/LinearIssueTracking.md`     | `.agents/skills/linear-issue-tracking/SKILL.md`     |
| `.kiro/steering/LosslessTranslation.md`     | `.agents/skills/lossless-translation/SKILL.md`      |
| `.kiro/steering/McpToolDocPages.md`         | `.agents/skills/mcp-tool-doc-pages/SKILL.md`        |
| `.kiro/steering/NamingConvention.md`        | `.agents/skills/naming-convention/SKILL.md`         |
| `.kiro/steering/NoCadRuntime.md`            | `.agents/skills/no-cad-runtime/SKILL.md`            |
| `.kiro/steering/NoDonorBlocks.md`           | `.agents/skills/no-donor-blocks/SKILL.md`           |
| `.kiro/steering/NoStubs.md`                 | `.agents/skills/no-stubs/SKILL.md`                  |
| `.kiro/steering/NoUnrequestedStyling.md`    | `.agents/skills/no-unrequested-styling/SKILL.md`    |
| `.kiro/steering/PageTitleSeparator.md`      | `.agents/skills/page-title-separator/SKILL.md`      |
| `.kiro/steering/PinDependencies.md`         | `.agents/skills/pin-dependencies/SKILL.md`          |
| `.kiro/steering/PixiLockfiles.md`           | `.agents/skills/pixi-lockfiles/SKILL.md`            |
| `.kiro/steering/PythonPackageManager.md`    | `.agents/skills/python-package-manager/SKILL.md`    |
| `.kiro/steering/RationaleComments.md`       | `.agents/skills/rationale-comments/SKILL.md`        |
| `.kiro/steering/ReactDoctor.md`             | `.agents/skills/react-doctor/SKILL.md`              |
| `.kiro/steering/RepositoryStructure.md`     | `.agents/skills/repository-structure/SKILL.md`      |
| `.kiro/steering/ShadcnPages.md`             | `.agents/skills/shadcn-pages/SKILL.md`              |
| `.kiro/steering/SplitLargeDefinitions.md`   | `.agents/skills/split-large-definitions/SKILL.md`   |
| `.kiro/steering/SpdxHeader.md`              | `.agents/skills/spdx-header/SKILL.md`               |
| `.kiro/steering/WorkosTokenVerification.md` | `.agents/skills/workos-token-verification/SKILL.md` |

The migration keeps each source body verbatim after removing only Kiro-specific
frontmatter. The Agent Skills frontmatter preserves the original Kiro inclusion
metadata under `metadata` for traceability.
