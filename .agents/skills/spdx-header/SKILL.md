---
name: spdx-header
description: "Apply the repository's required SPDX headers. Use when creating project files; Agent Skills use schema-required license frontmatter instead."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/SpdxHeader.md"
  kiro-inclusion: "always"
---

# SPDX License Header — Required On Every New File

Every new file created in this repository MUST start with the SPDX license header block defined in `HEADER_NOTICE` at the repository root. This applies to files you create yourself and to files you generate on the user's behalf.

## Scope

Add the header to every new file in the repository, **except** files under:

- `.kiro/` (this directory and everything below it)
- `examples/` (this directory and everything below it)

Binary files that cannot contain a text comment (images, compiled artifacts, CAD binaries, etc.) are exempt for the obvious reason that there is nowhere to put it.

## Agent Skills exception

`SKILL.md` files under `.agents/skills/` must begin with the Agent Skills YAML
frontmatter. Use `license: LicenseRef-PolyForm-Strict-1.0.0` in that
frontmatter instead of the comment header. The SPDX guard validates this field
in place of the standard header.

## The Header

Copy the exact text from `HEADER_NOTICE`, then prefix each line with that language's line-comment token (`#`, `//`, `--`, etc.), or wrap it in the language's block-comment syntax when the file has no line-comment token (e.g. HTML/Markdown `<!-- -->`). Do not paraphrase, shorten, or reorder the lines:

```
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
```

For a Python/YAML/shell-style file, this looks like:

```python
# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.
```

The header is the first thing in the file (before any shebang-adjacent content it must still come first except a `#!` shebang line, which stays on line 1 with the header immediately after).

## Rule

Never remove, edit, or truncate this header from an existing file. If a change requires touching the top of a file that already carries this header, preserve it exactly.

## Verification

Before considering any file-creation task complete, confirm every new file outside `.kiro/` and `examples/` carries this exact header as its first content.
