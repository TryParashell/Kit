# Split substantial definitions into focused files

Keep changes locally understandable and pull requests structurally small by giving every substantial declaration one focused file.

## The rule

A class function definition variable constant data table schema registry adapter strategy or algorithm gets its own file when any of these conditions apply:

- it exceeds 30 logical lines including its directly attached type declarations
- it owns validation state transitions serialization parsing orchestration or another independent responsibility
- it contains a nested helper callback or substantial inline expression
- it changes for a reason different from the surrounding declarations
- it is independently reusable testable replaceable or reviewable
- it makes the containing file require scrolling to understand one responsibility

Treat these as mandatory split signals not optional refactoring suggestions. When uncertain split the declaration.

Small declarations may share a file only when they form one inseparable concept remain below 30 combined logical lines and would have no meaningful independent name or test. Do not create meaningless one line wrapper modules merely to satisfy the rule.

## Scalable module shape

- Default to one substantial exported declaration per file.
- Name the file after the declaration or responsibility it owns.
- Keep feature implementation details beside that feature instead of growing central utility service adapter writer parser or native modules.
- Add new behavior through a new module and one small registry dispatcher factory composition root or public entry point edit.
- Keep registries declarative. A normal feature addition should add one explicit import and one registration entry without modifying unrelated branches.
- Split large constant tables schemas and generated programs from the behavior that consumes them.
- Put shared contracts and types in focused contract modules only when multiple implementations genuinely depend on them.
- Keep tests focused by module and feature so a new implementation normally adds a new test file rather than expanding an unrelated large suite.

## Explicit imports

- Import the exact symbol from its defining module such as `from Package.FeatureWriter import FeatureWriter`.
- Never use wildcard imports in production tests scripts generated code or package facades.
- Treat the steering checkers `IMP001` diagnostic as a merge blocking failure.
- Never import a broad package or module when only one or two symbols are required.
- Never depend on accidental transitive imports.
- Never create convenience barrel modules that re export unrelated implementation symbols.
- Public package entry points may re export intentionally supported public API symbols only. Keep that list explicit and minimal.
- Use type only imports or dependency injection when needed to break cycles instead of merging responsibilities back into one file.
- Remove obsolete imports and re exports in the same change.

## Reviewability gate

Before completing a code change verify:

1. Every substantial declaration owns a focused file.
2. No edited file accumulated a second independent responsibility.
3. New behavior was added primarily through new files plus small composition edits.
4. Every import names the narrowest required symbol and its real defining module.
5. The diff can be reviewed feature by feature without navigating an unrelated monolithic file.

If a change requires repeatedly editing a large central file redesign the extension point before adding the feature.
