# The container: file framing and the `file_id` -> signature table

This is the outermost layer and the only one that is **completely** inverted. Nothing else matters
until a file opens, and a wrong container header does not produce a clean error — it **hard-crashes
SOLIDWORKS**.

## What is here

| file | what it establishes | confidence |
|---|---|---|
| `STATIC.md` | Static census of the 63-file real-world corpus through Kit's own container parser, no COM: `format_version` 4 in all 63, 61 distinct `file_id`s, 61 distinct signature triplets, 234 distinct `mo*`/`sg*` classes, 11 distinct tree-node flag values, 83 distinct stream names (30 present in all 63, **39 unknown to Kit**), plus a per-file table of bytes / streams / lanes / classes / nodes / scalars / sketch points. | **confirmed** as a census (measured over real bytes). The "present in all 63 files" column is labelled *candidate* load-critical, not proven. |

Machine-readable: `../../data/container_inventory_static.json`,
`../../data/container_inventory_reader.json`, `../../data/corpus_census_per_file.json`.

## The signature table — the single most useful result in this workspace

A `.SLDPRT` header carries a 4-byte `file_id` and the container uses three 4-byte signatures for
its local records, its central directory and its end-of-directory record. Getting them wrong crashes
SOLIDWORKS, so for a long time a file could only be written by reusing a donor's triplet.

**There is no algorithm relating them. It is a 1000-entry lookup table baked into `sldmfcu.dll`.**

| array | virtual address | file offset (SW 2025 `sldmfcu.dll`) | size | element |
|---|---|---|---|---|
| ids | `0x3cf5a440` | **`0x566c40`** | 4000 bytes | `u32` file id, **big-endian** |
| signatures | `0x3cf5b3e0` | **`0x567be0`** | 12000 bytes | three `u32`, **big-endian** |

Exactly **1000** entries each, parallel: entry `i` of the id array pairs with entry `i` of the
signature array. The only function referencing either array is the initialiser `FUN_3cc4e200`, which
walks them once and inserts into a red-black-tree map keyed by the id. **The loop bound `1000` is a
literal in the code.** Three further parallel 1-byte arrays (`0x3d11bc60`, `0x3d11c050`,
`0x3d11c440`, 1000 bytes each) hold ASCII-ish per-entry values stored in the same map node; they are
**not** container signatures.

Byte order, stated so it cannot be got wrong: the id's four bytes go into the header **in the order
they appear in the DLL**; each signature's four bytes go into the file **reversed** — the DLL stores
a big-endian `u32` and the file field is that same `u32` little-endian.

The table is byte-identical in `sldmfcu.dll`, `slwstep30.dll` and `sldsetdocprop.exe`.

### Verification — **confirmed, 184 of 184**

```
distinct file_ids 1000 of 1000
parts=184 match=184 mismatch=0 unknown=0 unreadable=0
```

Every `.SLDPRT`/`.SLDASM` under `examples/` plus the four authored corpora was read through the
project's real container parser and compared against the extracted table: every file id is present,
and all three of its signatures are exactly the parallel entry. Nothing was hand-verified.

Reproduce:

```powershell
uv run python re\tooling\ghidra\sigtable.py
```

Reads `re/binaries/sldmfcu.dll` (falling back to the install), rewrites
`../../data/signature_table.json`, then rescans the corpora. Needs the `.SLDPRT` corpora under
`.rescratch/` for the 184-file half; the 1000-entry extraction half needs only the DLL.

### Why every mixer search failed

The ids and signatures are 4000 unrelated random dwords. XOR keys, affine maps over GF(2), LCGs,
CRC32, rotations and bit permutations were all correctly ruled out because **none of them exists**.
Record this before repeating it on another format: if a differential search over a plausible
function space comes up completely empty, look for a table in `.rdata` and find the loop that reads
it.

### What it changes

`build_sldprt(..., file_id=..., template=None)` used to raise
`"SLDPRT file id requires a native template with matching signatures"` for any id outside two
hardcoded pairs (they turned out to be table entries **711** `0xEC6E2386` and **750** `0x715BE98F`).
With `../../data/signature_table.json` it can serve all 1000 ids and the donor template is no longer
needed **for the container framing**. Stream content still needs a donor — nothing here changes that.

## Streams: droppable, stale-safe, load-critical

Established by deleting streams and rebuilding in SOLIDWORKS (`../archive/MULTISTREAM.md` §5):

| class | streams |
|---|---|
| **load-critical** | `Contents/Config-0-ResolvedFeatures`, `Contents/CMgr`, `Contents/Config-0-ModelHeader` + `Header2`, `Contents/Config-0`, `Contents/Definition` |
| **stale-safe** (keep the donor's copy, do not update) | `Contents/Config-0-LWDATA`, `Contents/DisplayLists`, `_MO_VERSION_*/Biography` |
| **droppable** | `Contents/Config-0-Partition`, `ThirdPtyStore/VisualStates` |

Dropping `Config-0-Partition` is why every volume in `../measurements/` is a genuine rebuild rather
than a cached solid being read back.

`swXmlContents/KeyWords` is a stream in its own right and is the cheapest oracle in the format: plain
XML, feature ids that match the binary tree nodes, authored dimensions as text. It **starts with a
single `0x86` byte** and uses **CRLF**; a UTF-8 BOM crashes SOLIDWORKS. See `../GROUND_TRUTH.md` §1
and `../archive/GRAMMAR.md`.

## Also relevant

* `../records/ANSWERS.md` **Q7** is the full derivation of the signature table, including the
  decompiled initialiser loop. `../../data/sldmfcu_sigtable_refs.c` is that function's decompiled C.
* `../corpus/CORPUS2.md` §9 shows the container being rebuilt end to end four times — donor stream
  reused, `Partition` dropped, file id and triplet carried over — with measured volumes agreeing to
  12 significant figures.
