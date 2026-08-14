---
name: shadcn-pages
description: "Follow the shadcn UI CLI-first composition method. Use when adding UI primitives or building React and Next.js pages."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/ShadcnPages.md"
  kiro-inclusion: "always"
---

# Building Pages with ShadCN — Mandatory Method

This file encodes how the creators of shadcn/ui say to build interfaces. It is NON-NEGOTIABLE for every page, view, and component in any Next.js/React app in this workspace. It ranks alongside the formatting, React Doctor, no-stubs, and component-architecture gates. If a page violates this method, the work is NOT done — rebuild it the right way.

## The Core Truth

shadcn/ui is NOT a traditional component library you import and forget. It is a code-distribution system: the CLI copies real, owned source into the project, and you compose product UI out of those primitives. Your job is never "make the component work." Your job is to compose pages that are deliberate, high-signal, consistent, and built from the design system — not hand-rolled markup.

The four principles you build by, every time: **Open Code, Composition, Distribution, Beautiful Defaults.**

## Rule 1: CLI-First, Always. Never Hand-Copy.

- Add every primitive through the CLI: `pnpm dlx shadcn@latest add <component>`. Never hand-paste component source from the docs or another project.
- Before using an unfamiliar primitive, pull its real API and examples: `pnpm dlx shadcn@latest docs <component>` (and `view`/`search` as needed). Use the ShadCN MCP to its maximum for this.
- Prefer installing existing blocks/registry items over building a layout from scratch when one fits.
- Run diagnostics with `pnpm dlx shadcn@latest info` when the setup is unclear.

## Rule 2: Compose From Primitives. Never Hand-Roll What Exists.

You MUST reach for the shadcn primitive before writing raw markup. These are FORBIDDEN when a primitive exists:

- Raw `<button>` / `<input>` / `<select>` / bare `<div>` shells when `Button` / `Input` / `Select` / a real primitive exists.
- Repeating `div rounded-xl border p-6` instead of `Card` / `Tabs` / `Table` / `Sheet` / `Dialog`.
- Using `Dialog` for destructive confirmation instead of `AlertDialog`.
- Nesting cards inside cards inside cards.
- Shipping empty / loading / error states with no design treatment (use `Skeleton`, `Alert`, designed empty states).

### Reach for this first

| Use case                | Compose from                                                                     |
| ----------------------- | -------------------------------------------------------------------------------- |
| Settings page           | `Tabs` + `Card` per group + `Separator` + explicit save action                   |
| Data dashboard          | summary `Card`s + filter bar + `Table` + `Badge` + `DropdownMenu`                |
| CRUD table              | `Table` + `DropdownMenu` + `Sheet` + `AlertDialog` for destructive               |
| Entity detail           | header + status `Badge` + main `Card` + side `Card` + `AlertDialog`              |
| Auth / onboarding       | centered `Card` + `Label` + `Input` + `Button` + inline `Alert`                  |
| Global search           | `Command` + `Dialog` (keyboard-first)                                            |
| Pickers                 | `Popover` + `Command`                                                            |
| Mobile nav / filters    | `Sheet` + `Button` + `Separator`; persistent desktop filters in a `Card` sidebar |
| Empty / loading / error | `Card` + `Skeleton` + `Alert`                                                    |

## Rule 3: Build On Tokens. Never Ad-Hoc Hex Or Palette Classes.

- Build core surfaces from theme tokens ONLY: `bg-background`, `bg-card`, `text-foreground`, `text-muted-foreground`, `border-border`, `ring-ring`. No ad-hoc hex values or arbitrary Tailwind palette classes for foundational surfaces.
- One accent color, applied through `--color-primary`. Do not let multiple accent colors fight.
- Keep radius consistent. `--radius: 0.625rem` is the baseline; derive the rest from it.
- One density system per page: comfortable (`gap-6` / `p-6` / `text-sm`) or compact (`gap-4` / `p-4` / `text-sm`). Do not mix arbitrary spacing/radius values.
- Add app-specific colors as `--color-*` tokens in `@theme inline`, then consume them as classes/`var()` — never sprinkle raw values across components.

## Rule 4: Beautiful Defaults, Deliberate Density

- Use the `new-york` style for product, dashboard, AI, admin, and developer-facing surfaces.
- Default to dark mode for dashboards, AI apps, internal tools, and settings. Use light mode only for clearly content-first / editorial products.
- Keep iconography quiet and consistent (this workspace standardizes on Phosphor per the frontend-stack rule; render at consistent sizes like `size={16}`/`size={20}`).
- Avoid decoration noise: no large gradients or glassmorphism on every surface. Effects (including MagicUI / Paper Shaders) are deliberate accents, not the baseline.

## Rule 5: Open Code vs. The Third-Party Boundary (READ THIS)

shadcn's "Open Code" principle means the `components/ui/*` source is yours to OWN and extend the shadcn-sanctioned way — e.g. adding a `cva` variant or a token to the component source when the design system genuinely needs it. That is a deliberate design-system decision.

This does NOT override the workspace boundary rules:

- Do NOT silently patch `components/ui/*` to work around a bug, to "fix" a React Doctor / lint finding, or for convenience. The `ReactDoctor.md` boundary and `ComponentArchitecture.md` Rule 2 still apply: treat generated primitives as protected.
- Default to composition: wrap the primitive in your OWN dedicated component file and extend via props / `className` / `cn()`.
- Only edit `components/ui/*` source for the legitimate shadcn extension pattern (adding a variant/token to the design system), and when doing so get explicit user approval first per `ComponentArchitecture.md`. State the file and the exact change, then wait for a clear yes.
- Never reformat, restyle, or refactor generated primitives.

## Rule 6: Page Anatomy

Every page is composed, not pasted:

1. Identify the use case and pick the primitives from the "Reach for this first" table.
2. Install missing primitives via the CLI.
3. Build each distinct UI unit as its own dedicated component file (per `ComponentArchitecture.md` — no inline/nested components).
4. Lay out surfaces with tokens and one density system.
5. Design the empty, loading, and error states — not just the happy path.
6. Use `AlertDialog` for anything destructive.
7. Keep one accent, consistent radius, consistent icon sizing.

## Gotchas You MUST Handle

- After `shadcn init` on Next.js + Tailwind v4, fix the Geist font: in `@theme inline` use literal family names (`--font-sans: "Geist", "Geist Fallback", ui-sans-serif, system-ui, sans-serif;`), NOT `var(--font-sans)` (circular) and NOT `var(--font-geist-sans)` (unresolvable at parse time). Put the font variable classNames on `<html>`, not `<body>`.
- shadcn primitives size via Tailwind classes, not a `size` prop (e.g. `Avatar` has no `size` prop — use `className="h-12 w-12"`).
- Many components need a provider at the root (e.g. `TooltipProvider`). Wire required providers in the layout.

## Verification

Before considering any page or React view complete, confirm:

1. Every interactive element uses a shadcn primitive where one exists — zero hand-rolled buttons/inputs/selects/card shells.
2. Surfaces use theme tokens; no ad-hoc hex or arbitrary palette classes for foundational surfaces.
3. One accent, consistent radius, one density system, consistent icon sizing.
4. Empty/loading/error states are designed; destructive flows use `AlertDialog`.
5. Every component lives in its own dedicated file (per `ComponentArchitecture.md`).
6. No generated `components/ui/*` source was modified without explicit approval.

If any check fails, the work is not done. Fix it before reporting completion.
