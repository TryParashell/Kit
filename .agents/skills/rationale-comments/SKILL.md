---
name: rationale-comments
description: "Explain why each class, function, lambda, and module-level constant exists in a comment directly above it. Use when adding or editing Python declarations."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/rationale-comments.md"
  kiro-inclusion: "always"
---

# Rationale Comment Convention — One "Why" Comment Above Every Definition

This rule is MANDATORY for every definition in this codebase. It is separate from and in addition to `naming-convention.md`. Every class, `def`, lambda, and module-level global or constant requires exactly one comment directly above it explaining WHY it exists — not what it does, not how it works.

## The Core Rule

Above every:

- `class` statement
- `def` statement (functions, methods, staticmethods, classmethods — all of them)
- lambda assignment
- global / module-level variable or constant

there must be:

1. A blank line immediately before the comment.
2. A comment immediately above the identifier, with no blank line between the comment and the thing it explains.
3. Comment text that explains purpose — the gap it fills, the problem it solves, why it is here. Never a restatement of the mechanics.
4. 5–25 words, hard range, counted as whitespace-separated tokens.
5. All lowercase. No exceptions — not even proper nouns, acronyms, or `i`.
6. No punctuation of any kind — no periods, commas, colons, semicolons, hyphens as punctuation, parentheses, exclamation or question marks. Hyphenated compounds (e.g. `rate-limit`) are borderline; rephrase instead of using one.
7. The surrounding code must still be Black-clean.

## Why vs What

Wrong, describes mechanics:

```python
# loops through users and appends active ones to a list
def GetActv():
    ...
```

Right, describes purpose:

```python
# needed because billing only cares about currently active accounts
def GetActv():
    ...
```

Wrong:

```python
# multiplies price by tax rate
CalcTax = lambda Price, Rate: Price * Rate
```

Right:

```python
# tax math got duplicated in three places so it lives here once
CalcTax = lambda Price, Rate: Price * Rate
```

## Classes

```python
# external api shape kept changing so this isolates us from it
class ApiShim:
    ...
```

## Globals & Module-Level Constants

```python
# support said five retries was the sweet spot after last outage
KMaxRetries = 5
```

## Methods Inside Classes

Every method gets its own comment, not just the class:

```python
# needed to isolate this integration for tests without a live network
class ApiShim:

    # mock responses have to live somewhere other tests cant reach
    def LoadMock(self):
        ...
```

## Decorated Functions

The comment goes above the decorator stack, never between a decorator and the `def`:

```python
# retries belong here so callers dont each reimplement backoff logic
@Retry(times=3)
def FetchData():
    ...
```

## Lambdas

Applies whether the lambda is assigned to a name or passed inline. When passed inline, the comment goes above the full statement it is part of:

```python
# sorting by cost was requested over sorting by name for this view
Items.sort(key=lambda Item: Item.Cost)
```

## Nested & Inner Functions

Same rule, no exception for closures or local helpers:

```python
def Outer():

    # extracted because outer was doing two unrelated jobs at once
    def Inner():
        ...
```

## Word Count & Case Enforcement

Word count is the number of whitespace-separated tokens after the `#` and its leading space. `# needed because billing only cares about currently active accounts` is 10 words and valid.

Reject any comment outside 5–25 words, any comment containing an uppercase letter, and any comment containing `.` `,` `;` `:` `-` `(` `)` `!` `?`.

The predicate:

```python
import re


# naming and rationale drift within a week unless a hook checks both
def IsValidRationale(CommentText: str) -> bool:
    CleanText = CommentText.lstrip("#").strip()
    if CleanText != CleanText.lower():
        return False
    if re.search(r"[.,;:!?()\-]", CleanText):
        return False
    WordCount = len(CleanText.split())
    return 5 <= WordCount <= 25
```

## Black Compatibility

Black does not touch comment text or comment placement relative to the code it precedes, so this convention does not conflict with it. Black will collapse extra blank lines and enforce its own blank-line rules between defs, but a single blank line before a comment or def is preserved, not removed. It reformats the code itself (line length, quotes, trailing commas) and leaves comment content alone.

Run Black as normal after writing code. It will never delete or reflow these comments, and it will never add the blank line or the comment for you.

## Enforcement

Neither Black nor Python enforces any of this. Pair the predicate above with `IsValidName` from `naming-convention.md` into a single AST-walking pre-commit hook that:

1. Walks the AST for every `ClassDef`, `FunctionDef`, `AsyncFunctionDef`, `Lambda`, and module-level `Assign`.
2. Confirms a blank line plus a comment line immediately precedes it in source.
3. Validates the comment against `IsValidRationale`.
4. Validates the identifier against `IsValidName`.

This is not optional tooling. Without it both conventions drift.

## Relationship To no-stubs.md

`no-stubs.md` bans explanatory comments in code. This rule overrides that ban for exactly one case: the single mandated rationale comment above each definition. Everything else in `no-stubs.md` still stands — no `TODO`, no `FIXME`, no inline commentary inside function bodies, no comments standing in for missing logic. One rationale comment per definition, nothing more.

## Cheat Sheet

- Blank line, then comment, then the class/def/lambda/global. No exceptions.
- The comment explains why it exists, never what it does.
- 5–25 words, hard range.
- All lowercase, always.
- No punctuation of any kind.
- Decorators: comment goes above the decorator stack.
- Lambdas: comment goes above wherever the lambda statement lives, inline or assigned.
- Black will not break this convention, and it will not create it.

## Verification

Before considering any code change complete, confirm:

1. Every class, `def`, lambda, and module-level global you added or touched has exactly one rationale comment above it, preceded by a blank line.
2. Every rationale comment is 5–25 words, all lowercase, and free of punctuation.
3. Every rationale comment states why the definition exists, not what it does.
4. Decorated definitions carry the comment above the decorator stack.
5. No stray inline commentary was added beyond the mandated rationale comments.

If any check fails, the work is not done. Fix it before reporting completion.
