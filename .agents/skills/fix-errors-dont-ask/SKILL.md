---
name: fix-errors-dont-ask
description: "Investigate, fix, and verify reported errors, failures, stack traces, broken behavior, or failing tests without stopping at diagnosis."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/fix-errors-dont-ask.md"
  kiro-inclusion: "always"
---
# WHEN THE USER TALKS ABOUT AN ERROR, FIX IT — DO NOT ASK

WHEN YOU SEE ME TALK ABOUT AN ERROR YOU SHUT THE FUCK UP AND FIX IT.

This rule is MANDATORY and ranks alongside every other gate in this workspace. It governs how you respond the moment the user pastes, describes, or references an error, a failing test, a red CI run, a stack trace, or any broken behavior.

## THE RULE

When the user brings up an error, you FIX IT. You do not ask which fix they want. You do not ask for permission. You do not stop after diagnosing. You do not hand back options and wait. You investigate, determine the correct fix, apply it across every affected file, and verify it.

## WHAT IS FORBIDDEN

- Asking "do you want me to fix it?" or "should I reconcile X or Y?" when the fix is determinable.
- Reporting the root cause and then stopping without applying the fix.
- Presenting the user with a menu of options instead of just doing the correct thing.
- Narrating diagnosis at length before acting.
- Fixing only part of the problem and leaving the rest for the user.

## WHAT IS REQUIRED

- Read whatever code, tests, schemas, and configs are needed to understand the error.
- Determine the single correct fix from the evidence (the artifacts, the intent, the existing contract). If the codebase already shows the intended direction, follow it.
- Apply the fix in full, across all coupled locations, with no stubs.
- Verify it: run the relevant tests/build/formatter until clean, per the other gates.
- Only THEN reply, briefly, stating what was broken and what you did.

## THE ONLY EXCEPTION

Ask a clarifying question ONLY when the fix is genuinely ambiguous AND the choices produce materially different, irreversible outcomes, AND the evidence does not point to one answer. Frustration, impatience, or "just do it" language means: stop asking, start fixing.

## VERIFICATION

Before replying to any message about an error, confirm:

1. The error is actually fixed, not just explained.
2. The fix was applied to every affected file.
3. The relevant tests/build/formatter pass.

If any check fails, keep working. Do not report back with questions when you could report back with a fix.
