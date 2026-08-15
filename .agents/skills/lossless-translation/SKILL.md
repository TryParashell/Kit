---
name: lossless-translation
description: "Hold every format translation to lossless, vendor loadable, application usable, and parametric output verified in the target application. Use when converting between CAD formats or reporting translation results."
license: LicenseRef-PolyForm-Strict-1.0.0
metadata:
  source: ".kiro/steering/LosslessTranslation.md"
  kiro-inclusion: "always"
---

# THE ONLY ACCEPTANCE CRITERION: LOSSLESS, VENDOR LOADABLE, APPLICATION USABLE, PARAMETRIC

This is the acceptance gate for every translation this workspace performs. It outranks progress reports, partial results, and your own sense that a hard problem has been worked hard enough. It sits alongside `NoDonorBlocks.md` and `NoStubs.md`.

## THE CRITERION

For any source format S and target format T, the question is exactly one question:

**Does this losslessly translate from S to T?**

If the answer is not an unqualified **yes**, the work is not done. And "yes" requires all four of these to be true at once, measured against the target application:

1. **Lossless** — the feature tree, sketches, dimensions, constraints, planes, origin, bodies and geometry that existed in the source exist in the output. Nothing silently dropped.
2. **Vendor loadable** — the target application opens the file. Not "opens with warnings and nothing in it". Opens.
3. **Application usable** — the target application shows the model. Solid bodies present, correct volume, correct centre of mass, verified against a control.
4. **Parametric** — the feature tree is live and editable in the target application. Dimensions drive geometry. A rebuild works. Not a dumb solid, not a mesh, not a carrier.

Four out of four, or it is not done.

## WHAT IS NOT AN ACCEPTABLE OUTCOME

Every one of these is a failure state, not a result. Reporting any of them as an outcome is the violation this rule exists to stop:

- **A file that opens with zero solid bodies.** This is the specific failure that motivated this rule. "It loads in SOLIDWORKS" with `bodies=0`, no mass, and only document-state folders in the tree is **not a pass**. It is a file that opens and contains nothing.
- A file that opens showing an empty viewport.
- A file that opens but shows no feature tree, no planes, no origin, no sketches.
- A carrier — a container holding neutral Kit data the target application cannot read.
- A file whose geometry is baked and unparametric when the source was parametric.
- `vendor_loadable = False` or `application_usable = False`, honestly attested. Honest attestation is required and is a virtue, but an honestly-attested unusable file is still an unusable file and still unfinished work.
- A partial result offered with an explanation of why the rest is hard.
- Round-trip byte identity, segmentation coverage, declared-byte percentages, or object counts presented **in place of** a loaded model. Those are instruments for getting to the criterion. They are never the criterion.

## HOW IT IS VERIFIED

Only the target application decides. Not a byte comparison, not a test suite, not a decoder that round-trips.

- Open the output in the target application itself, one fresh process, with a control document measured before and after so a bad session cannot be mistaken for a bad file.
- Report the **body count**, the **volume**, and the **centre of mass**, and compare them against the source's own figures.
- Report the **feature tree node by node**, and compare it against the source's feature list.
- Confirm the tree is **editable**: change a driving dimension, rebuild, and confirm the geometry follows.

State all of those numbers. A claim of success without them is not a claim, it is a guess.

## WHEN YOU ARE NOT THERE YET

Say so plainly, in the first line, with the measured numbers. Then keep working. The stopping conditions are the ones in `NoDonorBlocks.md`: **success, or running out of context.** Nothing else.

Do not ask whether to continue. Do not offer a menu of next steps and wait. Identify the blocking artifact, say you are going after it, and go after it.

## THE HONEST FRAMING

Losslessness is not a target you approach asymptotically and then declare close enough. A translator that produces a file with no bodies has translated nothing, however much machinery was built on the way. The intermediate work may be real, valuable and correct — recovered grammars, decoded records, passing gates — and none of it is the criterion. The criterion is a model the user can open and edit.

Report the intermediate work as intermediate. Report the criterion as failed until it passes.

## VERIFICATION

Before reporting any translation as complete:

1. The target application opened the file, in a measured session with a healthy control.
2. Body count, volume and centre of mass are reported and match the source.
3. The feature tree is reported node by node and matches the source.
4. The tree is parametric — a dimension change rebuilds.
5. `vendor_loadable` and `application_usable` are `True`, and they are true.

If any check fails, the translation is not complete. Keep going until success or out of context.
