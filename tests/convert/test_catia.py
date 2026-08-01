from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from convert import convert, open_document, write_document
from convert.adapters import ReadOptions
from convert.adapters.catia import (
    CatiaAdapter,
    CatiaAdapterError,
    Cfv2Archive,
    Cfv2FormatError,
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
    files = tuple(CATPARTS.glob("*.CATPart")) + tuple(CATPRODUCTS.glob("*.CATProduct"))
    assert len(files) == 30
    for path in files:
        archive = Cfv2Archive.from_bytes(path.read_bytes())
        assert archive.outer.offset + archive.outer.length == path.stat().st_size
        assert archive.outer.streams
        assert archive.named_stream("Data")
    assert Cfv2Archive.from_bytes((CATPARTS / "Banjo.CATPart").read_bytes()).nested


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


def test_native_catpart_retains_nested_cgm_payload() -> None:
    document = open_document(CATPARTS / "Banjo.CATPart")
    assert document.source.format_id == "catia.v5"
    assert document.source.application_version == "V5R28SP6HF0"
    assert document.metadata["catia.document_type"] == "CATPart"
    assert [payload.format_id for payload in document.brep_payloads] == [
        "catia.v5.cfv2",
        "catia.cgm",
    ]
    assert Capability.BREP in document.capabilities
    without_data = CatiaAdapter().read(
        CATPARTS / "Banjo.CATPart", ReadOptions(include_brep=False)
    )
    assert without_data.brep_payloads[0].data is None
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
