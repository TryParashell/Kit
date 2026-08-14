# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import os as OsInfo
from pathlib import Path as FilePath
import pytest as PytestLib
from convert import write_document as WriteDocument
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import (
    PARTITION_STREAM as Stream,
    RESOLVED_FEATURES_STREAM as StreamA,
)
from convert.adapters.solidworks.resolved.Core import (
    BLIND_END_CONDITION as Condition,
    locate_rectangle_pad as LocateRectanglePad,
)
from tests.convert.solidworks.core.SolidworksWriterTests import FreecadRPD
from tests.oracle.Session import IsOracleReady, OracleSession

# centralizes shared evidence so every related assertion uses one value
KEnabled = OsInfo.environ.get("KIT_SOLIDWORKS_ORACLE") == "1"

# centralizes shared evidence so every related assertion uses one value
KPytestmark = PytestLib.mark.skipif(
    not KEnabled or not IsOracleReady(),
    reason="KIT_SOLIDWORKS_ORACLE=1 and a registered SOLIDWORKS install are required",
)


# keeps this focused behavior isolated so regressions remain immediately visible
@KPytestmark
def TestFRPOISWEV(TmpPath: FilePath) -> None:
    Document = FreecadRPD()
    TargetDoc = TmpPath / "FreeCADRectanglePad.SLDPRT"
    ResultInfo = WriteDocument(Document, TargetDoc, allow_carrier=False)
    assert ResultInfo.application_usable is True
    assert ResultInfo.vendor_loadable is True
    Archive = SldprtArchive.from_bytes(TargetDoc.read_bytes())
    Layout = LocateRectanglePad(Archive.require(StreamA))
    assert Layout is not None
    MinimumX, MinimumY, MaximumX, MaximumY = Layout.bounds_mm
    ExpectedVolume = (MaximumX - MinimumX) * (MaximumY - MinimumY) * Layout.depth_mm
    with OracleSession() as Session:
        Report = Session.InspectPart(TargetDoc)
    assert Report.Opened is True
    assert Report.LoadErrors == ()
    assert Report.Rebuilt is True
    assert Report.BodyCount == 1
    assert Report.Solid is not None
    assert Report.Solid.VolumeMmThree == PytestLib.approx(ExpectedVolume, rel=1e-09)
    assert "Extrusion" in Report.FeatureTN
    assert "ProfileFeature" in Report.FeatureTN


# keeps this focused behavior isolated so regressions remain immediately visible
@KPytestmark
def TestSRGWACP(TmpPath: FilePath) -> None:
    Document = FreecadRPD()
    TargetDoc = TmpPath / "NoPartition.SLDPRT"
    WriteDocument(Document, TargetDoc, allow_carrier=False)
    Archive = SldprtArchive.from_bytes(TargetDoc.read_bytes())
    assert Archive.get(Stream) is not None
    Layout = LocateRectanglePad(Archive.require(StreamA))
    assert Layout is not None
    assert Layout.reversed is False
    assert Layout.end_condition_code == Condition
    with OracleSession() as Session:
        Report = Session.InspectPart(TargetDoc)
    assert Report.Opened is True
    assert Report.BodyCount == 1
