---
name: no-unrequested-styling
description: "Limit UI changes to the requested scope. Use when changing pages, visual styling, layout, or components."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/no-unrequested-styling.md"
  kiro-inclusion: "always"
---

# No Unrequested Styling — Do Only What Was Asked

This is MANDATORY for every page, view, and component in this workspace. It ranks alongside the formatting, React Doctor, no-stubs, shadcn-pages, design-system-discipline, and layout-system gates. The governing principle: **apply only the styling the user explicitly asked for. Do not add styling decisions they did not request.** If you add a visual property the user never mentioned, the work is NOT done correctly — remove it.

## Rule 1: Only Apply What Was Requested

When the user asks for content or a specific change, add ONLY that. Do not bundle in extra visual decisions they did not ask for.

FORBIDDEN unless the user explicitly asked for it:

- Font weight (`font-semibold`, `font-bold`, `font-medium`, etc.).
- Font size beyond what is required to render (`text-4xl`, `text-2xl`, etc.) when not specified.
- Letter spacing (`tracking-tight`, `tracking-wide`).
- Line height (`leading-tight`, `leading-8`).
- Colors, decoration, shadows, borders, animations, hover effects.
- Extra max-widths, padding, or margins beyond the layout-system requirement.

If the user said "add the title X pushed to the left," you add the text, left-aligned, in the shared layout frame — and NOTHING else. No weight, no size bump, no tracking, no decoration.

## Rule 2: Inheriting From Siblings Is Not License To Add Style

Mirroring sibling pages (per `layout-system.md` Rule 4) applies to the LAYOUT FRAME (`page-shell`, token spacing, structure). It does NOT mean copying every typographic class a sibling chose. Do not justify an unrequested `font-semibold` / `tracking-tight` / `text-4xl` by saying "the sibling page does it." Copy the frame, not the unrequested decoration.

## Rule 3: When In Doubt, Less Is Correct

If you are unsure whether a styling property was requested, leave it out. The minimal, unstyled-beyond-tokens version is the correct default. The user can always ask for weight, size, or emphasis afterward. Adding it preemptively is wrong.

## Rule 4: Ask, Don't Assume

If a request genuinely seems to need a styling decision you are unsure about, ask the user rather than picking one and applying it silently.

## Verification

Before considering any styling change complete, confirm:

1. Every visual property in the diff traces directly to an explicit user request or a mandatory token/layout-system requirement.
2. No font weight, size, tracking, leading, color, or decoration was added that the user did not ask for.
3. Sibling-page mirroring was limited to the layout frame, not unrequested typographic styling.

If any check fails, the work is not done. Remove the unrequested styling before reporting completion.
