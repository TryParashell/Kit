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
FORMAT_BY_SUFFIX = {
    ".SLDPRT": "solidworks.sldprt",
    ".SLDASM": "solidworks.sldasm",
    ".FCStd": "freecad.fcstd",
    ".CATPart": "catia.v5",
    ".CATProduct": "catia.v5",
}
PART_SUFFIXES = (".SLDPRT", ".FCStd", ".CATPart")
ASSEMBLY_SUFFIXES = (".SLDASM", ".FCStd", ".CATProduct")
SUPPORTED_SUFFIXES = frozenset(FORMAT_BY_SUFFIX)
MATRIX_SOURCES = (
    (
        "sldprt",
        ".SLDPRT",
        EXAMPLES / ".SLDPRT" / "example.SLDPRT",
        False,
    ),
    (
        "fcstd_part",
        ".FCStd",
        EXAMPLES / "Random" / "V8_engine" / "hex bolt gradeb_iso.FCStd",
        False,
    ),
    (
        "catpart",
        ".CATPart",
        EXAMPLES / ".CATPart" / "Banjo.CATPart",
        False,
    ),
    (
        "sldasm",
        ".SLDASM",
        EXAMPLES / "Random" / "Pistons" / "Piston.SLDASM",
        True,
    ),
    (
        "fcstd_assembly",
        ".FCStd",
        EXAMPLES / "Random" / "V8_engine" / "Conrod_2.FCStd",
        True,
    ),
    (
        "catproduct",
        ".CATProduct",
        EXAMPLES / ".CATProduct" / "Brake_Pedal_Assembly - Backup 2.CATProduct",
        True,
    ),
)
MATRIX_CASES = tuple(
    (name, source_suffix, source, is_assembly, destination_suffix)
    for name, source_suffix, source, is_assembly in MATRIX_SOURCES
    for destination_suffix in (ASSEMBLY_SUFFIXES if is_assembly else PART_SUFFIXES)
)
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


def _suffix(path: Path) -> str:
    return next(
        value
        for value in FORMAT_BY_SUFFIX
        if value.casefold() == path.suffix.casefold()
    )


def _target_suffixes(document: CadDocument) -> tuple[str, ...]:
    return ASSEMBLY_SUFFIXES if document.assembly is not None else PART_SUFFIXES


def _assert_target(
    document: CadDocument,
    suffix: str,
    source: Path | bytes,
    is_assembly: bool,
) -> None:
    assert (document.assembly is not None) == is_assembly
    if suffix in {".SLDPRT", ".SLDASM"}:
        assert document.source.format_id == FORMAT_BY_SUFFIX[suffix]
    elif suffix in {".CATPart", ".CATProduct"}:
        assert document.metadata["catia.document_type"] == suffix[1:]
    else:
        assert registry.select_reader(source).info.format_id == "freecad.fcstd"


def _assert_truthful_vendor_result(result, suffix: str) -> None:
    if suffix not in {".SLDPRT", ".SLDASM", ".CATPart", ".CATProduct"}:
        return
    metadata = result.output.metadata
    assert isinstance(metadata["vendor_loadable"], bool)
    assert isinstance(metadata["native_geometry"], bool)
    assert isinstance(metadata["native_history"], bool)
    assert isinstance(metadata["native_assembly"], bool)
    assert isinstance(metadata["native_self_contained"], bool)
    assert metadata["referenced_files_written"] == 0
    if metadata["compatibility"] != "native-exact":
        assert metadata["vendor_loadable"] is False
        assert metadata["native_geometry"] is False
        assert metadata["native_history"] is False
        assert metadata["native_assembly"] is False


@lru_cache(maxsize=len(MATRIX_SOURCES))
def _matrix_document(source: Path) -> CadDocument:
    return open_document(source)


def test_swap_formats_match_readme_and_document_kinds() -> None:
    supported = README.read_text(encoding="utf-8").split("## Supported formats", 1)[1]
    supported = supported.split("\n## ", 1)[0]
    readme_suffixes = set(re.findall(r"`(\.[A-Za-z0-9]+)`", supported))
    assert readme_suffixes == set(FORMAT_BY_SUFFIX)
    assert set(PART_SUFFIXES) | set(ASSEMBLY_SUFFIXES) == readme_suffixes
    assert set(PART_SUFFIXES) & set(ASSEMBLY_SUFFIXES) == {".FCStd"}
    assert len(SUPPORTED_FILES) == 155


@pytest.mark.parametrize(
    ("name", "source_suffix", "source", "is_assembly", "destination_suffix"),
    MATRIX_CASES,
    ids=[f"{case[0]}-to-{case[4][1:].lower()}" for case in MATRIX_CASES],
)
def test_every_valid_format_swap_runs_both_directions(
    name: str,
    source_suffix: str,
    source: Path,
    is_assembly: bool,
    destination_suffix: str,
    tmp_path: Path,
) -> None:
    original = _matrix_document(source)
    assert (original.assembly is not None) == is_assembly
    original_signature = _document_signature(original)
    destination = tmp_path / f"{name}_swapped{destination_suffix}"
    result = convert(source, destination)
    restored = open_document(destination)
    assert result.source_format == FORMAT_BY_SUFFIX[source_suffix]
    assert result.destination_format == FORMAT_BY_SUFFIX[destination_suffix]
    assert result.output.path == destination.resolve()
    assert result.output.bytes_written == destination.stat().st_size
    assert restored.validate() == ()
    assert _document_signature(restored) == original_signature
    _assert_target(restored, destination_suffix, destination, is_assembly)
    _assert_truthful_vendor_result(result, destination_suffix)
    reverse = tmp_path / f"{name}_reversed{source_suffix}"
    reverse_result = convert(destination, reverse)
    reversed_document = open_document(reverse)
    assert reverse_result.destination_format == FORMAT_BY_SUFFIX[source_suffix]
    assert reversed_document.validate() == ()
    assert _document_signature(reversed_document) == original_signature
    _assert_target(reversed_document, source_suffix, reverse, is_assembly)
    _assert_truthful_vendor_result(reverse_result, source_suffix)


@pytest.mark.parametrize(
    "source",
    SUPPORTED_FILES,
    ids=lambda path: str(path.relative_to(EXAMPLES)),
)
def test_every_supported_example_swaps_to_every_valid_format_and_back(
    source: Path,
) -> None:
    source_suffix = _suffix(source)
    original = open_document(source)
    is_assembly = original.assembly is not None
    original_signature = _document_signature(original)
    for destination_suffix in _target_suffixes(original):
        destination = BytesIO()
        forward = convert(
            source,
            destination,
            destination_format=FORMAT_BY_SUFFIX[destination_suffix],
        )
        destination_bytes = destination.getvalue()
        restored = open_document(destination_bytes)
        assert forward.destination_format == FORMAT_BY_SUFFIX[destination_suffix]
        assert forward.output.bytes_written == len(destination_bytes)
        assert restored.validate() == ()
        assert _document_signature(restored) == original_signature
        _assert_target(
            restored,
            destination_suffix,
            destination_bytes,
            is_assembly,
        )
        _assert_truthful_vendor_result(forward, destination_suffix)
        reverse = BytesIO()
        backward = convert(
            destination_bytes,
            reverse,
            destination_format=FORMAT_BY_SUFFIX[source_suffix],
        )
        reverse_bytes = reverse.getvalue()
        reversed_document = open_document(reverse_bytes)
        assert backward.destination_format == FORMAT_BY_SUFFIX[source_suffix]
        assert backward.output.bytes_written == len(reverse_bytes)
        assert reversed_document.validate() == ()
        assert _document_signature(reversed_document) == original_signature
        _assert_target(reversed_document, source_suffix, reverse_bytes, is_assembly)
        _assert_truthful_vendor_result(backward, source_suffix)
