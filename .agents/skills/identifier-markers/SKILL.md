---
name: identifier-markers
description: "Prefix boolean-returning functions and methods with Is, Has, or Can. Use when naming or renaming any function or method that returns a bool."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/identifier-markers.md"
  kiro-inclusion: "always"
---

# Identifier Markers — Old-School Conventions Adapted For Python

This rule layers three historically grounded conventions on top of `naming-convention.md` and `rationale-comments.md`. All three are old standards that cannot be adopted literally in Python, because Python identifiers cannot contain `?` or `!` and raw Hungarian-style prefixes would break the PascalCase and length rules already locked in. This file defines the adapted, Python-legal equivalents and makes them MANDATORY.

Nothing here overrides `naming-convention.md` or `rationale-comments.md`. The length ranges, PascalCase, and the mandatory why-comment still apply to every identifier below.

## 1. Predicate Marking — adapted from the Lisp/Scheme `?` suffix

Lisp and Scheme mark boolean-returning functions with a trailing `?` (`empty?`, `null?`). Python identifiers cannot end in `?`, so this project encodes the same signal with a mandatory prefix instead.

Any function or method that returns a `bool` MUST start with one of:

| Prefix | Use for                                                |
| ------ | ------------------------------------------------------ |
| `Is`   | state checks — `IsValid`, `IsEmpty`                    |
| `Has`  | possession / containment checks — `HasKey`, `HasAuth`  |
| `Can`  | capability / permission checks — `CanEdit`, `CanRetry` |

```python
# flags empty carts early so checkout never runs on nothing
def IsEmpty(Cart):
    return len(Cart.Items) == 0
```

No other prefix is valid for a bool-returning function. If none of `Is` / `Has` / `Can` fits semantically, that is a signal the function is doing too much or returning the wrong thing — split it, or rename what it returns.

This stacks with the 5–15 character limit. `Is` alone is too short as a full name, but `IsEmpty`, `HasAuth`, and `CanEdit` all clear it.

## 2. Mutation Marking — adapted from the Lisp/Scheme `!` suffix

Lisp and Scheme mark destructive, in-place operations with a trailing `!` (`set!`, `reverse!`) to warn callers the operation is not pure. `!` is not legal in a Python identifier, so this project uses a mandatory suffix instead.

Any function or method that mutates one of its arguments in place — rather than returning a new value — MUST end in `Mut`.

```python
# sorts the queue in place since callers reuse the same list object
def SortQueueMut(Queue):
    Queue.sort()
    return None
```

Contrast with a pure version, which takes no suffix and MUST NOT mutate its input:

```python
# returns a fresh sorted copy so the caller can compare before after
def SortedCopy(Queue):
    return sorted(Queue)
```

A method that mutates `self` — an ordinary instance method touching its own object's state — is exempt. `Mut` exists only for functions and methods that mutate an argument passed in, since that is the surprising case a caller needs warning about. `__init__` is exempt too.

This stacks with the 5–15 character limit. Plan for the three extra characters `Mut` costs when naming.

## 3. Constant Marking — adapted from the `k` prefix convention

Older C++ style guides in the Google and NeXT lineage prefixed compile-time constants with `k` (`kMaxSize`) so they were visually distinct from ordinary mutable variables. This project uses PascalCase everywhere, so no case-based signal is left over — the prefix is revived explicitly.

Any module-level or class-level constant — a value set once and never reassigned — MUST start with `K`.

```python
# capped low on purpose since the vendor api throttles aggressively past this
KMaxRetries = 5

# shared across every client so timeout behavior stays consistent
KDefaultTimeout = 30
```

This applies only to true constants. A module-level global that gets reassigned during runtime is NOT a constant, takes no `K` prefix, and follows the plain variable rule in `naming-convention.md`.

`K` counts toward the 5–25 character range like any other letter. `KMax` is too short at 4; `KMaxRetries` at 11 is fine.

## How The Three Combine

An identifier may stack more than one marker when it genuinely fits both patterns and still lands in range:

```python
# checks the cached flag first so this stays cheap to call repeatedly
def IsStale(Cache):
    ...


# clears the cache in place because callers hold a long lived reference
def ClearCacheMut(Cache):
    ...


# never changed at runtime but shared so drift cant happen across modules
KCacheTtlSecs = 300
```

## Cheat Sheet

- Predicate functions (bool return): must start with `Is` / `Has` / `Can`.
- In-place mutators (mutate an argument, not `self`): must end with `Mut`.
- True constants (module or class level, set once): must start with `K`.
- All three still obey PascalCase, the 5–15 range for classes and defs, the 5–25 range for variables and constants, and the mandatory why-comment above them.
- `__init__` and the other dunders remain exempt from all of the above, same as in `naming-convention.md`.

## Verification

Before considering any code change complete, confirm:

1. Every bool-returning function or method you added or renamed starts with `Is`, `Has`, or `Can`.
2. Every function or method that mutates an argument in place ends in `Mut`, and nothing ending in `Mut` is pure.
3. Every module-level or class-level constant starts with `K`, and no reassigned global carries the prefix.
4. Every marked identifier still satisfies PascalCase and its length range after the marker is counted.
5. Every marked identifier still carries its mandated rationale comment.

If any check fails, the work is not done. Fix it before reporting completion.
