<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Security Policy

## Supported versions

Security fixes target the default branch (`main`) and are released from it.
Older tags do not receive security backports.

## Reporting a vulnerability

Do not open a public issue for suspected vulnerabilities.

Report privately through GitHub's vulnerability reporting for this repository:
`https://github.com/TryParashell/Kit/security/advisories/new`

Include a description, affected version or commit, reproduction steps, and any
proof-of-concept material. Reports receive an initial triage response within
seven days and remain embargoed until a fix ships.

## Scope

In scope: code in `src/`, `tools/`, `.github/` (workflows and scripts), and the
locked dependency set in `uv.lock`.

Out of scope: vendor tooling under `re/`, compatibility workspaces under
`Parashell/` and `modules/`, and anything requiring a local CAD installation.

## Automated monitoring

Continuous integration runs secret auditing (Gitleaks, TruffleHog,
detect-secrets), dependency vulnerability scanning (pip-audit, Safety,
OSV-Scanner, Grype, Trivy), static analysis (Bandit, Semgrep, CodeQL, dlint),
infrastructure-as-code checks (Checkov), workflow audits (zizmor, actionlint),
and supply-chain posture scoring (OpenSSF Scorecard).
