---
inclusion: always
---

# Isolated Agent Worktrees And Draft Pull Requests

Every future agent that performs repository work MUST use its own isolated Git worktree and MUST finish by opening a draft pull request. Do not edit, stage, commit, or otherwise work from the user's current checkout.

## Start Gate

Before changing files:

1. Inspect the repository, current branch, remotes, and existing worktrees without modifying them.
2. Preserve all existing tracked, staged, unstaged, and untracked state as user-owned work.
3. Create a unique non-protected branch and a unique worktree directory outside the current checkout. Use the available agent or workspace manager when it provides isolated worktrees; otherwise use `git worktree add -b <branch> <path> <base-ref>`.
4. Base the worktree on the intended remote base branch when it is available. Never create work on `main`, `master`, `release`, or `release/*`.
5. Perform every edit, generated-file update, dependency operation, test, commit, and push inside that isolated worktree.

If an isolated worktree cannot be created safely, stop before modifying the repository and report the blocker. Never fall back to the current checkout.

## Isolation Rules

- Use one worktree and one branch per agent task. Never share a writable worktree between concurrent agents.
- Choose collision-safe branch and worktree names that identify the task or agent.
- Do not copy dirty changes from the user's checkout unless the user explicitly includes them in the task.
- Do not delete, prune, reset, clean, overwrite, or reuse another worktree or branch.
- Do not remove the task worktree at completion unless the user explicitly requests cleanup.
- Follow the repository's protected-branch and user-owned-workspace rules throughout.

## Completion Gate

Before reporting completion:

1. Complete and verify the requested work with no known failures.
2. Review the task branch diff and ensure it contains only intended changes and no secrets.
3. Commit the intended changes on the task branch.
4. Push only the task branch to its remote.
5. Open a draft pull request targeting the intended base branch, preferably with `gh pr create --draft`, and include a concise summary plus verification results.
6. Confirm the pull request is marked draft and report its URL.

The task is not complete until the draft pull request exists. If authentication, permissions, remote configuration, or network access prevents the push or draft pull request, keep the work and commits in the isolated worktree, report the exact blocker, and do not claim completion.

## Kiro Support

Kiro loads workspace steering from `.kiro/steering/` in the IDE, CLI, Web, and Mobile clients and also supports `AGENTS.md`. Kiro's documented steering and custom-agent configuration does not itself guarantee automatic Git worktree provisioning, so agents must enforce this rule through available workspace orchestration or Git worktree commands.
