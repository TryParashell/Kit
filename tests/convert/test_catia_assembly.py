from __future__ import annotations

from dataclasses import replace
import io
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import pytest

from convert import convert, open_document
from convert.adapters import ReadOptions
from convert.adapters.catia import CatiaAdapter, Cfv2Archive, write_catia
from convert.adapters.catia.assembly import (
    _under_root,
    decode_product_table,
    native_product_assembly,
)
from convert.adapters.freecad import read_freecad, write_freecad
from interchange import ComponentKind, Matrix4, frozen_mapping


ROOT = Path(__file__).parents[2]
CATPRODUCTS = ROOT / "examples" / ".CATProduct"


@pytest.mark.parametrize(
    ("name", "root_name", "token_count", "instance_count"),
    (
        (
            "Brake_Pedal_Assembly - Backup 1.CATProduct",
            "Brake_Pedal_Assembly",
            100,
            48,
        ),
        (
            "Brake_Pedal_Assembly - Backup 2.CATProduct",
            "Brake_Pedal_Assembly",
            37,
            7,
        ),
        ("Tilton_Set.CATProduct", "Tilton", 38, 4),
    ),
)
def test_every_catproduct_length_prefixed_table_is_decoded(
    name: str,
    root_name: str,
    token_count: int,
    instance_count: int,
) -> None:
    path = CATPRODUCTS / name
    table = decode_product_table(Cfv2Archive.from_bytes(path.read_bytes()))
    assert table.root_name == root_name
    assert table.stream_name == "Data"
    assert len(table.tokens) == token_count
    assert len(table.occurrences) == instance_count


def test_catproduct_occurrence_pairing_retains_variants_and_custom_names() -> None:
    brake = decode_product_table(
        Cfv2Archive.from_bytes(
            (CATPRODUCTS / "Brake_Pedal_Assembly - Backup 1.CATProduct").read_bytes()
        )
    )
    assert (
        brake.occurrences[-1].definition_name,
        brake.occurrences[-1].instance_name,
    ) == (
        "Low_Head_M4x20 1",
        "Low_Head_M4x20 2",
    )
    assert (
        sum(item.definition_name == "Washer_6_DIN_433_1" for item in brake.occurrences)
        == 4
    )
    tilton = decode_product_table(
        Cfv2Archive.from_bytes((CATPRODUCTS / "Tilton_Set.CATProduct").read_bytes())
    )
    assert [
        (item.definition_name, item.instance_name) for item in tilton.occurrences
    ] == [
        ("4876", "I_4876.2"),
        ("4876_1", "I_4876.3"),
        ("4784", "I_4784.5"),
        (
            "Brake_bias_90_degree_coupler",
            "I_Brake_bias_90_degree_coupler.1",
        ),
    ]


def test_catproduct_resolves_supplied_documents_by_internal_product_name() -> None:
    path = CATPRODUCTS / "Brake_Pedal_Assembly - Backup 1.CATProduct"
    document = CatiaAdapter().read(
        path,
        ReadOptions(include_brep=False),
    )
    assembly = document.assembly
    assert assembly is not None
    assert len(assembly.instances) == 48
    assert len(assembly.definitions) == 25
    assert len(assembly.documents) == 19
    definitions = {item.name: item for item in assembly.definitions}
    assert Path(definitions["Brake_pedal"].source_path).name == "Pedal_Body.CATPart"
    assert definitions["Brake_pedal"].kind == ComponentKind.PART
    assert (
        Path(definitions["Screw_ISO_7379_M6_8_30"].source_path).name
        == "Fitted_Bolet_M6_8x30.CATPart"
    )
    assert (
        Path(definitions["Low_Head_M4x20 1"].source_path).name
        == "Low_Head_M4x20.CATPart"
    )
    tilton = definitions["Tilton"]
    assert tilton.kind == ComponentKind.ASSEMBLY
    assert Path(tilton.source_path).name == "Tilton_Set.CATProduct"
    linked = assembly.document(tilton.document_id)
    assert linked.assembly is not None
    linked_definitions = {item.name: item for item in linked.assembly.definitions}
    assert Path(linked_definitions["4876_1"].source_path).name == "4876_1.CATPart"
    assert linked_definitions["4876_1"].document_id
    assert assembly.attributes["linked_document_count"] == 19
    assert assembly.attributes["linked_feature_count"] == 18
    missing = next(
        item
        for item in document.diagnostics
        if item.code == "catia.product.component_sources_missing"
    )
    assert missing.attributes["definition_names"] == (
        "Brake_Platform_2",
        "Brake_Platform",
        "Brake_Pedal_Shaft",
        "Reservoir_Holder",
        "Foot_Plate",
    )


def test_catproduct_provenance_spans_slice_exact_native_tokens() -> None:
    path = CATPRODUCTS / "Tilton_Set.CATProduct"
    data = path.read_bytes()
    document = CatiaAdapter().read(path, ReadOptions(include_brep=False))
    assembly = document.assembly
    assert assembly is not None
    for instance in assembly.instances:
        provenance = instance.provenance
        assert provenance is not None
        encoded = b"".join(
            data[span.offset : span.offset + span.length] for span in provenance.spans
        )
        assert encoded == instance.name.encode("ascii")
        assert all(span.stream == "Data" for span in provenance.spans)
    root = assembly.definition(assembly.root_definition_id)
    provenance = root.provenance
    assert provenance is not None
    encoded = b"".join(
        data[span.offset : span.offset + span.length] for span in provenance.spans
    )
    assert encoded == b"Tilton"


def test_catproduct_unresolved_positions_and_constraints_are_explicit() -> None:
    document = CatiaAdapter().read(
        CATPRODUCTS / "Tilton_Set.CATProduct",
        ReadOptions(include_brep=False),
    )
    assembly = document.assembly
    assert assembly is not None
    assert assembly.mates == ()
    assert all(item.transform == Matrix4() for item in assembly.instances)
    assert all(
        item.attributes["transform_resolved"] is False for item in assembly.instances
    )
    assert assembly.attributes["transform_status"] == "native-only"
    assert assembly.attributes["constraint_status"] == "native-only"
    assert {item.code for item in document.diagnostics} >= {
        "catia.product.transforms_unresolved",
        "catia.product.constraints_unresolved",
    }


@pytest.mark.parametrize(
    "name",
    (
        "Brake_Pedal_Assembly - Backup 1.CATProduct",
        "Brake_Pedal_Assembly - Backup 2.CATProduct",
        "Tilton_Set.CATProduct",
    ),
)
def test_every_native_catproduct_replays_byte_exactly(
    name: str, tmp_path: Path
) -> None:
    source = CATPRODUCTS / name
    document = CatiaAdapter().read(source)
    output = tmp_path / name
    result = write_catia(document, output)
    assert result.metadata["mode"] == "exact_native_roundtrip"
    assert output.read_bytes() == source.read_bytes()


def test_catproduct_memory_source_retains_structure_without_file_resolution() -> None:
    source = CATPRODUCTS / "Brake_Pedal_Assembly - Backup 1.CATProduct"
    document = CatiaAdapter().read(
        source.read_bytes(),
        ReadOptions(include_brep=False),
    )
    assembly = document.assembly
    assert assembly is not None
    assert len(assembly.instances) == 48
    assert assembly.documents == ()


@pytest.mark.parametrize(
    ("values", "limit"),
    (
        ({"component_search_max_files": 1}, "files"),
        ({"component_search_max_total_bytes": 1}, "total_bytes"),
        (
            {
                "component_search_root": ROOT / "examples",
                "component_search_max_depth": 0,
            },
            "depth",
        ),
    ),
)
def test_catproduct_component_search_limits_are_enforced(
    values: dict[str, object], limit: str
) -> None:
    document = CatiaAdapter().read(
        CATPRODUCTS / "Tilton_Set.CATProduct",
        ReadOptions(
            include_brep=False,
            strict=False,
            values=frozen_mapping(values),
        ),
    )
    assembly = document.assembly
    assert assembly is not None
    assert assembly.documents == ()
    diagnostic = next(
        item
        for item in document.diagnostics
        if item.code == "catia.product.component_search_limit"
    )
    assert diagnostic.attributes["limit"] == limit


def test_catproduct_component_search_rejects_reparse_escape(
    tmp_path: Path,
) -> None:
    link = tmp_path / "outside-parts"
    try:
        link.symlink_to(ROOT / "examples" / ".CATPart", target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable")
    document = CatiaAdapter().read(
        CATPRODUCTS / "Tilton_Set.CATProduct",
        ReadOptions(
            include_brep=False,
            strict=False,
            values=frozen_mapping({"component_search_root": tmp_path}),
        ),
    )
    assembly = document.assembly
    assert assembly is not None
    assert assembly.documents == ()
    rejected = tuple(
        item
        for item in document.diagnostics
        if item.code == "catia.product.component_search_rejected"
    )
    assert any(item.attributes["reason"] == "reparse_point" for item in rejected)


def test_catproduct_component_root_containment_rejects_escape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "components"
    root.mkdir()
    inside = root / "inside.CATPart"
    outside = tmp_path / "outside.CATPart"
    inside.touch()
    outside.touch()
    assert _under_root(inside.resolve(), root.resolve())
    assert not _under_root(outside.resolve(), root.resolve())


def test_catproduct_component_hash_change_prevents_linking() -> None:
    path = CATPRODUCTS / "Tilton_Set.CATProduct"
    archive = Cfv2Archive.from_bytes(path.read_bytes())
    adapter = CatiaAdapter()

    def mismatched_reader(component: Path, options: ReadOptions):
        values = dict(options.values)
        values["resolve_components"] = False
        document = adapter.read(
            component,
            replace(options, strict=False, values=frozen_mapping(values)),
        )
        return replace(
            document,
            source=replace(document.source, sha256="0" * 64),
        )

    assembly, diagnostics = native_product_assembly(
        archive,
        str(path.resolve()),
        ReadOptions(include_brep=False, strict=False),
        mismatched_reader,
    )
    assert assembly.documents == ()
    changed = tuple(
        item
        for item in diagnostics
        if item.code == "catia.product.component_source_changed"
    )
    assert len(changed) == 4
    assert all(item.attributes["indexed_sha256"] != "0" * 64 for item in changed)


def test_catproduct_to_fcstd_structural_roundtrip(tmp_path: Path) -> None:
    source = CATPRODUCTS / "Brake_Pedal_Assembly - Backup 1.CATProduct"
    output = tmp_path / "Brake.FCStd"
    result = convert(source, output)
    restored = open_document(output)
    assembly = restored.assembly
    assert assembly is not None
    assert len(assembly.instances) == 48
    assert len(assembly.definitions) == 25
    assert len(assembly.documents) == 19
    assert assembly.mates == ()
    assert result.output.metadata["component_file_count"] == 19
    component_directory = output.parent / output.stem
    component_files = tuple(sorted(component_directory.glob("*.FCStd")))
    assert len(component_files) == 19
    component_roots: dict[Path, ET.Element] = {}
    cgm_count = 0
    for component in component_files:
        component_document = open_document(component)
        cgm_payloads = tuple(
            payload
            for payload in component_document.brep_payloads
            if payload.format_id == "catia.cgm"
        )
        with zipfile.ZipFile(component) as archive:
            names = set(archive.namelist())
            root = ET.fromstring(archive.read("Document.xml"))
            component_roots[component.resolve()] = root
            target_node = root.find(
                "./ObjectData/Object[@name='KitMetadata']/Properties/"
                "Property[@name='ExternalLinkTarget']/String"
            )
            assert target_node is not None
            target = target_node.get("value", "")
            assert target
            assert root.find(f"./Objects/Object[@name='{target}']") is not None
            if cgm_payloads:
                assert len(cgm_payloads) == 1
                cgm = cgm_payloads[0]
                entry = "interchange/native/catia_native_cgm.cgm"
                assert entry in names
                assert archive.read(entry) == cgm.data
                assert "interchange/native/catia_native_cgm.brp" not in names
                assert not any(name.endswith(".Shape.brp") for name in names)
                cgm_count += 1
    assert cgm_count == 18
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    external_links = tuple(
        link for link in root.findall(".//XLink") if link.get("file")
    )
    assert external_links
    for link in external_links:
        component = (output.parent / link.get("file", "")).resolve()
        component_root = component_roots[component]
        target = link.get("name", "")
        assert target
        assert component_root.find(f"./Objects/Object[@name='{target}']") is not None


def test_catproduct_to_embedded_fcstd_structural_roundtrip() -> None:
    source = CATPRODUCTS / "Brake_Pedal_Assembly - Backup 1.CATProduct"
    document = open_document(source)
    output = io.BytesIO()
    write_freecad(document, output)
    data = output.getvalue()
    restored = read_freecad(data)
    assembly = restored.assembly
    assert assembly is not None
    assert len(assembly.instances) == 48
    assert len(assembly.definitions) == 25
    assert len(assembly.documents) == 19
    assert assembly.mates == ()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    object_names = {node.get("name", "") for node in root.findall("./Objects/Object")}
    internal_links = tuple(
        link
        for link in root.findall(
            "./ObjectData/Object/Properties/Property[@name='LinkedObject']/XLink"
        )
        if not link.get("file")
    )
    assert len(internal_links) == 48
    assert len({link.get("name", "") for link in internal_links}) == 24
    assert all(link.get("name", "") in object_names for link in internal_links)
    brake_target = "Definition_catia_definition_2_Bodies"
    assert any(link.get("name", "") == brake_target for link in internal_links)
    brake_group = root.find(f"./ObjectData/Object[@name='{brake_target}']")
    assert brake_group is not None
    assert {
        link.get("value", "")
        for link in brake_group.findall(
            "./Properties/Property[@name='Group']/LinkList/Link"
        )
    } == {"Definition_catia_definition_2_Brake_pedal"}
