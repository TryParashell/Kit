from __future__ import annotations

from dataclasses import replace
import hashlib
from io import BytesIO
from pathlib import Path
import struct

import pytest

from convert import convert, open_document, write_document
from convert.adapters import ReadOptions
from convert.adapters.catia import (
    CatiaAdapter,
    CatiaAdapterError,
    Cfv2Archive,
    Cfv2FormatError,
    OsmxArchive,
    build_cfv2,
    write_catia,
)
from convert.adapters.solidworks import read_sldprt, write_sldprt
from interchange import Capability, Configuration


ROOT = Path(__file__).parents[2]
CATPARTS = ROOT / "examples" / ".CATPart"
CATPRODUCTS = ROOT / "examples" / ".CATProduct"
SLDPRT = ROOT / "examples" / ".SLDPRT" / "example.SLDPRT"
SLDASM = ROOT / "examples" / "Random" / "Pistons" / "Piston.SLDASM"


def test_real_catia_corpus_uses_valid_cfv2_directories() -> None:
    parts = tuple(sorted(CATPARTS.glob("*.CATPart")))
    products = tuple(sorted(CATPRODUCTS.glob("*.CATProduct")))
    assert len(parts) == 27
    assert len(products) == 3
    for path in parts + products:
        archive = Cfv2Archive.from_bytes(path.read_bytes())
        assert archive.outer.offset + archive.outer.length == path.stat().st_size
        assert archive.outer.streams
        assert archive.named_stream("Data")
    expected_classes = (
        "CATProdCont",
        "CATPrtCont",
        "CGMGeom",
        "CATMFBRP",
        "CATSeeBodyCont",
        "CATBRepModeContainer",
        "CATStdCont",
        "CATCGRCont",
    )
    fragmented_geometry = {
        "4784.CATPart",
        "4876.CATPart",
        "4876_1.CATPart",
        "Pedal_Body.CATPart",
    }
    for path in parts:
        source = path.read_bytes()
        archive = Cfv2Archive.from_bytes(source)
        declarations = archive.declarations()
        assert len(archive.outer.streams) == 41
        assert tuple(item.class_name for item in declarations) == expected_classes
        assert tuple(item.ordinal for item in declarations) == tuple(range(1, 9))
        assert all(
            sum(stream.name == item.stream_name for stream in archive.outer.streams)
            == 2
            for item in declarations
        )
        assert len(archive.nested) == 1
        cgr_declaration = next(
            item for item in declarations if item.class_name == "CATCGRCont"
        )
        cgr_stream = archive.outer.stream(cgr_declaration.stream_name)
        assert cgr_stream is not None
        assert len(cgr_stream.extents) == 1
        assert archive.nested[0].physical_base == cgr_stream.extents[0].physical_offset
        assert archive.nested[0].offset + archive.nested[0].length == (
            cgr_stream.extents[0].physical_offset + cgr_stream.logical_length
        )
        cgm_declaration = next(
            item for item in declarations if item.class_name == "CGMGeom"
        )
        cgm_stream = archive.outer.stream(cgm_declaration.stream_name)
        assert cgm_stream is not None
        assert len(cgm_stream.extents) == (3 if path.name in fragmented_geometry else 1)
        assert len(archive.stream_bytes(cgm_stream)) == cgm_stream.logical_length
        part_declaration = next(
            item for item in declarations if item.class_name == "CATPrtCont"
        )
        part_stream = archive.outer.stream(part_declaration.stream_name)
        assert part_stream is not None
        graph = OsmxArchive.from_bytes(archive.stream_bytes(part_stream))
        assert graph.version == "V5R28SP6HF0"
        assert {"MechanicalPart", "xy-plane", "yz-plane", "zx-plane"} <= set(
            graph.values
        )
        document = open_document(path)
        assert len(document.support_planes) == 3
        assert len(document.feature_timeline) == 1
        assert len(document.bodies) == 1
        assert document.metadata["catia.product_name"]
        assert document.metadata["catia.internal_part_name"]
        assert len(document.metadata["catia.container_declarations"]) == 8
        cgm_payload = next(
            payload
            for payload in document.brep_payloads
            if payload.id == "catia:native-cgm"
        )
        assert cgm_payload.data == archive.stream_bytes(cgm_stream)
        feature_payload = next(
            payload
            for payload in document.brep_payloads
            if payload.id == "catia:native-feature-graph"
        )
        assert feature_payload.data == archive.stream_bytes(part_stream)
        assert document.validate() == ()
        output = BytesIO()
        result = CatiaAdapter().write(document, output)
        assert result.metadata["mode"] == "exact_native_roundtrip"
        assert output.getvalue() == source


@pytest.mark.parametrize(
    "source",
    (
        CATPARTS / "Banjo.CATPart",
        CATPRODUCTS / "Tilton_Set.CATProduct",
    ),
)
def test_native_catia_roundtrip_is_byte_exact(source: Path, tmp_path: Path) -> None:
    document = open_document(source)
    output = tmp_path / source.name
    result = write_document(document, output)
    assert result.metadata["mode"] == "exact_native_roundtrip"
    assert output.read_bytes() == source.read_bytes()


def test_native_catpart_retains_declared_geometry_and_feature_graphs() -> None:
    source = CATPARTS / "Banjo.CATPart"
    archive = Cfv2Archive.from_bytes(source.read_bytes())
    document = open_document(source)
    assert document.source.format_id == "catia.v5"
    assert document.source.application_version == "V5R28SP6HF0"
    assert document.metadata["catia.document_type"] == "CATPart"
    assert [payload.format_id for payload in document.brep_payloads] == [
        "catia.v5.cfv2",
        "catia.cgm",
        "catia.v5.osmx",
        "catia.v5.osmx",
        "catia.v5.mfbrp",
    ]
    cgm_declaration = next(
        item for item in archive.declarations() if item.class_name == "CGMGeom"
    )
    cgm_stream = archive.outer.stream(cgm_declaration.stream_name)
    assert cgm_stream is not None
    cgm = document.brep_payloads[1]
    assert cgm.data == archive.stream_bytes(cgm_stream)
    assert cgm.sha256 == hashlib.sha256(cgm.data or b"").hexdigest()
    assert cgm.source_stream == cgm_declaration.stream_name
    cgm_metadata = next(
        item
        for item in document.metadata["catia.container_declarations"]
        if item["class_name"] == "CGMGeom"
    )
    assert cgm_metadata["sha256"] == cgm.sha256
    assert cgm_metadata["logical_length"] == len(cgm.data or b"")
    feature_graph = document.brep_payloads[2]
    assert feature_graph.kind == "native_feature_graph"
    assert OsmxArchive.from_bytes(feature_graph.data or b"").version == "V5R28SP6HF0"
    assert [plane.name for plane in document.support_planes] == [
        "xy-plane",
        "yz-plane",
        "zx-plane",
    ]
    assert document.bodies[0].name == "Body.2"
    assert document.feature_timeline[0].attributes["native_payload_id"] == (
        feature_graph.id
    )
    assert Capability.PARAMETRIC_HISTORY in document.capabilities
    assert Capability.BREP in document.capabilities
    without_data = CatiaAdapter().read(source, ReadOptions(include_brep=False))
    assert without_data.brep_payloads[0].data is None
    assert {payload.kind for payload in without_data.brep_payloads[1:]} == {
        "native_feature_graph",
        "native_product_graph",
    }
    assert Capability.BREP not in without_data.capabilities


def test_native_catproduct_retains_product_occurrences() -> None:
    document = open_document(CATPRODUCTS / "Tilton_Set.CATProduct")
    assert document.assembly is not None
    assert [instance.name for instance in document.assembly.instances] == [
        "I_4876.2",
        "I_4876.3",
        "I_4784.5",
        "Brake_bias_90_degree_coupler!I_Brake_bias_90_degree_coupler.1",
    ]
    assert len(document.assembly.definitions) == 4
    assert Capability.BREP not in document.capabilities


def test_pedal_body_exposes_native_parametric_symbols() -> None:
    document = open_document(CATPARTS / "Pedal_Body.CATPart")
    assert document.metadata["catia.product_name"] == "Brake_pedal"
    assert document.metadata["catia.internal_part_name"] == "Part2"
    assert document.metadata["catia.body_name"] == "Brake_pedal"
    assert document.metadata["catia.native_feature_classes"] == (
        "GSMPoint",
        "GSMPointCoord",
        "GSMAxisToAxis",
        "GSMTranslate",
    )
    assert document.feature_timeline[0].attributes["native_classes"] == (
        "GSMPoint",
        "GSMPointCoord",
        "GSMAxisToAxis",
        "GSMTranslate",
    )
    assert document.feature_timeline[0].provenance is not None
    assert document.bodies[0].provenance is not None


def test_native_catpart_retains_declared_cgr_tessellation_on_request() -> None:
    source = CATPARTS / "Banjo.CATPart"
    archive = Cfv2Archive.from_bytes(source.read_bytes())
    document = CatiaAdapter().read(
        source,
        ReadOptions(include_brep=False, include_tessellation=True),
    )
    payload = next(
        item for item in document.brep_payloads if item.format_id == "catia.cgr"
    )
    declaration = next(
        item for item in archive.declarations() if item.class_name == "CATCGRCont"
    )
    stream = archive.outer.stream(declaration.stream_name)
    assert stream is not None
    assert payload.data == archive.stream_bytes(stream)
    assert payload.schema == "CATCGRCont"
    assert Capability.TESSELLATION in document.capabilities
    assert Capability.BREP not in document.capabilities


def test_solidworks_part_roundtrips_through_generated_catpart(
    tmp_path: Path,
) -> None:
    source = open_document(SLDPRT)
    output = tmp_path / "example.CATPart"
    with pytest.raises(CatiaAdapterError, match="allow_non_native"):
        convert(SLDPRT, output)
    result = convert(
        SLDPRT,
        output,
        write_values={"allow_non_native": True},
    )
    assert result.destination_format == "catia.v5"
    assert result.output.metadata["mode"] == "generated_cfv2"
    assert result.output.metadata["compatibility"] == "kit-neutral-only"
    assert result.output.metadata["native_feature_graph"] is False
    archive = Cfv2Archive.from_bytes(output.read_bytes())
    assert [value.class_name for value in archive.declarations()] == [
        "CATProdCont",
        "CATPrtCont",
    ]
    assert any(
        directory.stream("KitInterchange") is not None for directory in archive.nested
    )
    restored = open_document(output)
    assert restored.source.format_id == "catia.v5"
    assert (
        restored.metadata["catia.embedded_source_format_id"] == source.source.format_id
    )
    assert restored.metadata["catia.embedded_source_path"] == source.source.path
    assert restored.metadata["catia.embedded_source_sha256"] == source.source.sha256
    assert restored.configurations == source.configurations
    assert restored.sketches == source.sketches
    assert restored.feature_timeline == source.feature_timeline
    assert restored.brep_payloads[:-1] == source.brep_payloads
    assert restored.brep_payloads[-1].format_id == "catia.v5.cfv2"


def test_solidworks_assembly_roundtrips_through_generated_catproduct(
    tmp_path: Path,
) -> None:
    source = open_document(SLDASM)
    output = tmp_path / "Piston.CATProduct"
    result = convert(
        SLDASM,
        output,
        write_values={"allow_non_native": True},
    )
    assert result.source_format == "solidworks.sldasm"
    assert result.destination_format == "catia.v5"
    archive = Cfv2Archive.from_bytes(output.read_bytes())
    assert [value.class_name for value in archive.declarations()] == ["CATProdCont"]
    restored = open_document(output)
    assert restored.source.format_id == "catia.v5"
    assert (
        restored.metadata["catia.embedded_source_format_id"] == source.source.format_id
    )
    assert restored.assembly is not None
    assert restored.assembly == source.assembly
    assert len(restored.assembly.mates) == 6


def test_modified_native_document_rebuilds_instead_of_replaying(
    tmp_path: Path,
) -> None:
    source = CATPARTS / "Banjo.CATPart"
    document = open_document(source)
    changed = replace(
        document,
        configurations=(Configuration("catia:changed", "Changed", active=True),),
    )
    output = tmp_path / "Changed.CATPart"
    result = write_document(
        changed,
        output,
        values={"allow_non_native": True},
    )
    assert result.metadata["mode"] == "generated_cfv2"
    assert output.read_bytes() != source.read_bytes()
    restored = open_document(output)
    assert restored.source.format_id == "catia.v5"
    assert restored.configurations == changed.configurations
    assert restored.brep_payloads[:-1] == changed.brep_payloads[1:]


def test_embedded_manifest_applies_read_options_and_replays_exactly(
    tmp_path: Path,
) -> None:
    source = open_document(SLDPRT)
    output = tmp_path / "Filtered.CATPart"
    convert(SLDPRT, output, write_values={"allow_non_native": True})
    configuration = source.configurations[0]
    filtered = CatiaAdapter().read(
        output,
        ReadOptions(
            configuration=configuration.id,
            include_brep=False,
        ),
    )
    assert filtered.source.format_id == "catia.v5"
    assert filtered.metadata["catia.embedded_source_format_id"] == "solidworks.sldprt"
    assert filtered.brep_payloads == ()
    assert Capability.BREP not in filtered.capabilities
    assert [item.id for item in filtered.configurations if item.active] == [
        configuration.id
    ]
    complete = open_document(output)
    replay = tmp_path / "Replay.CATPart"
    result = write_catia(complete, replay)
    assert result.metadata["mode"] == "exact_native_roundtrip"
    assert replay.read_bytes() == output.read_bytes()


def test_embedded_manifest_rejects_unknown_configuration(tmp_path: Path) -> None:
    output = tmp_path / "Configured.CATPart"
    convert(SLDPRT, output, write_values={"allow_non_native": True})
    with pytest.raises(CatiaAdapterError, match="configuration"):
        CatiaAdapter().read(
            output,
            ReadOptions(configuration="missing-configuration"),
        )


def test_native_catpart_rejects_unknown_configuration() -> None:
    with pytest.raises(CatiaAdapterError, match="configuration"):
        CatiaAdapter().read(
            CATPARTS / "Banjo.CATPart",
            ReadOptions(configuration="missing-configuration"),
        )


def test_conversion_result_reports_selected_catia_reader(tmp_path: Path) -> None:
    catpart = tmp_path / "Reader.CATPart"
    output = tmp_path / "Reader.json"
    convert(SLDPRT, catpart, write_values={"allow_non_native": True})
    result = convert(catpart, output)
    assert result.source_format == "catia.v5"
    assert result.document.source.format_id == "catia.v5"
    assert result.document.metadata["catia.embedded_source_format_id"] == (
        "solidworks.sldprt"
    )


def test_changed_cgm_bytes_disable_exact_native_replay(tmp_path: Path) -> None:
    document = open_document(CATPARTS / "Banjo.CATPart")
    cgm = document.brep_payloads[1]
    changed = replace(
        document,
        brep_payloads=(
            document.brep_payloads[0],
            replace(cgm, data=(cgm.data or b"") + b"\x00"),
        ),
    )
    output = tmp_path / "ChangedGeometry.CATPart"
    result = write_catia(changed, output, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"


def test_swapped_native_document_cannot_exact_replay() -> None:
    document = open_document(CATPARTS / "Banjo.CATPart")
    replacement = (CATPARTS / "Bolt_M5x40.CATPart").read_bytes()
    changed = replace(
        document,
        brep_payloads=(
            replace(
                document.brep_payloads[0],
                data=replacement,
                sha256=hashlib.sha256(replacement).hexdigest(),
            ),
            *document.brep_payloads[1:],
        ),
    )
    output = BytesIO()
    result = write_catia(changed, output, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"
    assert output.getvalue() != replacement


def test_native_catpart_replays_across_solidworks_carrier(tmp_path: Path) -> None:
    source_path = CATPARTS / "Banjo.CATPart"
    source = open_document(source_path)
    carrier = tmp_path / "Banjo.SLDPRT"
    output = tmp_path / "Banjo.CATPart"
    write_sldprt(source, carrier, allow_non_native=True)
    restored = read_sldprt(carrier)
    result = write_catia(restored, output)
    assert result.metadata["mode"] == "exact_native_roundtrip"
    assert output.read_bytes() == source_path.read_bytes()


def test_engine_reports_solidworks_alias_and_output_adapter(tmp_path: Path) -> None:
    output = tmp_path / "Piston.SLDASM"
    result = convert(SLDASM, output)
    assert result.source_format == "solidworks.sldasm"
    assert result.destination_format == "solidworks.sldasm"
    assert result.output.adapter == "solidworks.sldasm"


def test_cfv2_rejects_inconsistent_outer_directory() -> None:
    data = bytearray((CATPARTS / "Banjo.CATPart").read_bytes())
    data[15] ^= 1
    with pytest.raises(Cfv2FormatError):
        Cfv2Archive.from_bytes(data)


def test_cfv2_rejects_extent_inside_directory() -> None:
    data = bytearray((CATPARTS / "Banjo.CATPart").read_bytes())
    archive = Cfv2Archive.from_bytes(data)
    stream = archive.outer.stream("Data")
    assert stream is not None
    struct.pack_into(">I", data, stream.descriptor_offset + 0x54, archive.outer.offset)
    with pytest.raises(Cfv2FormatError, match="payload region"):
        Cfv2Archive.from_bytes(data)


def test_cfv2_rejects_overlapping_extents() -> None:
    data = bytearray((CATPARTS / "Banjo.CATPart").read_bytes())
    archive = Cfv2Archive.from_bytes(data)
    first = archive.outer.stream("Format")
    second = archive.outer.stream("GesToler")
    assert first is not None
    assert second is not None
    struct.pack_into(
        ">I",
        data,
        second.descriptor_offset + 0x54,
        first.extents[0].physical_offset,
    )
    with pytest.raises(Cfv2FormatError, match="overlap"):
        Cfv2Archive.from_bytes(data)


def test_cfv2_rejects_unowned_nested_container() -> None:
    data = bytearray((CATPARTS / "Banjo.CATPart").read_bytes())
    archive = Cfv2Archive.from_bytes(data)
    preview = archive.outer.stream("CATPreview")
    assert preview is not None
    assert len(preview.extents) == 1
    injected = build_cfv2((("Injected", b"value"),))
    assert len(injected) < preview.logical_length
    start = preview.extents[0].physical_offset
    data[start : start + len(injected)] = injected
    with pytest.raises(Cfv2FormatError, match="owning stream"):
        Cfv2Archive.from_bytes(data)
