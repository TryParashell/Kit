# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import json as JsonData
from pathlib import Path as PathInfo
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = KHereInfo.parents[2]
for CandInfo in (KRootInfo, KRootInfo / "src"):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
from tests.oracle.Session import SolidWorksSession


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMain(Target) -> int:
    PayloadInfo: dict[str, object] = {"path": str(Target)}
    Session = SolidWorksSession()
    try:
        try:
            Inspection = Session.inspect_part(Target)
        except Exception as Error:
            PayloadInfo["opened"] = False
            PayloadInfo["open_exception"] = repr(Error)
            PayloadInfo["volume_mm3"] = None
            PayloadInfo["centre_mm"] = None
            System.stdout.write("@@RESULT@@" + JsonData.dumps(PayloadInfo) + "\n")
            return 0
        PayloadInfo["opened"] = Inspection.opened
        PayloadInfo["load_errors"] = list(Inspection.load_errors)
        PayloadInfo["load_warnings"] = list(Inspection.load_warnings)
        PayloadInfo["rebuilt"] = Inspection.rebuilt
        PayloadInfo["body_count"] = Inspection.body_count
        PayloadInfo["features"] = [
            {
                "name": ItemData.name,
                "type": ItemData.type_name,
                "suppressed": ItemData.suppressed,
                "dimensions": list(ItemData.dimensions),
            }
            for ItemData in Inspection.features
        ]
        if Inspection.solid is None:
            PayloadInfo["volume_mm3"] = None
            PayloadInfo["centre_mm"] = None
        else:
            PayloadInfo["volume_mm3"] = Inspection.solid.volume_mm3
            PayloadInfo["surface_mm2"] = Inspection.solid.surface_area_mm2
            PayloadInfo["centre_mm"] = list(Inspection.solid.center_of_mass_mm)
    finally:
        Session.close()
    System.stdout.write("@@RESULT@@" + JsonData.dumps(PayloadInfo) + "\n")
    return 0


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    Target = PathInfo(System.argv[1])
    return FinishMain(Target)


if __name__ == "__main__":
    raise SystemExit(MainRun())
