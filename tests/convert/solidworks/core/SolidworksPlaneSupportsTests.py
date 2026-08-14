# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path

import pytest

from convert.adapters.solidworks import SldprtArchive, read_sldprt
from convert.adapters.solidworks.container.Format import KEYWORDS_STREAM, RESOLVED_FEATURES_STREAM
from convert.adapters.solidworks.core.Native import REFERENCE_SUPPORT_SOURCE, STREAM_ORDER_SUPPORT_SOURCE, UNRESOLVED_SUPPORT_SOURCE, decode_native_model

VENDOR_CORPUS = (
    Path(__file__).resolve().parents[4]
    / "examples"
    / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
)
DERIVED_PLANE_PARTS = (
    ("BIELA.SLDPRT", 38, (39, 196, 205, 215, 242)),
    ("Turbo Tube.SLDPRT", 72, (73,)),
    ("CUBIERTA DE TURBINA 1.SLDPRT", 664, (643, 666, 689, 734, 735)),
)
vendor_corpus = pytest.mark.skipif(
    not VENDOR_CORPUS.is_dir(),
    reason="the localized SOLIDWORKS vendor corpus is not present in this checkout",
)


def _model(name: str):
    archive = SldprtArchive.open(VENDOR_CORPUS / name)
    return decode_native_model(
        archive.require(KEYWORDS_STREAM),
        archive.require(RESOLVED_FEATURES_STREAM),
    )


@vendor_corpus
@pytest.mark.parametrize(("name", "plane_id", "sketch_ids"), DERIVED_PLANE_PARTS)
def test_sketches_on_unframed_reference_planes_fall_back_to_decoded_planes(
    name: str, plane_id: int, sketch_ids: tuple[int, ...]
) -> None:
    model = _model(name)
    framed = {plane.object_id for plane in model.planes}
    assert plane_id not in framed
    affected = tuple(
        sketch for sketch in model.sketches if sketch.object_id in sketch_ids
    )
    assert {sketch.object_id for sketch in affected} == set(sketch_ids)
    for sketch in affected:
        assert sketch.unframed_support_plane_id == plane_id
        assert sketch.support_source == UNRESOLVED_SUPPORT_SOURCE
        assert sketch.support_plane_id in framed


@vendor_corpus
@pytest.mark.parametrize(("name", "plane_id", "sketch_ids"), DERIVED_PLANE_PARTS)
def test_unframed_reference_planes_are_reported_as_diagnostics(
    name: str, plane_id: int, sketch_ids: tuple[int, ...]
) -> None:
    model = _model(name)
    assert any(
        message.startswith("reference plane frames unavailable for")
        and f"{plane_id}:" in message
        for message in model.diagnostics
    )
    assert any(
        message.startswith("sketch supports fall back to decoded planes for")
        for message in model.diagnostics
    )


@vendor_corpus
@pytest.mark.parametrize(("name", "plane_id", "sketch_ids"), DERIVED_PLANE_PARTS)
def test_documents_with_unframed_reference_planes_validate(
    name: str, plane_id: int, sketch_ids: tuple[int, ...]
) -> None:
    document = read_sldprt(VENDOR_CORPUS / name, include_brep=False)
    assert document.validate() == ()
    plane_ids = {plane.id for plane in document.support_planes}
    for sketch in document.sketches:
        assert sketch.support_plane_id in plane_ids
        source = sketch.attributes["support_plane_source"]
        assert source in {
            REFERENCE_SUPPORT_SOURCE,
            STREAM_ORDER_SUPPORT_SOURCE,
            UNRESOLVED_SUPPORT_SOURCE,
        }
        if sketch.attributes["unframed_support_plane_native_id"] is not None:
            assert source == UNRESOLVED_SUPPORT_SOURCE
    assert any(
        diagnostic.message.startswith("reference plane frames unavailable for")
        and f"{plane_id}:" in diagnostic.message
        for diagnostic in document.diagnostics
    )
