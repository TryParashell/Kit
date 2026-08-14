---
inclusion: always
---

# Preserve user owned workspace state

Treat every preexisting concurrent or unexplained workspace change as user owned

- Assume unknown commits branches staged changes unstaged changes untracked files and background Git activity belong to the user
- Preserve user work and adapt the current task around it
- Never revert overwrite delete amend squash reset clean or otherwise rewrite unknown state
- Do not attribute unknown changes to another agent automation corruption or interference unless the user explicitly identifies the source
- Inspect history diffs and status read only when needed to understand overlap
- If user owned work overlaps the requested edit merge the intent carefully and keep both behaviors whenever technically possible
- Stop and ask only when preserving both changes is impossible or the next action would destroy or rewrite user owned state
- Report material overlap factually without treating the user activity as an error

