---
inclusion: always
---

# Isolated Agent Worktrees And Draft Pull Requests

Every future agent or sub-agent that performs repository work MUST use its own isolated Git worktree or an equivalent platform-provided isolated checkout. An agent MUST NOT make changes in the invoking agent's worktree.

## Required Workflow

1. Before delegation, create or select a dedicated worktree and non-protected feature branch for that agent. Use one worktree and branch per agent task; never share them between concurrent agents.
2. Give the agent only its isolated checkout as its working directory. Preserve all user-owned and caller-owned changes outside that checkout.
3. Require the agent to inspect, implement, format, and verify the task entirely inside its isolated checkout.
4. Require the agent to commit only its task changes to its feature branch and push only that branch. It MUST never write to `main` or another protected branch.
5. At the end, require the agent to open a draft pull request targeting the repository's normal base branch. The draft PR description MUST summarize the changes, list verification performed, and disclose failures or remaining blockers.
6. Treat the draft PR URL as the final handoff artifact. Do not merge the PR automatically.

## Capability Fallbacks

- Kiro Web tasks already run in isolated sandbox checkouts and normally create branches and pull requests. Preserve that isolation and make the resulting pull request a draft when the platform exposes draft control.
- If the agent runtime cannot create worktrees, use its native isolated workspace, sandbox, or checkout instead; never fall back to the caller's worktree.
- If credentials, remote access, or draft-PR tooling are unavailable, complete and verify the work on the isolated feature branch, then report the exact blocker and the branch or commit that is ready for handoff. Never claim a draft PR exists unless creation succeeded.
- Read-only advisory agents that make no repository changes do not require a worktree or pull request.

## Completion Gate

Repository-changing delegated work is not complete until the isolated branch is verified and a draft pull request has been created, except when a concrete capability blocker has been reported with a ready handoff branch or commit.
