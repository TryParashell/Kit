from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tests.oracle import SolidWorksSession, solidworks_available


def main() -> int:
    print("available:", solidworks_available(), flush=True)
    root = Path(__file__).parent
    targets = [
        root / "examples" / ".SLDPRT" / "example.SLDPRT",
        root / "PartDesignExample.SLDPRT",
        root / "_roundtrip.SLDPRT",
    ]
    with SolidWorksSession() as session:
        print("revision:", session.revision, flush=True)
        for target in targets:
            if not target.is_file():
                print(f"skip {target.name}: missing", flush=True)
                continue
            report = session.inspect_part(target)
            print(
                f"{target.name}: opened={report.opened} "
                f"errors={report.load_errors} warnings={report.load_warnings} "
                f"rebuilt={report.rebuilt} bodies={report.body_count}",
                flush=True,
            )
            print(f"  features={report.feature_type_names}", flush=True)
            if report.solid is not None:
                print(
                    f"  volume_mm3={report.solid.volume_mm3:.6f} "
                    f"area_mm2={report.solid.surface_area_mm2:.6f}",
                    flush=True,
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
