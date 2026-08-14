---
name: repository-structure
description: "Enforce repository path naming, semantic folder density, exact imports, extension modules, SOLID boundaries, and security-quality verification. Use when creating, renaming, moving, organizing, importing, or securing project files."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/RepositoryStructure.md"
  kiro-inclusion: "always"
---

# Repository structure and security quality

Keep the repository easy to extend by making paths predictable responsibilities narrow and verification mandatory

## Project owned path names

- Name every project owned file stem with PascalCase ASCII letters only
- Never place a digit in a project owned file stem and never add numeric sequence suffixes
- Name project owned semantic directories with PascalCase ASCII letters when an ecosystem does not prescribe their spelling
- Use names that state one stable responsibility rather than generic buckets such as misc common helpers utils or temp
- Rename references imports documentation manifests tests and ownership rules in the same change
- Preserve lowercase package directories only when an existing public import identity requires them
- Keep those compatibility packages as minimal facades with an explicit public surface and PascalCase implementation modules below them

The only filename exceptions are exact names required by a language package manager operating system repository host or Agent Skills specification such as `__init__.py` `conftest.py` `pyproject.toml` `uv.lock` hidden configuration files and `SKILL.md`

Standard repository governance names and copied third party assets may retain externally required spelling Do not invent a new exception when a project owned PascalCase name works Vendor and CAD fixture leaf names under `examples/` may retain their original identity but project authored files there still follow this rule

## Folder density

- Keep at most 32 direct files in every project owned directory
- Split a directory into cohesive domain feature format phase or responsibility subfolders before adding the thirty third direct file
- Never evade the cap with numbered folders numbered files arbitrary alphabet ranges or catch all buckets
- Keep every file beside its closest owner and keep focused tests in the matching semantic test tree
- Exclude only externally named example fixtures generated output caches dependencies and vendored trees from density enforcement

## Extension model

- Give every independently selectable reverse engineering method parser serializer writer adapter strategy and validation rule its own focused module and focused test file
- Add a new behavior by creating its module importing its exact public symbol and adding one declarative registry or composition entry
- Keep registries declarative and free of feature specific control flow
- Keep a generated serializer method table whole when it is the atomic representation of one natural recovered method and deterministic generation plus decomposition equivalence verify it Do not split it into numbered size based or otherwise arbitrary chunks
- Prefer one substantial exported declaration per file and apply `SplitLargeDefinitions.md` at every boundary
- Share immutable format facts through focused schema or catalog modules rather than copying large tables between implementations
- Keep compatibility facades thin and never place implementation logic in `__init__.py`

## Exact dependencies

- Import symbols from their real defining modules
- Never use wildcard imports in production tests scripts generated code or package facades
- Never rely on transitive imports or broad convenience barrels
- Re export only intentionally supported public API symbols through an explicit minimal list
- Break cycles with focused contracts type only imports or dependency injection instead of merging responsibilities
- Treat `IMP001` from the steering checker as a merge blocking failure

## SOLID boundaries

- Keep each module class and function responsible for one reason to change
- Extend behavior through new implementations and stable registries instead of growing central condition chains
- Require interchangeable implementations to honor the same input output error and state contract
- Expose the smallest interface each consumer needs
- Depend on contracts at orchestration boundaries and inject concrete integrations at composition roots
- Remove duplication obsolete aliases dead branches and misleading abstractions during the same structural change

## Required comments

- Start every new non exempt text file with the exact repository SPDX notice
- Put the required rationale comment above every Python class function lambda and module binding exactly as defined by `RationaleComments.md`
- Document public contracts when the language tooling requires API documentation
- Do not add mechanical narration inline explanations or blanket comments beyond required license rationale pragma and public contract documentation
- Treat missing required comments and unnecessary comments as merge blocking failures

## Security and quality verification

- Run CodeQL over every supported repository language with both the `security-and-quality` and `security-experimental` suites the local threat model in automation and the `all` threat model during maximal local audits
- Analyze ungrouped results from a fresh database built from a frozen complete tracked source set and record the query file raw finding and configured finding counts
- Inspect every CodeQL result regardless of severity precision or classification and fix the underlying code before merge
- Never hide path injection command injection regular expression denial of service definite timing attack or other security results with exclusions query removal baseline resets or suppressions
- Fix path flows with resolved fixed root containment command flows with strict allowlists and argument list subprocess calls and unsafe regular expressions with bounded escaped possessive or deterministic parsing
- Add a CodeQL barrier model only for a concrete validated boundary with focused regression tests and keep every modeled function and dataflow kind explicit
- Keep query exceptions limited to `py/not-named-self` `py/not-named-cls` `py/possible-timing-attack-sensitive-info` and `py/possible-timing-attack-against-hash` because the first pair conflicts with required PascalCase receivers and the second pair covers documented comparisons of nonsecret CAD structure and hash heuristics
- Keep definite timing queries enabled and reject any broader identifier timing path command or regular expression filter
- Store the maximal configuration suite and model sources below `.github/CodeQL/` and prepare the exact lowercase `.github/codeql/extensions/` ecosystem path before GitHub CodeQL initialization
- Document a narrow false positive only when evidence proves the exact result impossible and keep that exception reviewable tested and adjacent to the relevant check
- Include Actions Python and Java tracked sources in the audit and state that Java `build-mode: none` does not prove build integration or dependency resolution
- Run the native strict analyzer for languages and artifacts CodeQL does not cover and do not describe unsupported input as clean
- Run final local verification directly on native Windows when Windows is the target and never substitute WSL results for the bare metal run
- Keep custom repository checks for path casing digits folder density identifier rules exact imports comments and steering synchronization because CodeQL does not replace project policy
- Run focused tests full end to end verification formatters steering checks and security analysis after structural changes
- Leave no notices warnings alerts failing checks stale generated skills or known quality defects when handing work off

## Completion gate

Before completing a change verify that every added moved and modified path follows the naming rules every directory stays below the density cap every import is exact each new behavior is independently extensible all required comments are present and every security quality and end to end check passes
