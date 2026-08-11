---
name: design-system-discipline
description: "Apply shared design-system primitives and UI composition rules. Use when designing or modifying React or Next.js pages, views, or components."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/design-system-discipline.md"
  kiro-inclusion: "always"
---

# Design System Discipline — Mandatory

This file encodes how serious frontend teams keep UIs consistent. It is NON-NEGOTIABLE for every page, view, and component in any Next.js/React app in this workspace. It ranks alongside the formatting, React Doctor, no-stubs, component-architecture, and shadcn-pages gates. The governing principle: **architect the system so the easiest thing to do is the correct thing.** If a page hand-rolls structure or values that the system already provides, the work is NOT done.

## Rule 1: Use The Design System. Never Hand-Roll Primitives.

The visual rules are defined once — spacing scale, typography, colors, radii, shadows, breakpoints, and the styles for button/input/card/table plus page chrome (navbars, sidebars, headers, empty states, modals). You consume them. You do not reinvent them.

Required:

```tsx
<Button variant="primary" size="md">
  Save changes
</Button>
```

FORBIDDEN:

```tsx
<button className="bg-blue-500 px-3.5 py-[9px] rounded-[6.25px]">
  Save changes
</button>
```

No hand-rolled buttons, inputs, cards, or tables when a system component exist s. Variant/size props express intent; arbitrary one-off class soup is entropy and is rejected.

## Rule 2: Shared Layout Components. Pages Don't Invent Structure.

Pages control the CONTENT area only — never the global layout. Wrap pages in the standard shells:

```tsx
<AppShell>
  <PageHeader title="Billing" description="Manage invoices and plans" />
  <PageContent>
    <BillingTable />
  </PageContent>
</AppShell>
```

In the Next.js App Router, enforce shared layout through `layout.tsx` per segment so every route inherits the same chrome:

```tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AppShell>
      <Sidebar />
      <main className="min-h-screen">{children}</main>
    </AppShell>
  );
}
```

A `page.tsx` MUST be thin — it renders an approved page/template component, nothing more:

```tsx
export default function Page() {
  return <SettingsPage />;
}
```

Do not put bespoke layout markup, max-widths, or padding math in route files.

## Rule 3: Design Tokens. Never Hardcoded Values.

Use named tokens for spacing, color, radius, typography. Lock them into the Tailwind theme / CSS variables and consume them by name:

```ts
theme: {
  extend: {
    spacing: { page: "2rem", section: "1.5rem" },
    colors: { brand: { DEFAULT: "#4C8DFF" } },
  },
}
```

No page gets `37px` of padding because of a feeling. No raw hex in markup (`text-[#3b82f6]`), no inline pixel margins (`style={{ marginTop: 13 }}`), no arbitrary one-off values for foundational surfaces. This reinforces the token rule in `shadcn-pages.md`.

## Rule 4: Page Templates. Compose From Approved Patterns.

Prefer an approved page template over composing a page from scratch. The standard patterns: list, detail, settings, dashboard, form, empty-state, onboarding, error.

```tsx
<EntityListPage
  title="Customers"
  description="Manage customer accounts"
  actions={<CreateCustomerButton />}
  table={<CustomersTable />}
/>
```

The target shape for a real page in this workspace is boring on purpose:

```tsx
export default function ModelsPage() {
  return (
    <Page
      title="Models"
      description="Configure available inference providers and model routing."
    >
      <ModelsTable />
    </Page>
  );
}
```

Boring page files. Powerful shared components.

## Rule 5: Component Ownership. Don't Clone, Don't Fork.

Important components are owned by the shared layer. You CONSUME them; you do not clone a card and "just make it better." That is how a codebase ends up with nineteen different cards.

- Need a new shared behavior? Extend the shared component (or propose adding it there), don't fork a private copy into a feature folder.
- This is the same boundary as `component-architecture.md` Rule 2 and `shadcn-pages.md` Rule 5: generated/shared primitives are protected. Compose and wrap; don't duplicate or silently patch.

## Rule 6: Shared Packages / Monorepo Structure.

Frontend in this workspace is organized so all apps share one UI layer, one Tailwind config, one layout system, one lint config. Target structure:

```
apps/
  web/
packages/
  ui/            button.tsx, card.tsx, input.tsx, dialog.tsx, table.tsx
  layouts/       app-shell.tsx, page.tsx, page-header.tsx, settings-layout.tsx
  theme/         tailwind.config.ts, tokens.ts
  eslint-config/
  tsconfig/
```

When adding or refactoring frontend code: put reusable components, layouts, tokens, and configs in the shared packages — not copied per app. Application code imports from the shared layer (`@company/ui`, `@company/layouts`, `@company/design-tokens` style packages). Respect the existing monorepo wiring (this aligns with the `--monorepo` ShadCN init in `frontend-stack.md`). Do not introduce a second, divergent Tailwind config or UI copy inside an app.

## Rule 7: Make Inconsistency Hard (Lint + Constraints).

Enforce the system through tooling, not vibes. When working in this workspace:

- Do not write banned patterns: inline style numeric values (`style={{ marginTop: 13 }}`), raw color classes (`text-[#3b82f6]`), arbitrary radius/spacing literals for foundational surfaces, or direct imports that bypass the shared UI layer.
- Prefer semantic, token-driven props (`<Text tone="brand">`) over arbitrary utility soup.
- If you see or add lint rules / forbidden-import constraints that enforce the design system, honor them — never disable or work around them to ship faster (consistent with the React Doctor and no-stubs gates).

## Rule 8: Document & Protect States.

Every shared component must account for its real states, not just the happy path: default, loading, error, empty, disabled, mobile, dark mode, long-text overflow. When you build or modify a shared component, handle these states (use `Skeleton` / `Alert` / designed empty states per `shadcn-pages.md`). Where a Storybook or component catalog exists, keep it in sync as the source of truth.

## Rule 9: Visual Stability.

Shared spacing/layout changes have blast radius across many pages. When you change a shared token, layout, or primitive:

- State which surfaces are affected and verify they still render correctly.
- Where visual regression tooling (Chromatic, Percy, Playwright screenshots, Argos, Loki) exists, do not bypass it; treat a failing screenshot diff like a failing test.

## Rule 10: Figma-To-Code Discipline.

Keep code aligned with the design source. React components match design components; tokens stay in sync; no random one-off layouts unless explicitly approved by the user. When a request would diverge from the established system, flag it and get approval rather than quietly inventing a new pattern.

## Verification

Before considering any page or React view complete, confirm:

1. Every primitive comes from the design system / shared UI — zero hand-rolled buttons/inputs/cards/tables.
2. Global layout comes from shared shells (`AppShell` / `layout.tsx` / `Page`); `page.tsx` files are thin and render approved page components.
3. All values are tokens — no raw hex, inline pixel styles, or arbitrary spacing/radius literals for foundational surfaces.
4. Reusable components, layouts, tokens, and configs live in the shared layer, not copied per app.
5. No shared/owned component was cloned, forked, or silently patched (per `component-architecture.md` and `shadcn-pages.md`).
6. Real component states (loading/error/empty/disabled/long-text) are handled, and shared-change blast radius was checked.

If any check fails, the work is not done. Fix it before reporting completion.
