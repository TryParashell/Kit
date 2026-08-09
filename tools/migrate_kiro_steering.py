# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Generate and verify the Agent Skills copy of Kiro steering."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / ".kiro" / "steering"
TARGET_DIR = ROOT / ".agents" / "skills"
LICENSE = "LicenseRef-PolyForm-Strict-1.0.0"

DESCRIPTIONS = {
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
    "no-donor-blocks": "Never ship vendor bytes; reverse engineer proprietary binary formats until they can be emitted from first principles. Use when reading or writing SOLIDWORKS, CATIA, Parasolid, or any proprietary CAD format.",
    "no-stubs": "Deliver complete implementations with no stubs, placeholders, or incomplete code. Use for all code changes and bug fixes.",
    "no-unrequested-styling": "Limit UI changes to the requested scope. Use when changing pages, visual styling, layout, or components.",
    "page-title-separator": "Use the double-colon separator in public page titles. Use when editing document metadata, SEO titles, or public landing and marketing routes.",
    "pin-dependencies": "Pin GitHub Actions and runners to immutable references. Use when editing GitHub Actions workflows, actions, or runner versions.",
    "pixi-lockfiles": "Relock Pixi manifests. Use whenever editing pixi.toml, Pixi dependencies, environments, or channels.",
    "python-package-manager": "Use uv for Python dependency management. Use when changing Python dependencies, pyproject.toml, uv.lock, CI, or container commands.",
    "rationale-comments": "Explain why each class, function, lambda, and module-level constant exists in a comment directly above it. Use when adding or editing Python declarations.",
    "react-doctor": "Run React Doctor and resolve introduced regressions. Use when changing React source files, components, hooks, or JSX.",
    "shadcn-pages": "Follow the shadcn UI CLI-first composition method. Use when adding UI primitives or building React and Next.js pages.",
    "spdx-header": "Apply the repository's required SPDX headers. Use when creating project files; Agent Skills use schema-required license frontmatter instead.",
    "workos-token-verification": "Verify WorkOS user-management JWT access tokens with the client-specific issuer. Use when changing Python backend authentication, token validation, or backend files.",
}

KIRO_METADATA = {
    "workos-token-verification": {
        "kiro-inclusion": "fileMatch",
        "kiro-file-match-pattern": "backend/**/*.py",
    }
}


def source_body(source: str) -> str:
    """Remove only Kiro's leading YAML block, retaining its rule body verbatim."""

    match = re.match(r"\A---\r?\n[\s\S]*?\r?\n---\r?\n?", source)
    if match:
        source = source[match.end() :].lstrip("\r\n")
    return source.rstrip() + "\n"


def quote_yaml(value: str) -> str:
    """Emit a JSON string, which is also a valid YAML scalar."""

    return json.dumps(value, ensure_ascii=False)


def source_path(name: str) -> Path:
    """Return the Kiro steering source for one portable skill."""

    return SOURCE_DIR / f"{name}.md"


def target_path(name: str) -> Path:
    """Return the standard Agent Skills discovery location for one skill."""

    return TARGET_DIR / name / "SKILL.md"


def stale_skill_directories() -> list[Path]:
    if not TARGET_DIR.is_dir():
        return []
    expected_names = set(DESCRIPTIONS)
    return sorted(
        (
            path
            for path in TARGET_DIR.iterdir()
            if path.is_dir() and path.name not in expected_names
        ),
        key=lambda path: path.name,
    )


def render_skill(name: str) -> str:
    """Render one schema-valid Agent Skills document from its Kiro source."""

    source = source_path(name)
    metadata = {
        "source": source.relative_to(ROOT).as_posix(),
        "kiro-inclusion": "always",
        **KIRO_METADATA.get(name, {}),
    }
    frontmatter = [
        "---",
        f"name: {name}",
        f"description: {quote_yaml(DESCRIPTIONS[name])}",
        f"license: {LICENSE}",
        "metadata:",
        *(f"  {key}: {quote_yaml(value)}" for key, value in metadata.items()),
        "---",
        "",
    ]
    return "\n".join(frontmatter) + source_body(source.read_text(encoding="utf-8"))


def validate_specs() -> list[str]:
    """Check the source inventory and Agent Skills metadata before writing."""

    errors: list[str] = []
    source_names = {path.stem for path in SOURCE_DIR.glob("*.md")}
    skill_names = set(DESCRIPTIONS)
    if missing_skills := source_names - skill_names:
        errors.append(
            f"source files without skills: {', '.join(sorted(missing_skills))}"
        )
    if missing_sources := skill_names - source_names:
        errors.append(
            f"skills without source files: {', '.join(sorted(missing_sources))}"
        )
    for name, description in DESCRIPTIONS.items():
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            errors.append(f"invalid Agent Skills name: {name}")
        if not description or len(description) > 1024:
            errors.append(f"invalid Agent Skills description length: {name}")
    return errors


def write_skills() -> None:
    """Write every Kiro steering rule to its Agent Skills location."""

    for stale_directory in stale_skill_directories():
        shutil.rmtree(stale_directory)
    for name in sorted(DESCRIPTIONS):
        target = target_path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_skill(name), encoding="utf-8")


def check_skills() -> list[str]:
    """Report generated skills that are missing or no longer match their source."""

    errors = validate_specs()
    for stale_directory in stale_skill_directories():
        location = stale_directory.relative_to(ROOT).as_posix()
        errors.append(f"unexpected generated skill: {location}")
    for name in sorted(DESCRIPTIONS):
        target = target_path(name)
        location = target.relative_to(ROOT).as_posix()
        if not target.is_file():
            errors.append(f"missing generated skill: {location}")
            continue
        if target.read_text(encoding="utf-8") != render_skill(name):
            errors.append(f"out-of-date generated skill: {location}")
    return errors


def parse_args() -> argparse.Namespace:
    """Parse the explicit generation or verification mode."""

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="write the Agent Skills copy from .kiro/steering",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="verify the Agent Skills copy without writing (the default)",
    )
    return parser.parse_args()


def main() -> int:
    """Synchronize or check the portable Agent Skills tree."""

    args = parse_args()
    if args.write:
        if errors := validate_specs():
            print("Cannot write Agent Skills migration:", file=sys.stderr)
            print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
            return 1
        write_skills()

    if errors := check_skills():
        print("Agent Skills migration check failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1

    print(f"Agent Skills migration is current: {len(DESCRIPTIONS)} skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
