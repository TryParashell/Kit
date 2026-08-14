# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as FilePath
import pytest as PytestLib
from convert.adapters.solidworks import SldprtArchive, read_sldprt as ReadSldprt
from convert.adapters.solidworks.container.Format import KEYWORDS_STREAM as Stream, RESOLVED_FEATURES_STREAM as StreamA
from convert.adapters.solidworks.core.Native import REFERENCE_SUPPORT_SOURCE as Source, STREAM_ORDER_SUPPORT_SOURCE as SourceA, UNRESOLVED_SUPPORT_SOURCE as SourceB, decode_native_model as DecodeNativeModel

# centralizes shared evidence so every related assertion uses one value
KCorpus = FilePath(__file__).resolve().parents[4] / 'examples' / 'Single Turbo Dual Overhead Cam V8 - KDP - 2024'

# centralizes shared evidence so every related assertion uses one value
KParts = (('BIELA.SLDPRT', 38, (39, 196, 205, 215, 242)), ('Turbo Tube.SLDPRT', 72, (73,)), ('CUBIERTA DE TURBINA 1.SLDPRT', 664, (643, 666, 689, 734, 735)))

# centralizes shared evidence so every related assertion uses one value
KVendorCorpus = PytestLib.mark.skipif(not KCorpus.is_dir(), reason='the localized SOLIDWORKS vendor corpus is not present in this checkout')

# keeps this focused behavior isolated so regressions remain immediately visible
def Model(NameText: str):
    Archive = SldprtArchive.open(KCorpus / NameText)
    return DecodeNativeModel(Archive.require(Stream), Archive.require(StreamA))

# keeps this focused behavior isolated so regressions remain immediately visible
@KVendorCorpus
@PytestLib.mark.parametrize(('NameText', 'PlaneId', 'SketchIds'), KParts)
def TestSOURPFBTDP(NameText: str, PlaneId: int, SketchIds: tuple[int, ...]) -> None:
    ModelDoc = Model(NameText)
    Framed = {Plane.object_id for Plane in ModelDoc.planes}
    assert PlaneId not in Framed
    Affected = tuple((Sketch for Sketch in ModelDoc.sketches if Sketch.object_id in SketchIds))
    assert {Sketch.object_id for Sketch in Affected} == set(SketchIds)
    for Sketch in Affected:
        assert Sketch.unframed_support_plane_id == PlaneId
        assert Sketch.support_source == SourceB
        assert Sketch.support_plane_id in Framed

# keeps this focused behavior isolated so regressions remain immediately visible
@KVendorCorpus
@PytestLib.mark.parametrize(('NameText', 'PlaneId', 'SketchIds'), KParts)
def TestURPARAD(NameText: str, PlaneId: int, SketchIds: tuple[int, ...]) -> None:
    ModelDoc = Model(NameText)
    assert any((Message.startswith('reference plane frames unavailable for') and f'{PlaneId}:' in Message for Message in ModelDoc.diagnostics))
    assert any((Message.startswith('sketch supports fall back to decoded planes for') for Message in ModelDoc.diagnostics))

# keeps this focused behavior isolated so regressions remain immediately visible
@KVendorCorpus
@PytestLib.mark.parametrize(('NameText', 'PlaneId', 'SketchIds'), KParts)
def TestDWURPV(NameText: str, PlaneId: int, SketchIds: tuple[int, ...]) -> None:
    Document = ReadSldprt(KCorpus / NameText, include_brep=False)
    assert Document.validate() == ()
    PlaneIds = {Plane.id for Plane in Document.support_planes}
    for Sketch in Document.sketches:
        assert Sketch.support_plane_id in PlaneIds
        SourceDoc = Sketch.attributes['support_plane_source']
        assert SourceDoc in {Source, SourceA, SourceB}
        if Sketch.attributes['unframed_support_plane_native_id'] is not None:
            assert SourceDoc == SourceB
    assert any((Diagnostic.message.startswith('reference plane frames unavailable for') and f'{PlaneId}:' in Diagnostic.message for Diagnostic in Document.diagnostics))
