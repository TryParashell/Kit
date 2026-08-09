---
name: pin-dependencies
description: "Pin GitHub Actions and runners to immutable references. Use when editing GitHub Actions workflows, actions, or runner versions."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/pin-dependencies.md"
  kiro-inclusion: "always"
---
# Pin Dependencies To Immutable References — GitHub Actions And Runners

Every GitHub Actions workflow in this repository MUST reference third-party actions by their full 40-character commit SHA, never by a mutable tag or branch. Runners MUST be pinned to a specific image version, never a floating `-latest` label. This rule is MANDATORY for every workflow file added or edited in this workspace.

## Why

A tag like `@v4` or a branch like `@main` is a pointer that the upstream maintainer — or an attacker who compromises their account or force-pushes the tag — can move to different code at any time, with no corresponding diff in this repository. `runs-on: ubuntu-latest` has the same problem: the underlying image changes on GitHub's schedule, not ours, so a workflow can start behaving differently with no change to this repo's history. Pinning to an exact commit SHA and an exact runner image version means the same code runs on every invocation until a human deliberately bumps the pin.

## Rule 1: Pin Every `uses:` To A Full Commit SHA

For every `uses: <owner>/<repo>@<ref>` step (including nested/composite actions and reusable workflows), replace the ref with the full 40-character commit SHA of the exact release you intend to run, followed by a trailing comment naming the human-readable version:

```yaml
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
```

Resolve the SHA for a given tag with:

```bash
git ls-remote --tags --refs https://github.com/<owner>/<repo>.git | grep '<tag>$'
```

Never pin to a short SHA, a branch name, or a bare major/minor tag (`@v4`, `@v4.4`, `@main`, `@master`).

## Rule 2: Pin Runners To A Specific Image Version

Replace floating `runs-on` labels with a pinned version:

- `ubuntu-latest` → `ubuntu-24.04` (or whichever specific Ubuntu version the workflow is verified against).
- `windows-latest` → `windows-2022` (or the specific version in use).
- `macos-latest` → `macos-14` (or the specific version in use).

Self-hosted runner labels are exempt from this rule since there is no upstream image to float.

## Rule 3: Keep The Pins Fresh Via Dependabot

`.github/dependabot.yml` MUST include a `github-actions` ecosystem entry alongside the language-package entries. Dependabot understands the `@<sha> # vX.Y.Z` comment convention and opens PRs that bump both the SHA and the comment when a new release ships — do not remove the trailing version comment, and do not hand-roll a separate update mechanism.

## Verification

Before considering any workflow-file change complete, confirm:

1. Every `uses:` step resolves to a full 40-character commit SHA, with a `# vX.Y.Z` (or equivalent) comment naming the release.
2. Every `runs-on:` value is a specific runner image version, not a `-latest` label (self-hosted labels excepted).
3. `.github/dependabot.yml` has a `github-actions` ecosystem entry covering the directory the workflow lives in.

If any check fails, the work is not done. Fix it before reporting completion.
