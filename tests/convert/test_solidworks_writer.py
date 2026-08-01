from __future__ import annotations

from dataclasses import replace
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from convert import convert, registry, write_document
from convert.adapters.catia import read_catia, write_catia
from convert.adapters.freecad import read_freecad, write_freecad
from convert.adapters.solidworks import (
    SldprtArchive,
    SldprtFormatError,
    read_sldprt,
    write_sldprt,
)
from tests.interchange.test_assembly import assembly_document
from tests.interchange.test_document import document


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"


def test_solidworks_source_replays_exactly_after_freecad_roundtrip(tmp_path) -> None:
    source = read_sldprt(SAMPLE)
    fcstd = tmp_path / "source.FCStd"
    output = tmp_path / "source.SLDPRT"
    write_freecad(source, fcstd)
    restored = read_freecad(fcstd)
    result = write_sldprt(restored, output)
    assert output.read_bytes() == SAMPLE.read_bytes()
    assert result.metadata["mode"] == "exact"
    assert result.metadata["native_content"] == "exact"
    assert result.metadata["compatibility"] == "native-exact"
    assert result.metadata["neutral_edits_are_native"] is True


def test_solidworks_source_replays_exactly_after_catia_carrier(tmp_path) -> None:
    source = read_sldprt(SAMPLE)
    catpart = tmp_path / "source.CATPart"
    output = tmp_path / "source.SLDPRT"
    write_catia(source, catpart, allow_non_native=True)
    restored = read_catia(catpart)
    result = write_sldprt(restored, output)
    assert output.read_bytes() == SAMPLE.read_bytes()
    assert result.metadata["mode"] == "exact"
    assert result.metadata["compatibility"] == "native-exact"


def test_freecad_document_writes_structural_solidworks_container(tmp_path) -> None:
    source = document()
    fcstd = tmp_path / "neutral.FCStd"
    output = tmp_path / "neutral.SLDPRT"
    write_freecad(source, fcstd)
    restored = read_freecad(fcstd)
    with pytest.raises(SldprtFormatError, match="allow_non_native"):
        write_sldprt(restored, output, allow_non_native=False)
    result = write_sldprt(restored, output)
    archive = SldprtArchive.open(output)
    assert archive.format_version == 4
    assert archive.require("Kit/Interchange")
    assert archive.require("swXmlContents/KeyWords").startswith(b"<?xml")
    assert archive.get("Contents/Config-0-ResolvedFeatures") == b""
    assert output.read_bytes()[:1] not in {b"{", b"["}
    assert output.read_bytes()[:4] != b"PK\x03\x04"
    reread = read_sldprt(output)
    assert reread.configurations == source.configurations
    assert reread.support_planes == source.support_planes
    assert reread.sketches == source.sketches
    assert reread.feature_timeline == source.feature_timeline
    assert reread.bodies == source.bodies
    assert result.metadata["mode"] == "generated"
    assert result.metadata["native_content"] == "none"
    assert result.metadata["compatibility"] == "kit-neutral-only"
    assert result.metadata["neutral_edits_are_native"] is False
    assert result.metadata["vendor_loadable"] is False
    assert result.metadata["native_geometry"] is False
    assert result.metadata["native_history"] is False
    assert result.metadata["native_assembly"] is False
    assert [item.code for item in result.diagnostics] == ["sldprt.neutral_write"]
    replay = BytesIO()
    replay_result = write_sldprt(reread, replay)
    assert replay.getvalue() == output.read_bytes()
    assert replay_result.metadata["compatibility"] == "kit-neutral-only"
    assert replay_result.metadata["vendor_loadable"] is False


def test_semantic_edit_uses_native_template_without_claiming_native_edit(
    tmp_path,
) -> None:
    source = read_sldprt(SAMPLE)
    edited_feature = replace(source.feature_timeline[0], name="Edited in Kit")
    edited = replace(
        source,
        feature_timeline=(edited_feature, *source.feature_timeline[1:]),
    )
    output = tmp_path / "edited.SLDPRT"
    with pytest.raises(SldprtFormatError, match="allow_non_native"):
        write_sldprt(edited, output, allow_non_native=False)
    result = write_sldprt(edited, output)
    original_archive = SldprtArchive.open(SAMPLE)
    edited_archive = SldprtArchive.open(output)
    assert output.read_bytes() != SAMPLE.read_bytes()
    assert set(original_archive.streams) <= set(edited_archive.streams)
    assert edited_archive.require("Kit/Interchange")
    assert read_sldprt(output).feature_timeline[0].name == "Edited in Kit"
    assert result.metadata["mode"] == "template"
    assert result.metadata["native_content"] == "source-preserved"
    assert result.metadata["compatibility"] == "native-source-with-kit-neutral"
    assert result.metadata["neutral_edits_are_native"] is False
    assert result.diagnostics[-1].code == "sldprt.neutral_write"


def test_solidworks_aliases_enforce_document_kind(tmp_path) -> None:
    adapter = registry.writer("solidworks.sldprt")
    assert registry.reader("solidworks.sldasm") is registry.reader("solidworks.sldprt")
    assert registry.writer("solidworks.sldasm") is adapter
    assert "solidworks.sldasm" in registry.format_ids()
    part = document()
    assembly = assembly_document()
    assert adapter.supports(part, tmp_path / "part.SLDPRT")
    assert not adapter.supports(part, tmp_path / "part.SLDASM")
    assert adapter.supports(assembly, tmp_path / "assembly.SLDASM")
    assert not adapter.supports(assembly, tmp_path / "assembly.SLDPRT")
    assert adapter.supports(part, BytesIO())
    assert not adapter.supports(part, StringIO())
    with pytest.raises(ValueError, match=r"\.SLDPRT"):
        write_sldprt(part, tmp_path / "part.SLDASM")
    with pytest.raises(ValueError, match=r"\.SLDASM"):
        write_sldprt(assembly, tmp_path / "assembly.SLDPRT")
    result = write_sldprt(
        assembly,
        tmp_path / "assembly.SLDASM",
        allow_non_native=True,
    )
    assert result.adapter == "solidworks.sldasm"
    assert result.metadata["format_id"] == "solidworks.sldasm"
    assembly_json = assembly.write_json(tmp_path / "assembly.json")
    conversion = convert(
        assembly_json,
        tmp_path / "converted.SLDASM",
        destination_format="solidworks.sldasm",
        write_values={"allow_non_native": True},
    )
    assert conversion.destination_format == "solidworks.sldasm"


def test_generated_sldasm_stream_retains_assembly_identity() -> None:
    source = assembly_document()
    output = BytesIO()
    result = write_sldprt(source, output)
    restored = read_sldprt(output.getvalue())
    assert result.adapter == "solidworks.sldasm"
    assert restored.source.format_id == "solidworks.sldasm"
    assert restored.assembly == source.assembly


def test_public_sdk_generates_non_native_swaps_by_default(tmp_path) -> None:
    source = document()
    direct = tmp_path / "direct.SLDPRT"
    blocked = tmp_path / "blocked.SLDPRT"
    with pytest.raises(SldprtFormatError, match="allow_non_native"):
        write_document(source, blocked, values={"allow_non_native": False})
    written = write_document(source, direct)
    assert written.metadata["compatibility"] == "kit-neutral-only"
    fcstd = tmp_path / "source.FCStd"
    converted = tmp_path / "converted.SLDPRT"
    write_freecad(source, fcstd)
    blocked_conversion = tmp_path / "blocked_conversion.SLDPRT"
    with pytest.raises(SldprtFormatError, match="allow_non_native"):
        convert(
            fcstd,
            blocked_conversion,
            write_values={"allow_non_native": False},
        )
    result = convert(
        fcstd,
        converted,
    )
    assert result.destination_format == "solidworks.sldprt"
    assert result.output.metadata["compatibility"] == "kit-neutral-only"
