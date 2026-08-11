---
name: naming-convention
description: "Apply the PascalCase identifier casing and length ranges. Use when naming or renaming classes, functions, methods, variables, globals, or constants."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/naming-convention.md"
  kiro-inclusion: "always"
---

# Naming Convention — PascalCase Everywhere, With Hard Length Ranges

This rule is MANDATORY for every identifier in this codebase. It ranks alongside the formatting, no-stubs, and no-donor-blocks gates. All identifiers — classes, functions/methods, variables, globals, and constants — use PascalCase. No underscores, no camelCase, no snake_case, no ALL_CAPS constants.

This deliberately breaks from PEP 8. That is a project decision, not an oversight. Do NOT "fix" names back to standard Python style, and do not flag them as a style problem.

## Hard Length Ranges

| Identifier type                 | Min | Max | Case       |
| ------------------------------- | --- | --- | ---------- |
| Classes                         | 5   | 15  | PascalCase |
| Functions / methods (`def`)     | 5   | 15  | PascalCase |
| Variables / globals / constants | 5   | 25  | PascalCase |

Length is counted in letters only (no underscores exist to count, since none are used). If a name does not fit the range, shorten or expand it — never truncate mid-word into something unreadable. Prefer a synonym or a dropped filler word.

## Classes (5–15 chars)

Noun or noun phrase, PascalCase, no verbs.

```python
class UserAcct:      # ok
class HttpClient:    # ok
class Cfg:           # too short (3) — invalid
class UserAccountManagerFactory:  # too long — invalid, shorten
```

Fix for overlong class names: drop redundant words (`Manager`, `Factory`, `Helper`, `Object`) or abbreviate consistently per the glossary below.

```python
class AcctMgr:       # 7 chars, ok
```

## Functions & Methods (5–15 chars)

Verb or verb phrase, PascalCase. Applies to free functions, instance methods, staticmethods, and classmethods alike — no exception for methods taking `self` or `cls`.

```python
def GetUser():       # ok
def CalcTotal():     # ok
def Run():           # too short (3) — invalid
def InitializeConnectionPool():  # too long — invalid
```

Fix for overlong method names:

```python
def InitPool():      # 8 chars, ok
```

Dunder methods (`__init__`, `__repr__`, etc.) are exempt — Python requires those exact names and they are outside your naming authority.

## Variables, Globals & Constants (5–25 chars)

Noun or noun phrase, PascalCase. Covers locals, instance attributes, module-level globals, and constants alike. There is no ALL_CAPS carve-out for constants.

```python
UserName = "Jae"     # ok
KMaxRetries = 5      # ok, K prefix per identifier-markers.md
Db = None            # too short (2) — invalid
X = 1                # too short — invalid
TotalNumberOfActiveUserConnections = 0  # too long — invalid
```

Fix for overlong variable names:

```python
ActiveConns = 0      # 11 chars, ok
```

Loop counters, throwaway locals, and lambda arguments must also hit the 5-char floor. No `i`, `j`, `x`, `n` — and no `Idx`, `Val`, `Itm` either, since those are under 5. Use `Index`, `Value`, `Item` (all exactly 5).

## Abbreviation Glossary

Abbreviations come from this shared glossary so they stay consistent project-wide instead of being improvised per file.

| Full word     | Abbreviation |
| ------------- | ------------ |
| Manager       | Mgr          |
| Configuration | Cfg          |
| Account       | Acct         |
| Connection    | Conn         |
| Database      | Db           |
| Message       | Msg          |
| Request       | Req          |
| Response      | Resp         |
| Initialize    | Init         |
| Calculate     | Calc         |
| Maximum       | Max          |
| Minimum       | Min          |
| Parameter     | Param        |
| Argument      | Arg          |
| Reference     | Ref          |

Add new terms to this table as they come up. Never invent a one-off abbreviation inline — put it here first so every file agrees.

## Padding Rules

Never pad to reach the 5-char floor with meaningless filler (`Xxxxx`, `Val1`). Add a real qualifying word instead.

```python
Val         # 3 chars, invalid
CurVal      # 6 chars, ok — "current value"
TmpBuf      # 6 chars, ok — "temporary buffer"
```

## Validation

Python does not enforce this, so it needs a custom check (a pre-commit hook or an AST-walking script). The predicate is:

```python
import re


def IsValidName(NameText: str, KindText: str) -> bool:
    if KindText in ("class", "def"):
        LowLimit, HighLimit = 5, 15
    else:
        LowLimit, HighLimit = 5, 25
    if not re.fullmatch(r"[A-Z][a-zA-Z]*", NameText):
        return False
    return LowLimit <= len(NameText) <= HighLimit
```

## Cheat Sheet

- Classes: PascalCase, 5–15 chars, noun phrase.
- Functions/methods: PascalCase, 5–15 chars, verb phrase.
- Variables/globals/constants: PascalCase, 5–25 chars, noun phrase.
- No underscores anywhere in names.
- No ALL_CAPS constants — constants follow the same PascalCase + 5–25 rule as variables.
- Dunder methods are the only exempt identifiers.
- Abbreviations come from the shared glossary, not improvised per file.

## Verification

Before considering any code change complete, confirm:

1. Every identifier you added or renamed is PascalCase with no underscores.
2. Every class and `def` name is 5–15 letters; every variable, global, and constant is 5–25 letters.
3. Any abbreviation used appears in the glossary above (add it there if it is new).
4. No existing PascalCase name was "corrected" to snake_case, camelCase, or ALL_CAPS.

If any check fails, the work is not done. Fix it before reporting completion.
