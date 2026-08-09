---
name: frontend-stack
description: "Use the required Next.js, React, shadcn, and frontend stack. Use when scaffolding, upgrading, or changing frontend applications."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/frontend-stack.md"
  kiro-inclusion: "always"
---
# Frontend Technology Stack

Any frontend work in this workspace MUST use the stack defined below. This applies to new projects, new features, and any refactor that touches the frontend. Do not substitute alternative frameworks, component libraries, or data-fetching layers without explicit instruction from the user.

## Required Technologies

### Next.js 16+

All frontends are built on Next.js, version 16 or higher, using the App Router.

Before scaffolding, web search for the current latest stable release of Next.js and pin to that major version (minimum 16). At the time this rule was written the latest stable line was 16.2. If a newer major exists, prefer it unless the user states otherwise.

Verify the resolved version after install:

```bash
pnpm why next
```

### React (latest)

Use the latest stable release of React and `react-dom`. Web search for the current version before installing rather than assuming a fixed number. At the time of writing the latest stable line was 19.2.x.

React and `react-dom` versions MUST match each other exactly, and MUST satisfy the minimum React version required by the installed Next.js release.

### ShadCN

Initialize ShadCN with the exact command below. It targets Next.js with the `b0` preset:

```bash
pnpm dlx shadcn@latest init --preset b0 --template next --pointer
```

Add components through the ShadCN CLI (`pnpm dlx shadcn@latest add <component>`) rather than hand-copying source, so the registry and dependency resolution stay correct.

Use the MCP to its maximum to interface with ShadCN

Immediately after the ShadCN init completes, install the full MagicUI component set by default:

```bash
pnpm dlx shadcn@latest add @magicui --all -y
```

This is not optional. Every fresh frontend gets MagicUI added right after ShadCN, before any feature work begins.

### MagicUI

MagicUI is added as part of the standard ShadCN setup (see the command above). Treat MagicUI components as available building blocks for animated and decorative UI, and add any additional MagicUI items through the ShadCN CLI/registry rather than hand-copying source.

### Paper Shaders

Install Paper Shaders by default as part of every frontend setup:

```bash
pnpm add @paper-design/shaders-react
```

Use `@paper-design/shaders-react` for shader-based backgrounds and effects. Add this package whenever scaffolding a new frontend, alongside the ShadCN and MagicUI setup.

### Radix UI (latest)

Use the latest stable release of the unified `radix-ui` package. Web search for the current version before installing.

Import primitives from the single `radix-ui` package, not the individual legacy `@radix-ui/react-*` packages:

```ts
import { Popover, Dialog } from "radix-ui";
```

### tRPC (latest)

Use tRPC for the typesafe API layer between the Next.js frontend and the backend. Web search for the current latest stable major before installing; at the time of writing this was v11.

Install the client, server, and the React Query integration together, keeping all `@trpc/*` packages on the same version:

```bash
pnpm add @trpc/server @trpc/client @trpc/react-query @trpc/next @tanstack/react-query
```

Define routers and procedures on the server, infer types on the client, and never duplicate request or response type definitions by hand.

### Lucide Icons

Use Lucide for all iconography. Install the current Lucide package.

Do not pull in other icon sets (Phosphor, Heroicons, react-icons, etc.) for new work. Standardize on Lucide so weights and sizing stay consistent across the UI.

## Package Manager

Use `pnpm` for all installs, scripts, and the ShadCN initializer (`pnpm dlx`). Do not mix in `npm` or `yarn` within the same project.

## Version Resolution Workflow

Whenever you scaffold or upgrade a frontend:

1. Web search for the latest stable version of Next.js, React, Radix UI, and tRPC.
2. Pin Next.js to its latest major (minimum 16) and install the latest stable of the others.
3. Confirm React and `react-dom` satisfy the Next.js minimum and match each other.
4. Run the ShadCN init command exactly as specified above.
5. Add the full MagicUI set with `pnpm dlx shadcn@latest add @magicui --all -y`.
6. Install Paper Shaders with `pnpm add @paper-design/shaders-react`.
7. Verify installed versions with `pnpm why <package>` before continuing.
