---
inclusion: always
---

# mcp tool documentation pages

Agent facing MCP tools must have standalone Mintlify documentation pages

- treat every `@mcp.tool` in `modules/src/bridge/tools` as agent facing
- when adding renaming or materially changing a tool update the docs in the same change
- create or update `docs/agent/tools/reference/<tool_name>.mdx` for the tool
- the page must include the full descriptor signature without `ctx` arguments response type invocation shape and operational notes
- update `docs/agent/tools/reference/index.mdx` so the tool is linked from the verbose reference index
- update `docs/docs.json` so the page is present in Mintlify navigation
- update any grouped MCP tool page and count when the tool belongs to an existing group
- keep the runtime tool description compact and move detail into the Mintlify page
- do not leave a new agent facing MCP tool undocumented because the docs submodule is missing initialize it or stop and report the blocker
