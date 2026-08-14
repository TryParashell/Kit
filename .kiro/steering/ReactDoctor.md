# React Doctor Health Gate

All React code committed to this workspace MUST pass a React Doctor regression check. Run React Doctor after every chat completion that creates or modifies React code, in the same way Prettier and Black are run for formatting, before considering the work done.

## Scope

This applies to any change touching React source: `.tsx`, `.jsx`, and `.ts`/`.js` files that contain React components, hooks, or JSX. It applies to the frontend projects (e.g. `AgentUI/` and any other Next.js app in the workspace). It does not apply to pure Python or backend-only changes.

## The Loop

After changing React code, run from the affected project root (the directory containing its `package.json`, e.g. `AgentUI/`):

```bash
npx react-doctor@latest --verbose --silent --yes --no-ci --scope changed
```

## YOU MUST ADD THESE ARGS --silent --yes --no-ci OR ELSE REACT DOCTOR WILL STALL

Then:

1. Read the reported issues. Fix every issue introduced by your change — errors first, then warnings.
2. Apply real fixes that address the root cause. Do not silence a rule with an inline ignore or by deleting the offending feature.
3. Re-run the exact same command.
4. Repeat the fix-and-rerun cycle until the command reports no issues introduced by your change and the score does not regress versus the base branch.

The work is not done until a clean `--scope changed` run confirms zero new issues.

## Boundaries

- Only fix issues in our codebase. Do not fix the pre-existing or issues in another codebase, for example if issues get flagged for ShadCN, do not fix ShadCN's code as that is not our code, even though it may be in our components dir. THIS RULE APPLIES TO ALL OTHER RULES.
- A full-codebase cleanup pass (`npx react-doctor@latest --verbose --scope full`, fixing by severity) is done only when the user explicitly requests triage or `/doctor`.

## Non-Interactive Use

Run React Doctor non-interactively so the loop never blocks. Do not accept the wizard's prompts to add CI workflows, package scripts, or other files during the loop. If a prior run added a `.github/workflows/react-doctor.yml` or similar that the user did not ask for, leave it out.

## Verification

A change to React code is complete only when `npx react-doctor@latest --verbose --scope changed` reports no newly introduced errors or warnings for the files you touched. Treat a non-clean result the same as a failing formatter check: keep working until it is clean.
