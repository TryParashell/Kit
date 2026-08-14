---
name: hostcontrol-contract
description: "Keep HostControl services, schemas, tests, documentation, and consumers synchronized. Use when changing a HostControl service contract."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/HostcontrolContract.md"
  kiro-inclusion: "always"
---

# HostControl Service Contract — Change All Coupled Files Together

This rule is MANDATORY whenever you add, remove, rename, or change the fields of a HostControl service. It ranks alongside the formatting, React Doctor, no-stubs, and Linear-tracking gates. The HostControl service contract is duplicated across several files that MUST stay in perfect lockstep. Change one without the others and the P0 suite fails CI (exactly the `services keys changed` / `Items in the second set but not the first` failures this rule exists to prevent). If any coupled location is out of sync, the work is NOT done.

## The Core Truth

There is no single source of truth for the HostControl service set — the published artifacts, the JSON Schema, the test contract, the README, and every downstream consumer each encode it independently. A service change is therefore a multi-file change by definition. Touching only `a.json` (or only the schema) is always a bug.

## Rule 1: A Service Change Touches EVERY Coupled Location, In The Same Change

When you add, remove, rename, or re-field any service, you MUST update all of these together:

1. `hostControl/src/a.json` — the published document (`services` object: the service key, its `name`/`desc`/`host`/`ver`, and any `extra_data`).
2. `hostControl/src/schema.json` — the published schema (`services.properties.<svc>`, the `services.required` list, and any `$defs`/extra_data shape for that service).
3. `hostControl/tests/test_hostcontrol.py` — the hard-coded contract constants:
   - `EXPECTED_SERVICES` (the exact service key set),
   - `EXPECTED_SERVICE_FIELDS` (the exact top-level fields per service),
   - `EXPECTED_EXTRA_FIELDS` (the exact `extra_data` fields for services that have them).
4. `hostControl/README.md` — any service listing or documentation that enumerates services.
5. Downstream consumers exercised by `hostControl/tests/test_hostcontrol_consumers.py` — the Python clients (auth, agent, bridge) and the AgentUI consumer that reference service ids. If a consumer must resolve the new/changed service, wire it; the consumer contract tests assert every service is intentionally covered.

Adding a service key to `a.json` and `schema.json` without adding it to `EXPECTED_SERVICES` (and vice versa) is the exact drift that breaks `test_services_are_exactly_the_expected_contract`, `test_document_validates_against_schema`, `test_schema_declares_each_expected_service_property`, and `test_schema_services_required_list_matches_runtime_contract`. Never ship that.

## Rule 2: The Document, Schema, And Test Constants Are Exact Sets — Not Supersets

These comparisons are equality, not subset checks:

- `set(document["services"]) == set(EXPECTED_SERVICES)`
- schema `services.required` and `services.properties` keys `== set(EXPECTED_SERVICES)`
- each service's field set `== EXPECTED_SERVICE_FIELDS[svc]`
- each `extra_data` field set `== EXPECTED_EXTRA_FIELDS[svc]`

So an extra key OR a missing key both fail. When you add `foo`, add it to all three. When you remove `foo`, remove it from all three. When you add a field to a service, update both the artifact and the corresponding `EXPECTED_*` entry.

## Rule 3: Run The P0 Suite Before Declaring Done

After any HostControl service/field change, run the exact suite CI runs, from `hostControl/`:

```bash
uv run python -m unittest discover -s tests -v
```

(Use `uv` per the Python package manager rule — HostControl is outside `Parashell/` and `modules/`.) The change is complete only when this reports zero failures, including both `test_hostcontrol.py` and `test_hostcontrol_consumers.py`. Treat a failure here the same as a failing formatter check: keep working until it is clean. Do not "fix" a failure by weakening or deleting the contract assertions — update the real contract in all coupled locations.

## Verification

Before considering any HostControl service change complete, confirm:

1. The service key set is identical across `a.json`, `schema.json` (`required` + `properties`), and `EXPECTED_SERVICES`.
2. Every changed service's fields match between the artifact and `EXPECTED_SERVICE_FIELDS`, and its `extra_data` matches `EXPECTED_EXTRA_FIELDS`.
3. The README and any affected downstream consumers were updated in the same change.
4. `uv run python -m unittest discover -s tests -v` from `hostControl/` passes with zero failures.

If any check fails, the work is not done. Fix it before reporting completion.
