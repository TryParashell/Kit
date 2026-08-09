---
name: page-title-separator
description: "Use the double-colon separator in public page titles. Use when editing document metadata, SEO titles, or public landing and marketing routes."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/page-title-separator.md"
  kiro-inclusion: "always"
---
# Page Title Separator — Use `::`

This rule is MANDATORY for every landing page, marketing page, and public-facing route in this workspace (the SolidStart site in `website/` and any Next.js landing app such as `LandingPage/`, `landingPageOld/`, `accountDashboard/`, `agentUi/`). It governs the browser tab title only — the string rendered into the document `<title>` element.

## Rule

The separator between the brand name and the page name in a browser page title MUST be ` :: ` (space, two colons, space). Never use ` | `, ` - `, ` – `, ` — `, or ` • `.

Correct:

```
Parashell :: Download
Parashell :: Privacy Policy
Not Found :: Parashell
```

Forbidden:

```
Parashell | Download
Parashell - Download
Parashell – Download
```

## Where This Applies

- Any string passed to a `<Title>` (SolidStart / `@solidjs/meta`) or Next.js `metadata.title` / `<title>` for a landing or marketing route.
- Title values stored in i18n dictionaries (e.g. `home.title`, `download.title`, `notFound.title`) that are rendered into the document title.
- Title templates (e.g. Next.js `title.template`) MUST use `%s :: Brand` style, not `%s | Brand`.

This rule is about the browser/tab title only. It does NOT change on-page visible headings (`<h1>`, section titles), body copy, or any user-facing text — leave those separators alone.

## Verification

Before considering a landing/marketing page complete, confirm:

1. Every document title uses ` :: ` between brand and page name.
2. No landing-page title ships with ` | `, ` - `, ` – `, ` — `, or ` • ` as the brand/page separator.

If any check fails, the work is not done. Fix it before reporting completion.
