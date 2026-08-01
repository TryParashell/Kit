from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re

import pytest

from convert import convert, open_document, registry
from interchange import AssemblyData, CadDocument


ROOT = Path(__file__).parents[2]
README = ROOT / "README.md"
EXAMPLES = ROOT / "examples"
SOURCES = (
    (".SLDPRT", EXAMPLES / ".SLDPRT" / "example.SLDPRT"),
    (".SLDASM", EXAMPLES / "Random" / "Pistons" / "Piston.SLDASM"),
    (
        ".FCStd",
        EXAMPLES / "Random" / "V8_engine" / "hex bolt gradeb_iso.FCStd",
    ),
    (".CATPart", EXAMPLES / ".CATPart" / "Banjo.CATPart"),
    (
        ".CATProduct",
        EXAMPLES / ".CATProduct" / "Brake_Pedal_Assembly - Backup 2.CATProduct",
    ),
)
DESTINATION_FORMATS = {
    ".SLDPRT": "solidworks.sldprt",
    ".SLDASM": "solidworks.sldasm",
    ".FCStd": "freecad.fcstd",
    ".CATPart": "catia.v5",
    ".CATProduct": "catia.v5",
}
SOURCE_FORMATS = DESTINATION_FORMATS
SUPPORTED_SUFFIXES = frozenset(DESTINATION_FORMATS)
SUPPORTED_FILES = tuple(
    sorted(
        path
        for path in EXAMPLES.rglob("*")
        if path.is_file()
        and path.suffix.casefold() in {value.casefold() for value in SUPPORTED_SUFFIXES}
    )
)


def _assembly_signature(assembly: AssemblyData | None):
    if assembly is None:
        return None
    return (
        assembly.root_definition_id,
        assembly.definitions,
        assembly.instances,
        tuple(
            (component.id, _document_signature(component.document))
            for component in assembly.documents
        ),
        assembly.mate_entities,
        assembly.mates,
        assembly.mate_groups,
        assembly.attributes,
    )


def _document_signature(document: CadDocument):
    return (
        document.configurations,
        document.parameters,
        document.support_planes,
        document.sketches,
        document.selections,
        document.feature_timeline,
        document.bodies,
        document.meshes,
        tuple(
            payload
            for payload in document.brep_payloads
            if payload.kind not in {"native_document", "native_document_binding"}
        ),
        document.units,
        document.schema_version,
        _assembly_signature(document.assembly),
    )


@lru_cache(maxsize=len(SOURCES))
def _matrix_document(source: Path) -> CadDocument:
    return open_document(source)


def test_swap_matrix_matches_every_readme_format() -> None:
    supported = README.read_text(encoding="utf-8").split("## Supported formats", 1)[1]
    readme_suffixes = set(re.findall(r"`(\.[A-Za-z0-9]+)`", supported))
    assert readme_suffixes == set(SOURCE_FORMATS) == set(DESTINATION_FORMATS)


@pytest.mark.parametrize(
    "source",
    SUPPORTED_FILES,
    ids=lambda path: str(path.relative_to(EXAMPLES)),
)
def test_every_supported_example_swaps_through_freecad(source: Path) -> None:
    source_suffix = next(
        suffix
        for suffix in SOURCE_FORMATS
        if suffix.casefold() == source.suffix.casefold()
    )
    original = open_document(source)
    original_signature = _document_signature(original)
    freecad = BytesIO()
    forward = convert(source, freecad, destination_format="freecad.fcstd")
    freecad_bytes = freecad.getvalue()
    restored = open_document(freecad_bytes, source_format="freecad.fcstd")
    assert forward.destination_format == "freecad.fcstd"
    assert forward.output.bytes_written == len(freecad_bytes)
    assert restored.validate() == ()
    assert _document_signature(restored) == original_signature
    reverse = BytesIO()
    backward = convert(
        freecad_bytes,
        reverse,
        source_format="freecad.fcstd",
        destination_format=SOURCE_FORMATS[source_suffix],
    )
    reversed_document = open_document(
        reverse.getvalue(),
        source_format=SOURCE_FORMATS[source_suffix],
    )
    assert backward.destination_format == SOURCE_FORMATS[source_suffix]
    assert reversed_document.validate() == ()
    assert _document_signature(reversed_document) == original_signature


@pytest.mark.parametrize(
    ("source_suffix", "source"),
    SOURCES,
    ids=("sldprt", "sldasm", "fcstd", "catpart", "catproduct"),
)
@pytest.mark.parametrize(
    "destination_suffix",
    tuple(DESTINATION_FORMATS),
    ids=("sldprt", "sldasm", "fcstd", "catpart", "catproduct"),
)
def test_every_supported_format_swaps_both_directions(
    source_suffix: str,
    source: Path,
    destination_suffix: str,
    tmp_path: Path,
) -> None:
    original = _matrix_document(source)
    original_signature = _document_signature(original)
    destination = tmp_path / f"swapped{destination_suffix}"
    result = convert(source, destination)
    restored = open_document(destination)
    assert result.source_format == SOURCE_FORMATS[source_suffix]
    assert result.destination_format == DESTINATION_FORMATS[destination_suffix]
    assert result.output.path == destination.resolve()
    assert result.output.bytes_written == destination.stat().st_size
    assert restored.validate() == ()
    assert _document_signature(restored) == original_signature
    if destination_suffix in {".SLDPRT", ".SLDASM"}:
        assert restored.source.format_id == DESTINATION_FORMATS[destination_suffix]
    elif destination_suffix in {".CATPart", ".CATProduct"}:
        assert restored.metadata["catia.document_type"] == destination_suffix[1:]
    else:
        assert registry.select_reader(destination).info.format_id == "freecad.fcstd"
    reverse = tmp_path / f"reversed{source_suffix}"
    reverse_result = convert(destination, reverse)
    reversed_document = open_document(reverse)
    assert reverse_result.destination_format == SOURCE_FORMATS[source_suffix]
    assert reversed_document.validate() == ()
    assert _document_signature(reversed_document) == original_signature
