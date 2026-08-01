---
inclusion: always
---

# ABSOLUTE ZERO TOLERANCE: NO STUBS, NO PLACEHOLDERS, NO INCOMPLETE CODE

This is the single most important rule in this workspace. Every other instruction is secondary to this one.

## THE RULE

Every line of code you write MUST be production-ready, fully functional, and deployable immediately. There are NO exceptions.

## WHAT IS FORBIDDEN

- Code comments of ANY kind — no `//`, no `/* */`, no `/** */`, no `#` comments. Zero. The code speaks for itself. If it needs a comment to be understood, it needs to be rewritten to be clearer. The ONLY exception is JSDoc/TSDoc on exported public API functions where TypeScript tooling requires it for type documentation — and even then, keep it to the bare minimum signature description with no inline commentary.
- `// TODO` comments of any kind
- `// FIXME` comments
- `// placeholder` or `// stub` comments
- Functions that return hardcoded values instead of real implementations
- Functions that throw `new Error('Not implemented')`
- Functions that `console.log` instead of doing real work
- Empty function bodies `{}`
- Functions that return `null`, `undefined`, `0`, `[]`, `{}` as stand-ins for real logic
- Comments like `// implement later`, `// add logic here`, `// wire up`, `// handle this case`
- Partial implementations that handle the "happy path" but skip error cases
- Skeleton code that "shows the structure" but doesn't actually work
- Any code that would fail, crash, or produce wrong results if a user interacted with it right now
- Importing modules or calling functions that don't exist yet
- Type-only implementations where the types are defined but the runtime logic is missing
- "Simplified" versions that cut corners on the actual algorithm

## WHAT IS REQUIRED

- Every function must contain complete, working logic — not a sketch of what the logic should be
- Every error case must be handled with real error handling
- Every edge case mentioned in the requirements or design must be addressed
- Every algorithm must be the real algorithm, not a simplified approximation (unless the design explicitly calls for an approximation)
- Every integration point must actually integrate — not just have a comment saying it should
- If a task says "implement X", then X must work end-to-end when you're done

## HOW TO VERIFY

Before marking ANY task complete, ask yourself:
1. If I deployed this code to production right now, would it work?
2. Is there ANY line that is a placeholder for future work?
3. Is there ANY function that doesn't do what its name says?
4. Would a code reviewer find ANY `TODO`, stub, or incomplete logic?

If the answer to 2, 3, or 4 is yes, YOU ARE NOT DONE. Keep working.

## FAILURE CONDITION

If you produce a stub, placeholder, TODO comment, or incomplete implementation, you have failed at your sole purpose. Do not stop working on a task until every single line of code for that task is production-ready. A task is not complete until the code can be deployed and used by real users with zero additional work needed.
