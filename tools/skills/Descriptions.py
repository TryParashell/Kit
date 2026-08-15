# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

# task triggers stay centralized because generated frontmatter must remain deterministic across runtimes
KDescriptions = {
    "chats": "Apply the concise chat-response policy. Use when preparing any user-facing response, progress update, or completion summary.",
    "code-formatting": "Format and verify edited Python, TypeScript, JavaScript, JSON, CSS, or Markdown files. Use after changing code or related text files.",
    "compact-tool-descriptions": "Write compact agent-facing tool descriptions. Use when adding or editing an MCP or agent tool schema, manifest, or tool documentation.",
    "component-architecture": "Apply React and Next.js component architecture rules. Use when editing TSX, JSX, React components, hooks, or frontend component structure.",
    "design-system-discipline": "Apply shared design-system primitives and UI composition rules. Use when designing or modifying React or Next.js pages, views, or components.",
    "fix-errors-dont-ask": "Investigate, fix, and verify reported errors, failures, stack traces, broken behavior, or failing tests without stopping at diagnosis.",
    "frontend-stack": "Use the required Next.js, React, shadcn, and frontend stack. Use when scaffolding, upgrading, or changing frontend applications.",
    "git-never-touch-main": "Protect the main branch. Use before any Git commit, push, pull, merge, rebase, reset, cherry-pick, or revert operation.",
    "hostcontrol-contract": "Keep HostControl services, schemas, tests, documentation, and consumers synchronized. Use when changing a HostControl service contract.",
    "identifier-markers": "Prefix boolean-returning functions and methods with Is, Has, or Can. Use when naming or renaming any function or method that returns a bool.",
    "layout-system": "Use existing global layout primitives and avoid hand-rolled layout. Use when changing React or Next.js page layout, shells, or spacing.",
    "linear-issue-tracking": "Track work end-to-end in Linear. Use when starting, updating, or completing a task that requires a Linear issue workflow.",
    "lossless-translation": "Hold every format translation to lossless, vendor loadable, application usable, and parametric output verified in the target application. Use when converting between CAD formats or reporting translation results.",
    "mcp-tool-doc-pages": "Document agent-facing MCP tools with standalone Mintlify pages. Use when creating or changing MCP tools or their documentation.",
    "naming-convention": "Apply the PascalCase identifier casing and length ranges. Use when naming or renaming classes, functions, methods, variables, globals, or constants.",
    "no-cad-runtime": "Keep CAD applications and vendor automation out of production runtime paths. Use when implementing, testing, or reviewing CAD parsing, conversion, or writing workflows.",
    "no-donor-blocks": "Never ship vendor bytes; reverse engineer proprietary binary formats until they can be emitted from first principles. Use when reading or writing SOLIDWORKS, CATIA, Parasolid, or any proprietary CAD format.",
    "no-stubs": "Deliver complete implementations with no stubs, placeholders, or incomplete code. Use for all code changes and bug fixes.",
    "no-unrequested-styling": "Limit UI changes to the requested scope. Use when changing pages, visual styling, layout, or components.",
    "page-title-separator": "Use the double-colon separator in public page titles. Use when editing document metadata, SEO titles, or public landing and marketing routes.",
    "pin-dependencies": "Pin GitHub Actions and runners to immutable references. Use when editing GitHub Actions workflows, actions, or runner versions.",
    "pixi-lockfiles": "Relock Pixi manifests. Use whenever editing pixi.toml, Pixi dependencies, environments, or channels.",
    "python-package-manager": "Use uv for Python dependency management. Use when changing Python dependencies, pyproject.toml, uv.lock, CI, or container commands.",
    "rationale-comments": "Explain why each class, function, lambda, and module-level constant exists in a comment directly above it. Use when adding or editing Python declarations.",
    "react-doctor": "Run React Doctor and resolve introduced regressions. Use when changing React source files, components, hooks, or JSX.",
    "repository-structure": "Enforce repository path naming, semantic folder density, exact imports, extension modules, SOLID boundaries, and security-quality verification. Use when creating, renaming, moving, organizing, importing, or securing project files.",
    "shadcn-pages": "Follow the shadcn UI CLI-first composition method. Use when adding UI primitives or building React and Next.js pages.",
    "split-large-definitions": "Split substantial declarations into focused files with exact symbol imports. Use when adding or changing code structure, modules, classes, functions, variables, registries, or imports.",
    "spdx-header": "Apply the repository's required SPDX headers. Use when creating project files; Agent Skills use schema-required license frontmatter instead.",
    "user-owned-workspace": "Preserve user-owned workspace state. Use whenever inspecting or modifying a shared worktree, especially when unknown commits, branches, staged changes, unstaged changes, untracked files, or background Git activity appear.",
    "workos-token-verification": "Verify WorkOS user-management JWT access tokens with the client-specific issuer. Use when changing Python backend authentication, token validation, or backend files.",
}
