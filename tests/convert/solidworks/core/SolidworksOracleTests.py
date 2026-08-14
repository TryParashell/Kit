# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import os
from pathlib import Path

import pytest

from convert import write_document
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import PARTITION_STREAM, RESOLVED_FEATURES_STREAM
from convert.adapters.solidworks.resolved.Core import BLIND_END_CONDITION, locate_rectangle_pad

from tests.convert.solidworks.core.SolidworksWriterTests import _freecad_rectangle_pad_document
from tests.oracle import SolidWorksSession, solidworks_available

ORACLE_ENABLED = os.environ.get("KIT_SOLIDWORKS_ORACLE") == "1"
pytestmark = pytest.mark.skipif(
    not ORACLE_ENABLED or not solidworks_available(),
    reason="KIT_SOLIDWORKS_ORACLE=1 and a registered SOLIDWORKS install are required",
)


def test_freecad_rectangle_pad_opens_in_solidworks_with_exact_volume(
    tmp_path: Path,
) -> None:
    document = _freecad_rectangle_pad_document()
    target = tmp_path / "FreeCADRectanglePad.SLDPRT"
    result = write_document(document, target, allow_carrier=False)
    assert result.application_usable is True
    assert result.vendor_loadable is True

    archive = SldprtArchive.from_bytes(target.read_bytes())
    layout = locate_rectangle_pad(archive.require(RESOLVED_FEATURES_STREAM))
    assert layout is not None
    minimum_x, minimum_y, maximum_x, maximum_y = layout.bounds_mm
    expected_volume = (
        (maximum_x - minimum_x) * (maximum_y - minimum_y) * layout.depth_mm
    )

    with SolidWorksSession() as session:
        report = session.inspect_part(target)

    assert report.opened is True
    assert report.load_errors == ()
    assert report.rebuilt is True
    assert report.body_count == 1
    assert report.solid is not None
    assert report.solid.volume_mm3 == pytest.approx(expected_volume, rel=1e-9)
    assert "Extrusion" in report.feature_type_names
    assert "ProfileFeature" in report.feature_type_names


def test_solidworks_rebuilds_geometry_without_a_cached_partition(
    tmp_path: Path,
) -> None:
    document = _freecad_rectangle_pad_document()
    target = tmp_path / "NoPartition.SLDPRT"
    write_document(document, target, allow_carrier=False)
    archive = SldprtArchive.from_bytes(target.read_bytes())
    assert archive.get(PARTITION_STREAM) is not None

    layout = locate_rectangle_pad(archive.require(RESOLVED_FEATURES_STREAM))
    assert layout is not None
    assert layout.reversed is False
    assert layout.end_condition_code == BLIND_END_CONDITION

    with SolidWorksSession() as session:
        report = session.inspect_part(target)

    assert report.opened is True
    assert report.body_count == 1
