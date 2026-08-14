---
name: linear-issue-tracking
description: "Track work end-to-end in Linear. Use when starting, updating, or completing a task that requires a Linear issue workflow."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/LinearIssueTracking.md"
  kiro-inclusion: "always"
---

# Linear Issue Tracking Gate

Every problem the user hands you MUST be tracked end-to-end in Linear. Before you start work you log the problem as a Linear issue with a structured analysis, you drive that issue through its workflow states as you work, and you do not consider the task finished until the issue is marked resolved (the completed `Done` state). This is mandatory, the same way formatting and the React Doctor gate are mandatory.

Use the Linear MCP tools for all of this (`save_issue`, `save_comment`, `list_issue_statuses`, `get_issue`, etc.). Never fabricate an issue identifier or claim an issue was created/updated/closed unless the tool call actually succeeded.

## Scope

This applies to any actionable problem: bug fixes, features, refactors, investigations, analyses, design/spec work, and multi-step tasks. It does NOT apply to:

- Pure questions or explanations where nothing in the workspace changes.
- Trivial one-liners, clarifying questions, or conversational replies.
- Work that is already governed by an open issue you created in this conversation — keep using that issue instead of opening a duplicate.

If you are unsure whether a request qualifies, default to logging it. When a single request contains several independent problems, open one issue per problem.

## Workspace Settings

- Team: `Parashell`.
- Workflow states (in order): `Backlog` → `Todo` → `In Progress` → `Done`. There is no state literally named "Resolved"; "resolved" means the completed state `Done`. `Duplicate` and `Canceled` are the other terminal states.
- Always confirm the live state names with `list_issue_statuses` if a tool call rejects a state value.

### Classification (priority + labels)

Every issue MUST be created with a deliberate priority and at least one label. Never leave an issue at `No priority` or unlabeled.

- **Priority** (the `priority` arg on `save_issue`): `1` = Urgent, `2` = High, `3` = Medium, `4` = Low. Do not use `0` (None) — always choose a real priority. Guidance:
  - `1` Urgent — broken builds/CI, crashes, data loss, security issues, or anything actively blocking the user right now.
  - `2` High — important bugs or features the user is waiting on, with no clean workaround.
  - `3` Medium — normal bugs, features, refactors, and improvements (the default for most work).
  - `4` Low — minor polish, nice-to-haves, cosmetic or non-urgent cleanup.
- **Labels** (the `labels` arg on `save_issue`): apply exactly one type label, adding more only when genuinely warranted. Current team labels:
  - `Bug` — something is broken or behaving incorrectly (build failures, crashes, wrong output).
  - `Feature` — new capability or net-new functionality.
  - `Improvement` — refactor, performance, docs/steering, tooling, or polish of existing behavior.
- Confirm the live label set with `list_issue_labels` (team `Parashell`) before creating. If none of the existing labels fit, create an appropriate one with `create_issue_label` rather than leaving the issue unlabeled, and never invent a label name without creating it.

## The Loop

1. **Log first.** Before touching code or running commands, create the issue with `save_issue` (team `Parashell`, state `Todo`). Set a deliberate `priority` and at least one `label` on creation per the Classification rules above — an issue at `No priority` or with no label is not properly logged. Title it as a concise problem statement. The description MUST contain a structured problem analysis, in the spirit of a Kiro spec / SWOT / problem breakdown:

   - **Problem** — what the user asked for, in their terms, plus the observable symptom or goal.
   - **Context** — affected files, components, domains, and any relevant current behavior you have confirmed.
   - **Analysis** — root-cause hypotheses or a short SWOT (strengths/weaknesses/opportunities/threats, or risks and constraints) for the approaches considered.
   - **Plan** — the concrete steps you intend to take, in order.
   - **Acceptance criteria** — the checklist that, when all true, means the problem is solved (build passes, tests pass, formatter/React Doctor clean, behavior verified, etc.).

   The issue is not properly logged until it has a real priority and at least one label set, in addition to the structured description above.

2. **Start.** Move the issue to `In Progress` with `save_issue` the moment you begin executing the plan.

3. **Work it systematically.** Tackle the plan step by step. As meaningful progress, decisions, scope changes, or blockers occur, append them to the issue with `save_comment` so the issue is an accurate running log. If the plan changes materially, update the description or add a comment explaining why.

4. **Verify before closing.** Only when every acceptance criterion is actually met — work done, build/tests/formatters/React Doctor clean per the other steering rules, and behavior verified — move the issue to `Done` with `save_issue`. Add a final `save_comment` summarizing the resolution and what was verified.

The task is not complete until its Linear issue is in the `Done` state. If you cannot finish, leave the issue in `In Progress` with a comment describing what remains, and say so plainly to the user — never silently mark it `Done`.

## Reporting

In your chat reply, reference the issue by its identifier (e.g. `OGM-123`) when you create it and when you resolve it, so the user can follow along. Keep this brief, consistent with the concise chat policy. Do not narrate every intermediate Linear update in chat — the issue comments are the running log; the chat reply states the outcome.

## Honesty

Treat Linear state as ground truth, not aspiration. Do not mark an issue `Done` if anything in the acceptance criteria is unmet or unverified. Do not claim a comment or status change happened unless the tool call returned success. If a Linear tool call fails, report the failure and keep the work item open rather than pretending it is tracked. An issue created without a deliberate priority and at least one label is not properly tracked — set them, do not rely on defaults.
