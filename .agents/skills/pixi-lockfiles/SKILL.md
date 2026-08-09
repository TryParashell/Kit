---
name: pixi-lockfiles
description: "Relock Pixi manifests. Use whenever editing pixi.toml, Pixi dependencies, environments, or channels."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/pixi-lockfiles.md"
  kiro-inclusion: "always"
---
# Pixi Manifests — Always Relock Before Finishing

This rule is MANDATORY whenever you touch a `pixi.toml` in this workspace. It ranks alongside the formatting, React Doctor, no-stubs, and HostControl-contract gates. A dependency change is not done when the manifest is edited — it is done when the matching `pixi.lock` has been regenerated and the solve has actually succeeded. An edited manifest with a stale lock is a broken build, because CI and the packaging scripts install from the lock, not the manifest.

## Scope

Every pixi manifest in the workspace, each with its own lock beside it:

- `Parashell/pixi.toml` — the source build and development environment.
- `Parashell/package/rattler-build/pixi.toml` — the packaging environment. This is the one whose `default` environment the bundle scripts copy into shipped artifacts, so a dependency only reaches users if it is here.
- `Parashell/src/3rdParty/pivy/pixi.toml` — the vendored pivy build.

If you add a manifest, it falls under this rule too.

## Rule 1: Relock Every Manifest You Edited

Run `pixi lock` from the directory containing the edited `pixi.toml`, once per edited manifest:

```bash
pixi lock
```

Relocking one manifest does not relock the others. If a change spans several manifests, run it in each directory.

Do not hand-edit `pixi.lock`, and do not commit a manifest change with an untouched lock.

## Rule 2: The Solve Must Succeed

`pixi lock` must exit zero. Treat a failed solve exactly like a failing formatter or test: keep working until it is clean, or revert the dependency change. Never leave the workspace with a manifest the solver rejects.

Locking resolves every platform the manifest declares, so a dependency that is missing on one platform fails the whole solve. Read the manifest's `platforms` list and confirm the package exists for all of them before adding it — the lists are not identical across manifests. `Parashell/pixi.toml` and `Parashell/package/rattler-build/pixi.toml` both target `linux-64`, `linux-aarch64`, `osx-arm64`, and `win-64`, while `Parashell/src/3rdParty/pivy/pixi.toml` also targets `osx-64`.

Use `[target.<platform>.dependencies]` for a genuinely platform-specific dependency rather than dropping a platform from the manifest.

## Rule 3: Verify The Lock Changed The Way You Expected

After a successful relock, confirm the diff matches your intent — the packages you added are present for every platform, and nothing unrelated was silently added, removed, or version-bumped. A stale lock can re-solve into unrelated upgrades that change the shipped runtime.

The raw line diff of a lock is large and mostly re-serialization, so compare the resolved artifact set rather than reading the diff. `pixi lock` also prints the added and removed packages per environment; capture that output and check it.

## Rule 4: Understand PyPI Pins Before Adding A PyPI Dependency

Pixi pins `[pypi-dependencies]` to the versions the conda solve already chose. A PyPI package whose requirements conflict with a conda-resolved version fails to solve, reported as a pinned-package conflict.

When that happens, do NOT loosen or downgrade the conda side to satisfy the PyPI package unless that version is genuinely correct for the application. Constraining what the app ships in order to satisfy a tool the app only invokes as a subprocess is the wrong trade, and it has to be redone on every upstream bump. Prefer a conda package when one exists, otherwise isolate the tool outside the environment. Fix the conflict at its cause and state the tradeoff rather than chasing pins one at a time.

## Rule 5: Shipping Requires The Packaging Manifest And The Bundle Scripts

Adding a runtime dependency to `Parashell/pixi.toml` alone does not ship it. For a dependency that must reach users:

- Add it to `Parashell/package/rattler-build/pixi.toml`, and to the `run:` requirements in `Parashell/package/rattler-build/recipe.yaml` when it is a conda package.
- Check the bundle scripts. `windows/create_bundle.sh` copies only named executables from `Library/bin` plus `*.dll`, and `linux/create_bundle.sh` and `osx/create_bundle.sh` rebuild `bin/` from an explicit allowlist. A new executable that is not listed is silently dropped from the shipped artifact.

## Verification

Before considering any pixi manifest change complete, confirm:

1. `pixi lock` was run in every directory whose `pixi.toml` you edited, and each exited zero.
2. The resolved artifact set changed only as intended, for every platform.
3. No `pixi.lock` was hand-edited.
4. A dependency meant to ship is present in the packaging manifest, the recipe when applicable, and the bundle scripts.

If any check fails, the work is not done. Fix it before reporting completion.
