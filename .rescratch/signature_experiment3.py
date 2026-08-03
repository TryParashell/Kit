from __future__ import annotations

from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container import (  # noqa: E402
    SldprtArchive,
    _template_fields,
)
from tests.oracle import SolidWorksSession  # noqa: E402

from signature_experiment import build_container  # noqa: E402

SAMPLE = ROOT / "examples" / ".SLDPRT" / "example.SLDPRT"
DONOR = ROOT / "examples" / "Random" / "Addons" / "Alternator_pulley.SLDPRT"
OUTPUT = ROOT / ".rescratch" / "variants3"


def describe(target: Path) -> None:
    session: SolidWorksSession | None = None
    try:
        session = SolidWorksSession()
        result = session.inspect_part(target)
        print(
            f"{target.stem}: opened={result.opened} errors={result.load_errors} "
            f"rebuilt={result.rebuilt} bodies={result.body_count} "
            f"features={len(result.features)} "
            f"volume={None if result.solid is None else result.solid.volume_mm3}",
            flush=True,
        )
    except Exception as exc:
        print(f"{target.stem}: CRASHED {type(exc).__name__} {exc}", flush=True)
    finally:
        if session is not None:
            try:
                session.close()
            except Exception:
                pass


def signature_report(path: Path) -> tuple[int, tuple[bytes, bytes, bytes]]:
    data = path.read_bytes()
    archive = SldprtArchive.from_bytes(data)
    signatures, _ = _template_fields(data, archive)
    return archive.file_id, signatures


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    original = SAMPLE.read_bytes()
    archive = SldprtArchive.from_bytes(original)
    signatures, type_ids = _template_fields(original, archive)
    streams = [(record.name, record.data) for record in archive.records]

    donor_id, donor_signatures = signature_report(DONOR)
    print(f"sample file_id=0x{archive.file_id:08x}", flush=True)
    print(f"donor  file_id=0x{donor_id:08x}", flush=True)

    variants = {
        "g_newid_same_signatures": build_container(
            streams, 0x1234ABCD, signatures, type_ids, 0
        ),
        "h_donor_pair": build_container(
            streams, donor_id, donor_signatures, type_ids, 0
        ),
        "i_newid_donor_signatures": build_container(
            streams, 0x1234ABCD, donor_signatures, type_ids, 0
        ),
        "j_local_only_changed": build_container(
            streams,
            archive.file_id,
            (bytes.fromhex("deadbe01"), signatures[1], signatures[2]),
            type_ids,
            0,
        ),
        "k_end_only_changed": build_container(
            streams,
            archive.file_id,
            (signatures[0], signatures[1], bytes.fromhex("deadbe03")),
            type_ids,
            0,
        ),
        "l_version3": build_container(
            streams, archive.file_id, signatures, type_ids, 0, format_version=3
        ),
    }
    paths: list[Path] = []
    for label, payload in variants.items():
        target = OUTPUT / f"{label}.SLDPRT"
        target.write_bytes(payload)
        paths.append(target)
        print(f"{label}: bytes={len(payload)}", flush=True)

    for target in paths:
        describe(target)

    print("=== save-as identity test ===", flush=True)
    resaved_first = OUTPUT / "resaved_first.SLDPRT"
    resaved_second = OUTPUT / "resaved_second.SLDPRT"
    session: SolidWorksSession | None = None
    try:
        session = SolidWorksSession()
        for target in (resaved_first, resaved_second):
            if target.exists():
                target.unlink()
            saved = session.resave_part(SAMPLE, target)
            print(f"resave {target.name}: {saved}", flush=True)
    except Exception as exc:
        print(f"resave CRASHED {type(exc).__name__} {exc}", flush=True)
    finally:
        if session is not None:
            try:
                session.close()
            except Exception:
                pass
    for target in (SAMPLE, resaved_first, resaved_second):
        if not target.is_file():
            print(f"{target.name}: missing", flush=True)
            continue
        file_id, values = signature_report(target)
        print(
            f"{target.name}: file_id=0x{file_id:08x} "
            f"signatures={' '.join(item.hex() for item in values)}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
