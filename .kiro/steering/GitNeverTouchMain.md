# Git: NEVER Commit, Push, or Pull On `main`

This rule is ABSOLUTE and MANDATORY for every agent in this workspace, across every repository (the `Parashell` FreeCAD fork, `modules/`, `agentUi/`, and all others). It ranks above convenience, above "fix errors don't ask", and above any urge to get CI green faster. Violating it is a hard failure, no matter how small or safe the change seems.

## The Rule

You MUST NEVER run a git operation that commits to, pushes to, or pulls into the `main` branch. This is true even if:

- The user says "fix CI asap", "fix all issues", or otherwise sounds urgent.
- The change is tiny, obviously correct, or "just a one-liner".
- CI is red and the only way to verify a fix is to push.
- `main` is the currently checked-out branch.
- A previous agent or the user pushed to `main` earlier in the session.

Urgency, triviality, and prior precedent are NEVER authorization. There is no implicit permission. The only way `main` gets a commit/push/pull is the human doing it themselves.

## FORBIDDEN On `main` (never, under any circumstance without being on a different working branch)

- `git commit` while `main` is checked out.
- `git push` that updates `origin/main` (or any remote `main`), including `git push origin main`, `git push` while `main` is checked out and tracking `origin/main`, and any force variant.
- `git pull` / `git fetch && git merge` / `git rebase` that updates the local `main` branch.
- `git merge`, `git reset`, `git rebase`, `git cherry-pick`, or `git revert` that writes onto `main`.
- Any `--force` / `-f` push to `main`, ever.

## ALLOWED (on a working branch that is NOT `main`)

- Commit, push, pull, merge, and rebase freely ON THE CURRENT WORKING BRANCH, provided that branch is not `main` (and not another protected trunk such as `master`, `release`, or a `release/*` branch).
- Create a new working branch off `main` (`git switch -c <branch>`) and do all work there.
- Read-only inspection anywhere: `git status`, `git log`, `git diff`, `git show`, `git branch`, `git remote -v`, `git rev-list`, `gh run list`, `gh run view`. Reading is always fine.

Note: creating a branch and pushing THAT branch to its own `origin/<branch>` ref is allowed. What is forbidden is writing to the `main` ref, locally or remotely.

## Required Behavior When Work Needs To Land On `main`

1. Do the work as local edits.
2. If commits are needed, first confirm you are on a non-`main` working branch. If you are on `main`, STOP and either create a working branch (only if the user asked you to commit) or leave the changes uncommitted for the user.
3. Never open a PR-merge or push to `main` yourself. Hand off to the user: state exactly what you changed and that landing it on `main` (commit/push/PR merge) is theirs to do.
4. If the only way to verify a fix is via CI on `main`, do NOT push to `main` to trigger it. Explain that verification requires the user to land the change (or authorize a branch + PR), and stop.

## Pre-Flight Check Before ANY Git Write

Before running any git command that could write history, run `git rev-parse --abbrev-ref HEAD` (or otherwise confirm the branch) and verify:

- The target of the operation is NOT `main` (or another protected trunk).
- For pushes, the refspec does NOT resolve to `origin/main`.

If either check fails, do not run the command.

## Verification

Before considering any task involving git complete, confirm:

1. No commit was created on `main`.
2. No push updated `origin/main` (or any remote `main`).
3. No pull/merge/rebase/reset updated local `main`.
4. All git writes happened on a non-`main` working branch, or were left to the user.

If any check fails, the rule was violated. Stop, disclose it plainly to the user, and do not repeat it.
