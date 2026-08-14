from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for candidate in (ROOT, ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from tests.oracle.Session import SolidWorksSession


def main() -> int:
    target = Path(sys.argv[1])
    payload: dict[str, object] = {"path": str(target)}
    session = SolidWorksSession()
    try:
        try:
            inspection = session.inspect_part(target)
        except Exception as error:
            payload["opened"] = False
            payload["open_exception"] = repr(error)
            payload["volume_mm3"] = None
            payload["centre_mm"] = None
            sys.stdout.write("@@RESULT@@" + json.dumps(payload) + "\n")
            return 0
        payload["opened"] = inspection.opened
        payload["load_errors"] = list(inspection.load_errors)
        payload["load_warnings"] = list(inspection.load_warnings)
        payload["rebuilt"] = inspection.rebuilt
        payload["body_count"] = inspection.body_count
        payload["features"] = [
            {
                "name": item.name,
                "type": item.type_name,
                "suppressed": item.suppressed,
                "dimensions": list(item.dimensions),
            }
            for item in inspection.features
        ]
        if inspection.solid is None:
            payload["volume_mm3"] = None
            payload["centre_mm"] = None
        else:
            payload["volume_mm3"] = inspection.solid.volume_mm3
            payload["surface_mm2"] = inspection.solid.surface_area_mm2
            payload["centre_mm"] = list(inspection.solid.center_of_mass_mm)
    finally:
        session.close()
    sys.stdout.write("@@RESULT@@" + json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
