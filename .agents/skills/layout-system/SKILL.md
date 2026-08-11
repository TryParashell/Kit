---
name: layout-system
description: "Use existing global layout primitives and avoid hand-rolled layout. Use when changing React or Next.js page layout, shells, or spacing."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/layout-system.md"
  kiro-inclusion: "always"
---

# Layout System — Use globals.css, Never Hand-Roll Layout

This is MANDATORY for every page, view, and component in this workspace. It ranks alongside the formatting, React Doctor, no-stubs, shadcn-pages, and design-system-discipline gates. The layout primitives are already defined once in `src/app/globals.css`. You CONSUME them. You do not reinvent page width, gutters, centering, or spacing with arbitrary utilities. If a page hand-rolls layout that globals.css already provides, the work is NOT done — fix it before reporting completion.

## Rule 1: Wrap Page Content In The Shared Layout Classes

Every page's top-level content container MUST use the layout classes defined in `globals.css`. Never substitute arbitrary width/padding/margin utilities for them.

- `page-shell` — standard page content wrapper (max-width `--max-width-container`, centered via `margin-inline: auto`). This is the default for a page's `<main>`.
- `page-section` — full-width section band with vertical rhythm.
- `page-prose` — narrow reading-width content.
- `container` — responsive max-width container with token gutters.
- `two-column-section`, `grid-24`, `site-header-inner` — for their specific documented use cases.

The established page shape in this workspace (match it):

```tsx
export default function Page() {
  return (
    <main className="page-shell flex flex-1 flex-col justify-center py-24">
      <h1 className="font-heading text-3xl font-semibold tracking-tight text-foreground">
        Title
      </h1>
    </main>
  );
}
```

## Rule 2: FORBIDDEN — Arbitrary Layout Utilities On Page Containers

These are banned for page/section width, centering, and gutters when a globals.css class exists:

- Arbitrary horizontal padding as the page gutter: `px-16`, `px-12`, `px-[64px]`, etc. The gutter comes from `page-shell` / `container` (`--spacing-g2`).
- Hand-rolled max-widths for the page frame: `max-w-3xl`, `max-w-7xl`, `max-w-[1300px]` on the page container. Use `page-shell` / `--max-width-container`.
- Manual centering math: `mx-auto` + `max-w-*` to re-create what `page-shell` already does.
- Raw viewport math (`w-[calc(100vw-...)]`, `ml-[calc(50%-50vw)]`) duplicating `page-shell` / `two-column-section`.

Constraining inner content (e.g. `max-w-2xl` on a heading or `max-w-prose` on a paragraph) is fine. The ban is on re-inventing the PAGE FRAME.

## Rule 3: Spacing & Type Come From Tokens

- Vertical rhythm uses token spacing (`py-24`, the `--spacing-g*` scale), consistent with sibling pages — not arbitrary one-off values picked by feel.
- Headings use `font-heading`; surfaces use theme tokens (`text-foreground`, `text-muted-foreground`, `bg-background`) per `design-system-discipline.md` and `shadcn-pages.md`.

## Rule 4: Match Sibling Pages

Before writing a new page, read an existing one (`src/app/pricing/page.tsx`, `src/app/open-source/page.tsx`) and mirror its structure exactly. A new page that does not visually align with its siblings' frame is wrong.

## Verification

Before considering any page/view complete, confirm:

1. The top-level content container uses a `globals.css` layout class (`page-shell` / `page-section` / `container` / etc.) — zero hand-rolled page frames.
2. No arbitrary gutter padding, max-width, or centering math re-creates what globals.css already provides.
3. Spacing and typography use tokens (`py-24`, `font-heading`, theme color tokens), consistent with sibling pages.

If any check fails, the work is not done. Fix it before reporting completion.
