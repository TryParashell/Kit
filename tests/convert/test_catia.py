# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
import struct
from xml.etree import ElementTree as ET
import zipfile
import zlib

import pytest

from convert import (
    ApplicationUsabilityError,
    convert,
    open_document,
    registry,
    write_document,
)
from convert.adapters import ReadOptions, WriteOptions
from convert.adapters.base import CarrierReason, TransferMode
from convert.adapters.catia import (
    CatiaAdapter,
    CatiaAdapterError,
    Cfv2Archive,
    Cfv2FormatError,
    OsmxArchive,
    OsmxFormatError,
    append_cfv2_stream,
    build_cfv2,
    build_declaration,
    read_catia,
    write_catia,
)
from convert.adapters.catia.adapter import _semantic_digest
from convert.adapters.catia.format import (
    DOCUMENT_TYPE_BY_SUFFIX,
    INFO,
    PART_DOCUMENT_TYPE,
    PRODUCT_DOCUMENT_TYPE,
    SUFFIX_BY_DOCUMENT_TYPE,
)
from convert.adapters.freecad.brep import brep_model_brep
from convert.adapters.solidworks import read_sldprt, write_sldprt
from convert.parasolid import encode_brep_model
from interchange import (
    BrepPayload,
    Capability,
    Configuration,
    Diagnostic,
    NativeFeatureDefinition,
    PayloadRole,
    Provenance,
    Severity,
    frozen_mapping,
)
from tests.interchange.test_document import document
from tests.interchange.test_brep import triangle_brep

ROOT = Path(__file__).parents[2]
CATPARTS = ROOT / "examples" / ".CATPart"
CATPRODUCTS = ROOT / "examples" / ".CATProduct"
SLDPRT = ROOT / "examples" / ".SLDPRT" / "example.SLDPRT"
SLDASM = ROOT / "examples" / "Random" / "Pistons" / "Piston.SLDASM"


def test_catia_format_names_have_one_authoritative_bijection() -> None:
    assert CatiaAdapter().info is INFO
    assert tuple(DOCUMENT_TYPE_BY_SUFFIX) == INFO.extensions
    assert tuple(DOCUMENT_TYPE_BY_SUFFIX.values()) == (
        PART_DOCUMENT_TYPE,
        PRODUCT_DOCUMENT_TYPE,
    )
    assert SUFFIX_BY_DOCUMENT_TYPE == {
        document_type: suffix
        for suffix, document_type in DOCUMENT_TYPE_BY_SUFFIX.items()
    }


def _packed_manifest(raw: bytes) -> bytes:
    return b"".join(
        (
            b"KITCFV2\x01",
            struct.pack(">Q", len(raw)),
            hashlib.sha256(raw).digest(),
            zlib.compress(raw),
        )
    )


def _parasolid_payload(
    payload_id: str,
    data: bytes,
    *,
    kind: str = "partition",
    format_id: str = "parasolid",
) -> BrepPayload:
    return BrepPayload(
        payload_id,
        format_id,
        kind,
        "SCH_SW_32001_11000",
        hashlib.sha256(data).hexdigest(),
        data=data,
        source_stream=payload_id,
        role=PayloadRole.BREP,
        file_extension=".x_b" if format_id != "catia.cgm" else ".cgm",
    )


def _opencascade_payload(
    payload_id: str,
    data: bytes,
    *,
    kind: str = "shape",
    format_id: str = "opencascade",
) -> BrepPayload:
    return BrepPayload(
        payload_id,
        format_id,
        kind,
        "CASCADE Topology V1",
        hashlib.sha256(data).hexdigest(),
        data=data,
        source_stream=f"{payload_id}.brep",
        role=PayloadRole.BREP,
        file_extension=".brep",
    )


def test_catia_carrier_decodes_one_parasolid_model_without_changing_payloads() -> None:
    encoded = encode_brep_model(triangle_brep())
    payload = _parasolid_payload("partition", encoded)
    source = replace(document(), brep_payloads=(payload,))
    output = BytesIO()
    write_catia(source, output, allow_non_native=True)
    restored = read_catia(output.getvalue())
    assert restored.brep is not None
    assert restored.brep.validate(frozenset({"body:1"})) == ()
    assert (
        next(item for item in restored.brep_payloads if item.id == payload.id)
        == payload
    )


def test_catia_carrier_refuses_ambiguous_or_delta_parasolid_models() -> None:
    encoded = encode_brep_model(triangle_brep())
    for payloads in (
        (
            _parasolid_payload("partition:1", encoded),
            _parasolid_payload("partition:2", encoded),
        ),
        (
            _parasolid_payload("partition", encoded),
            _parasolid_payload("delta", encoded, kind="deltas"),
        ),
    ):
        output = BytesIO()
        write_catia(
            replace(document(), brep_payloads=payloads),
            output,
            allow_non_native=True,
        )
        restored = read_catia(output.getvalue())
        assert restored.brep is None
        assert (
            tuple(
                item
                for item in restored.brep_payloads
                if item.id in {p.id for p in payloads}
            )
            == payloads
        )


def test_catia_cgm_payload_is_never_treated_as_parasolid() -> None:
    encoded = encode_brep_model(triangle_brep())
    payload = _parasolid_payload(
        "catia:native-cgm",
        encoded,
        kind="native_brep",
        format_id="catia.cgm",
    )
    output = BytesIO()
    write_catia(
        replace(document(), brep_payloads=(payload,)),
        output,
        allow_non_native=True,
    )
    restored = read_catia(output.getvalue())
    assert restored.brep is None
    assert (
        next(item for item in restored.brep_payloads if item.id == payload.id)
        == payload
    )


@pytest.mark.parametrize(
    "format_id",
    ("freecad.brep", "opencascade", "opencascade.brep"),
)
def test_catia_carrier_decodes_supported_opencascade_payloads(format_id: str) -> None:
    encoded = brep_model_brep(triangle_brep())
    payload = _opencascade_payload("shape", encoded, format_id=format_id)
    output = BytesIO()
    write_catia(
        replace(document(), brep_payloads=(payload,)),
        output,
        allow_non_native=True,
    )
    restored = read_catia(output.getvalue())
    assert restored.brep is not None
    assert restored.brep.validate(frozenset({"body:1"})) == ()
    assert restored.brep.bodies[0].design_body_id == "body:1"
    assert (
        next(item for item in restored.brep_payloads if item.id == payload.id)
        == payload
    )


def test_catia_carrier_refuses_ambiguous_or_delta_opencascade_models() -> None:
    encoded = brep_model_brep(triangle_brep())
    for payloads in (
        (
            _opencascade_payload("shape:1", encoded),
            _opencascade_payload("shape:2", encoded),
        ),
        (
            _opencascade_payload("shape", encoded),
            _opencascade_payload("delta", encoded, kind="delta"),
        ),
        (
            _opencascade_payload("shape", encoded),
            _parasolid_payload("partition", encode_brep_model(triangle_brep())),
        ),
    ):
        output = BytesIO()
        write_catia(
            replace(document(), brep_payloads=payloads),
            output,
            allow_non_native=True,
        )
        restored = read_catia(output.getvalue())
        assert restored.brep is None
        assert (
            tuple(
                item
                for item in restored.brep_payloads
                if item.id in {payload.id for payload in payloads}
            )
            == payloads
        )


def test_pre_payload_field_catpart_manifest_restores_roles_and_envelope(
    tmp_path: Path,
) -> None:
    native_data = b"legacy CATPart envelope"
    native_digest = hashlib.sha256(native_data).digest()
    source = replace(
        document(),
        brep_payloads=(
            BrepPayload(
                "catia:native-document",
                "catia.v5.cfv2",
                "native_document",
                "CATPart",
                hashlib.sha256(native_data).hexdigest(),
                data=native_data,
                source_stream="V5_CFV2",
                role=PayloadRole.DOCUMENT,
                file_extension=".catpart",
            ),
            BrepPayload(
                "catia:native-document-binding",
                "catia.v5.sha256",
                "native_document_binding",
                "sha256",
                hashlib.sha256(native_digest).hexdigest(),
                data=native_digest,
                source_stream="V5_CFV2",
                role=PayloadRole.VERIFICATION,
                file_extension=".sha256",
            ),
            BrepPayload(
                "catia:native-cgm",
                "catia.cgm",
                "native_brep",
                "CGMGeom",
                hashlib.sha256(b"legacy CGM").hexdigest(),
                data=b"legacy CGM",
                source_stream="1000_00000003_3",
                role=PayloadRole.BREP,
                file_extension=".cgm",
            ),
        ),
    )
    manifest = json.loads(source.to_json(indent=None))
    for payload in manifest["brep_payloads"]["$tuple"]:
        payload.pop("role")
        payload.pop("file_extension")
    carrier = build_cfv2(
        (("KitInterchange", _packed_manifest(json.dumps(manifest).encode("utf-8"))),)
    )
    path = tmp_path / "legacy.CATPart"
    path.write_bytes(carrier)
    restored = read_catia(path)
    by_kind = {payload.kind: payload for payload in restored.brep_payloads}
    assert set(by_kind) == {
        "native_document",
        "native_document_binding",
        "native_brep",
    }
    assert by_kind["native_brep"].role == PayloadRole.BREP
    assert by_kind["native_brep"].file_extension == ".cgm"
    assert by_kind["native_brep"].data == b"legacy CGM"
    assert by_kind["native_document"].role == PayloadRole.DOCUMENT
    assert by_kind["native_document"].file_extension == ".catpart"
    assert by_kind["native_document"].data == carrier
    assert by_kind["native_document_binding"].role == PayloadRole.VERIFICATION
    assert by_kind["native_document_binding"].file_extension == ".sha256"
    assert by_kind["native_document_binding"].data == hashlib.sha256(carrier).digest()


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
        declaration_payloads = document.brep_payloads[2:]
        assert len(declaration_payloads) == len(declarations)
        for declaration, payload in zip(declarations, declaration_payloads):
            declared_stream = archive.outer.stream(declaration.stream_name)
            assert declared_stream is not None
            declared_data = archive.stream_bytes(declared_stream)
            assert payload.schema == declaration.class_name
            assert payload.source_stream == declaration.stream_name
            assert payload.sha256 == hashlib.sha256(declared_data).hexdigest()
            assert payload.data == declared_data
        assert document.validate() == ()
        output = BytesIO()
        result = CatiaAdapter().write(document, output)
        assert result.metadata["mode"] == "exact_native_roundtrip"
        assert output.getvalue() == source


def test_cfv2_native_stream_append_preserves_every_source_stream() -> None:
    source = (CATPARTS / "Banjo.CATPart").read_bytes()
    original = Cfv2Archive.from_bytes(source)
    generated = Cfv2Archive.from_bytes(
        append_cfv2_stream(source, "KitInterchange", b"manifest")
    )
    assert generated.named_stream("KitInterchange") == b"manifest"
    assert tuple(
        (stream.name, generated.stream_bytes(stream, generated.outer))
        for stream in generated.outer.streams
        if stream.name != "KitInterchange"
    ) == tuple(
        (stream.name, original.stream_bytes(stream, original.outer))
        for stream in original.outer.streams
    )


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
    if document.assembly is not None:
        with pytest.raises(ApplicationUsabilityError) as captured:
            registry.write(
                document,
                output,
                options=WriteOptions(values={"portable": False}),
            )
        assert captured.value.requirements == ("referenced CATIA component files",)
        assert not output.exists()
    result = registry.write(
        document,
        output,
        options=WriteOptions(
            values={
                "portable": False,
                "allow_carrier": document.assembly is not None,
                "require_self_contained": document.assembly is None,
            }
        ),
    )
    assert result.metadata["mode"] == "exact_native_roundtrip"
    assert result.metadata["vendor_loadable"] is True
    assert result.metadata["native_geometry"] is True
    assert result.metadata["native_history"] is True
    assert result.metadata["native_assembly"] is (document.assembly is not None)
    assert result.metadata["native_self_contained"] is (document.assembly is None)
    assert result.metadata["referenced_files_written"] == 0
    assert result.requirements == (
        ("referenced CATIA component files",) if document.assembly is not None else ()
    )
    assert result.near_lossless is (document.assembly is None)
    assert output.read_bytes() == source.read_bytes()


def test_public_sdk_defaults_to_portable_catproduct_writes(
    tmp_path: Path,
) -> None:
    source = CATPRODUCTS / "Tilton_Set.CATProduct"
    document = open_document(source)
    output = tmp_path / source.name
    result = write_document(document, output)
    assert result.metadata["mode"] == "generated_cfv2"
    assert result.metadata["compatibility"] == "kit-neutral-only"
    assert result.metadata["vendor_loadable"] is False
    assert result.metadata["native_self_contained"] is False
    assert open_document(output).assembly == document.assembly
    blocked = tmp_path / f"blocked{source.suffix}"
    with pytest.raises(ApplicationUsabilityError):
        write_document(document, blocked, allow_carrier=False)
    assert not blocked.exists()


@pytest.mark.parametrize(
    ("source", "write_values"),
    (
        (CATPARTS / "Banjo.CATPart", {"rebuild": True}),
        (CATPRODUCTS / "Tilton_Set.CATProduct", {}),
    ),
)
def test_generated_carrier_preserves_native_pair_for_exact_replay(
    source: Path,
    write_values: dict[str, bool],
    tmp_path: Path,
) -> None:
    carrier = tmp_path / f"carrier{source.suffix}"
    result = write_document(
        open_document(source),
        carrier,
        allow_carrier=True,
        values=write_values,
    )
    assert result.metadata["mode"] == "generated_cfv2"
    restored = open_document(carrier)
    preserved_document = next(
        payload
        for payload in restored.brep_payloads
        if payload.id.startswith("catia:preserved-native-document:")
    )
    token = preserved_document.id.removeprefix("catia:preserved-native-document:")
    preserved_binding = next(
        payload
        for payload in restored.brep_payloads
        if payload.id == f"catia:preserved-native-document-binding:{token}"
    )
    native_data = source.read_bytes()
    native_digest = hashlib.sha256(native_data).digest()
    assert preserved_document.data == native_data
    assert preserved_document.sha256 == native_digest.hex()
    assert preserved_binding.data == native_digest
    assert preserved_binding.sha256 == hashlib.sha256(native_digest).hexdigest()
    assert isinstance(
        preserved_document.attributes["catia.replay_semantic_sha256"], str
    )
    replay = tmp_path / f"replay{source.suffix}"
    replay_result = registry.write(
        restored,
        replay,
        options=WriteOptions(
            values={
                "portable": False,
                "allow_carrier": source.suffix.casefold() == ".catproduct",
                "require_self_contained": source.suffix.casefold() != ".catproduct",
            }
        ),
    )
    assert replay_result.metadata["mode"] == "exact_native_roundtrip"
    assert replay_result.requirements == (
        ("referenced CATIA component files",)
        if source.suffix.casefold() == ".catproduct"
        else ()
    )
    assert replay.read_bytes() == native_data
    if source.suffix.casefold() == ".catproduct":
        regenerated = tmp_path / "regenerated.CATProduct"
        write_document(restored, regenerated, allow_carrier=True)
        regenerated_document = open_document(regenerated)
        assert tuple(
            payload
            for payload in regenerated_document.brep_payloads
            if payload.id.startswith("catia:preserved-native-document")
        ) == (preserved_document, preserved_binding)


def test_stripped_carrier_metadata_cannot_promote_catia_replay(tmp_path: Path) -> None:
    original = open_document(CATPARTS / "Banjo.CATPart")
    changed = replace(
        original,
        metadata=frozen_mapping({**original.metadata, "audit_change": True}),
    )
    carrier = tmp_path / "carrier.CATPart"
    first = write_document(changed, carrier, allow_carrier=True)
    assert first.vendor_loadable is False
    restored = open_document(carrier)
    metadata = dict(restored.metadata)
    assert (
        metadata.pop("catia.container_compatibility") == "native-base-neutral-overlay"
    )
    stripped = replace(restored, metadata=frozen_mapping(metadata))
    blocked = tmp_path / "blocked.CATPart"
    with pytest.raises(ApplicationUsabilityError) as captured:
        write_document(stripped, blocked, allow_carrier=False)
    assert captured.value.vendor_loadable is False
    assert not blocked.exists()
    explicit = tmp_path / "explicit.CATPart"
    result = write_document(stripped, explicit, allow_carrier=True)
    assert result.vendor_loadable is False
    assert result.near_lossless is False
    assert explicit.read_bytes() == carrier.read_bytes()
    assert open_document(explicit).feature_timeline == restored.feature_timeline


def test_native_catpart_retains_declared_geometry_and_feature_graphs() -> None:
    source = CATPARTS / "Banjo.CATPart"
    archive = Cfv2Archive.from_bytes(source.read_bytes())
    document = open_document(source)
    assert document.source.format_id == "catia.v5"
    assert document.source.application_version == "V5R28SP6HF0"
    assert document.metadata["catia.document_type"] == "CATPart"
    native_containers = document.brep_payloads[2:]
    assert [payload.schema for payload in native_containers] == [
        declaration.class_name for declaration in archive.declarations()
    ]
    assert [payload.source_stream for payload in native_containers] == [
        declaration.stream_name for declaration in archive.declarations()
    ]
    cgm_declaration = next(
        item for item in archive.declarations() if item.class_name == "CGMGeom"
    )
    cgm_stream = archive.outer.stream(cgm_declaration.stream_name)
    assert cgm_stream is not None
    cgm = next(
        payload
        for payload in document.brep_payloads
        if payload.id == "catia:native-cgm"
    )
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
    feature_graph = next(
        payload
        for payload in document.brep_payloads
        if payload.id == "catia:native-feature-graph"
    )
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
    definition = document.feature_timeline[0].definition
    assert isinstance(definition, NativeFeatureDefinition)
    assert definition.format_id == "catia.v5.osmx"
    assert definition.type_id == "CATPrtCont"
    assert definition.object_data["symbols"] == document.metadata["catia.part_symbols"]
    assert document.capabilities == frozenset(
        {
            Capability.PARAMETRIC_HISTORY,
            Capability.SUPPORT_PLANES,
            Capability.BODY_STRUCTURE,
            Capability.CONFIGURATIONS,
            Capability.BREP,
            Capability.TESSELLATION,
            Capability.NATIVE_PAYLOADS,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
        }
    )
    without_data = CatiaAdapter().read(
        source,
        ReadOptions(include_brep=False, include_tessellation=False),
    )
    native_document = next(
        payload
        for payload in without_data.brep_payloads
        if payload.kind == "native_document"
    )
    assert native_document.data is None
    assert {
        payload.kind
        for payload in without_data.brep_payloads
        if payload.kind != "native_document"
    } == {
        "native_document_binding",
        "native_feature_graph",
        "native_product_graph",
        "native_brep",
        "brep_topology",
        "brep_mode",
        "native_tessellation",
        "native_container",
    }
    assert all(
        payload.data is None
        for payload in without_data.brep_payloads
        if payload.role
        in {PayloadRole.BREP, PayloadRole.TESSELLATION, PayloadRole.DOCUMENT}
    )
    assert all(
        payload.data is not None
        for payload in without_data.brep_payloads
        if payload.role
        in {
            PayloadRole.FEATURE_HISTORY,
            PayloadRole.ASSEMBLY_STRUCTURE,
            PayloadRole.AUXILIARY,
        }
    )
    assert Capability.BREP not in without_data.capabilities


def test_native_catpart_exposes_unrecognized_declared_containers() -> None:
    source = Cfv2Archive.from_bytes((CATPARTS / "Banjo.CATPart").read_bytes())
    product = next(
        value for value in source.declarations() if value.class_name == "CATProdCont"
    )
    part = next(
        value for value in source.declarations() if value.class_name == "CATPrtCont"
    )
    product_stream = source.outer.stream(product.stream_name)
    part_stream = source.outer.stream(part.stream_name)
    assert product_stream is not None
    assert part_stream is not None
    product_stream_name = "1000_00000001_1"
    part_stream_name = "1000_00000002_2"
    custom_stream_name = "1000_00000003_3"
    custom_data = b"company-native-feature-container"
    declarations = b"".join(
        (
            build_declaration(
                product.class_name,
                product.base_class,
                product_stream_name,
                1,
            ),
            build_declaration(
                part.class_name,
                part.base_class,
                part_stream_name,
                2,
            ),
            build_declaration(
                "CompanyFeatureCont",
                "CATFeatCont",
                custom_stream_name,
                3,
            ),
        )
    )
    generated = build_cfv2(
        (
            ("Format", b"CATPart"),
            ("Data", declarations),
            (product_stream_name, source.stream_bytes(product_stream)),
            (part_stream_name, source.stream_bytes(part_stream)),
            (custom_stream_name, custom_data),
        )
    )
    document = CatiaAdapter().read(generated, ReadOptions(include_brep=False))
    custom = next(
        payload
        for payload in document.brep_payloads
        if payload.schema == "CompanyFeatureCont"
    )
    assert custom.kind == "native_container"
    assert custom.format_id == "catia.v5.cfv2.stream"
    assert custom.role == PayloadRole.AUXILIARY
    assert custom.file_extension == ".bin"
    assert custom.data == custom_data
    changed_data = b"changed-company-native-feature-container"
    changed = replace(
        custom,
        data=changed_data,
        sha256=hashlib.sha256(changed_data).hexdigest(),
    )
    modified = replace(
        document,
        brep_payloads=tuple(
            changed if payload.id == custom.id else payload
            for payload in document.brep_payloads
        ),
    )
    output = BytesIO()
    result = CatiaAdapter().write(modified, output)
    assert result.metadata["mode"] == "generated_cfv2"
    assert output.getvalue() != generated


def test_native_catpart_discovers_custom_root_classes_structurally() -> None:
    source = Cfv2Archive.from_bytes((CATPARTS / "Banjo.CATPart").read_bytes())
    product = next(
        value for value in source.declarations() if value.class_name == "CATProdCont"
    )
    part = next(
        value for value in source.declarations() if value.class_name == "CATPrtCont"
    )
    product_stream = source.outer.stream(product.stream_name)
    part_stream = source.outer.stream(part.stream_name)
    assert product_stream is not None
    assert part_stream is not None
    product_stream_name = "1000_00000001_1"
    part_stream_name = "1000_00000002_2"
    declarations = b"".join(
        (
            build_declaration(
                "CompanyProductRoot",
                "CATFeatCont",
                product_stream_name,
                1,
            ),
            build_declaration(
                "CompanyPartRoot",
                "CompanyProductRoot",
                part_stream_name,
                2,
            ),
        )
    )
    generated = build_cfv2(
        (
            ("Format", b"CATPart"),
            ("Data", declarations),
            (product_stream_name, source.stream_bytes(product_stream)),
            (part_stream_name, source.stream_bytes(part_stream)),
        )
    )
    document = CatiaAdapter().read(generated)
    payloads = {payload.schema: payload for payload in document.brep_payloads}
    assert payloads["CompanyProductRoot"].role == PayloadRole.ASSEMBLY_STRUCTURE
    assert payloads["CompanyPartRoot"].role == PayloadRole.FEATURE_HISTORY
    definition = document.feature_timeline[0].definition
    assert isinstance(definition, NativeFeatureDefinition)
    assert definition.type_id == "CompanyPartRoot"
    assert tuple(
        stream["class_name"] for stream in document.metadata["catia.osmx_streams"]
    ) == ("CompanyProductRoot", "CompanyPartRoot")
    assert "CATPrtCont" not in document.diagnostics[-1].message
    assert document.validate() == ()


def test_native_catpart_classifies_container_roles_from_payload_structure() -> None:
    source = Cfv2Archive.from_bytes((CATPARTS / "Banjo.CATPart").read_bytes())
    product = next(
        value for value in source.declarations() if value.class_name == "CATProdCont"
    )
    part = next(
        value for value in source.declarations() if value.class_name == "CATPrtCont"
    )
    cgm = next(
        value for value in source.declarations() if value.class_name == "CGMGeom"
    )
    product_stream = source.outer.stream(product.stream_name)
    part_stream = source.outer.stream(part.stream_name)
    cgm_stream = source.outer.stream(cgm.stream_name)
    assert product_stream is not None
    assert part_stream is not None
    assert cgm_stream is not None
    product_stream_name = "1000_00000001_1"
    part_stream_name = "1000_00000002_2"
    renamed_cgm_stream_name = "1000_00000003_3"
    misleading_stream_name = "1000_00000004_4"
    declarations = b"".join(
        (
            build_declaration(
                product.class_name,
                product.base_class,
                product_stream_name,
                1,
            ),
            build_declaration(
                part.class_name,
                part.base_class,
                part_stream_name,
                2,
            ),
            build_declaration(
                "CompanyGeometryContainer",
                "CATContainer",
                renamed_cgm_stream_name,
                3,
            ),
            build_declaration(
                "CGMGeom",
                "CATContainer",
                misleading_stream_name,
                4,
            ),
        )
    )
    generated = build_cfv2(
        (
            ("Format", b"CATPart"),
            ("Data", declarations),
            (product_stream_name, source.stream_bytes(product_stream)),
            (part_stream_name, source.stream_bytes(part_stream)),
            (renamed_cgm_stream_name, source.stream_bytes(cgm_stream)),
            (misleading_stream_name, b"opaque-company-payload"),
        )
    )
    document = CatiaAdapter().read(generated, ReadOptions(include_brep=False))
    renamed_cgm = next(
        payload
        for payload in document.brep_payloads
        if payload.schema == "CompanyGeometryContainer"
    )
    misleading = next(
        payload for payload in document.brep_payloads if payload.schema == "CGMGeom"
    )
    assert renamed_cgm.role == PayloadRole.BREP
    assert renamed_cgm.format_id == "catia.cgm"
    assert renamed_cgm.data is None
    assert misleading.role == PayloadRole.AUXILIARY
    assert misleading.format_id == "catia.v5.cfv2.stream"
    assert misleading.data == b"opaque-company-payload"


def test_native_catpart_symbol_discovery_preserves_customer_feature_types() -> None:
    source = Cfv2Archive.from_bytes((CATPARTS / "Banjo.CATPart").read_bytes())
    product = next(
        value for value in source.declarations() if value.class_name == "CATProdCont"
    )
    part = next(
        value for value in source.declarations() if value.class_name == "CATPrtCont"
    )
    product_stream = source.outer.stream(product.stream_name)
    part_stream = source.outer.stream(part.stream_name)
    assert product_stream is not None
    assert part_stream is not None
    part_graph = bytearray(source.stream_bytes(part_stream))
    symbol_table_offset = struct.unpack_from("<I", part_graph, 0x64)[0]
    feature_type = b"CustomerDefinedFeature_99"
    part_graph.extend(bytes((len(feature_type) + 1,)) + feature_type)
    struct.pack_into(
        "<I",
        part_graph,
        symbol_table_offset + 2,
        len(part_graph) - symbol_table_offset,
    )
    product_stream_name = "1000_00000001_1"
    part_stream_name = "1000_00000002_2"
    declarations = b"".join(
        (
            build_declaration(
                product.class_name,
                product.base_class,
                product_stream_name,
                1,
            ),
            build_declaration(
                part.class_name,
                part.base_class,
                part_stream_name,
                2,
            ),
        )
    )
    generated = build_cfv2(
        (
            ("Format", b"CATPart"),
            ("Data", declarations),
            (product_stream_name, source.stream_bytes(product_stream)),
            (part_stream_name, bytes(part_graph)),
        )
    )
    document = CatiaAdapter().read(generated, ReadOptions(include_brep=False))
    assert feature_type.decode("ascii") in document.metadata["catia.native_symbols"]
    assert (
        document.feature_timeline[0].attributes["native_symbols"]
        == document.metadata["catia.native_symbols"]
    )
    definition = document.feature_timeline[0].definition
    assert isinstance(definition, NativeFeatureDefinition)
    assert feature_type.decode("ascii") in definition.object_data["symbols"]


def test_native_catpart_principal_plane_names_are_discovered_structurally() -> None:
    source = Cfv2Archive.from_bytes((CATPARTS / "Banjo.CATPart").read_bytes())
    product = next(
        value for value in source.declarations() if value.class_name == "CATProdCont"
    )
    part = next(
        value for value in source.declarations() if value.class_name == "CATPrtCont"
    )
    product_stream = source.outer.stream(product.stream_name)
    part_stream = source.outer.stream(part.stream_name)
    assert product_stream is not None
    assert part_stream is not None
    part_data = bytearray(source.stream_bytes(part_stream))
    graph = OsmxArchive.from_bytes(part_data)
    plane_type_index = graph.values.index("GSMPlane")
    algorithm_id_index = graph.values.index("_PartAlgoConfigUUID")
    indices = (plane_type_index + 1, algorithm_id_index - 2, algorithm_id_index - 1)
    names = ("PrimaryA", "PrimaryB", "PrimaryC")
    for symbol_index, name in zip(indices, names, strict=True):
        symbol = graph.symbols[symbol_index]
        assert len(symbol.value) == len(name)
        part_data[symbol.offset : symbol.offset + len(name)] = name.encode("ascii")
    product_stream_name = "1000_00000001_1"
    part_stream_name = "1000_00000002_2"
    declarations = b"".join(
        (
            build_declaration(
                product.class_name,
                product.base_class,
                product_stream_name,
                1,
            ),
            build_declaration(
                part.class_name,
                part.base_class,
                part_stream_name,
                2,
            ),
        )
    )
    generated = build_cfv2(
        (
            ("Format", b"CATPart"),
            ("Data", declarations),
            (product_stream_name, source.stream_bytes(product_stream)),
            (part_stream_name, bytes(part_data)),
        )
    )
    document = CatiaAdapter().read(generated)
    assert [plane.name for plane in document.support_planes] == list(names)
    assert [
        plane.attributes["principal_index"] for plane in document.support_planes
    ] == [
        0,
        1,
        2,
    ]


def test_adapter_capabilities_cover_the_complete_interchange_schema() -> None:
    assert CatiaAdapter().info.capabilities == frozenset(Capability)


def test_native_catproduct_retains_product_occurrences() -> None:
    source = CATPRODUCTS / "Tilton_Set.CATProduct"
    archive = Cfv2Archive.from_bytes(source.read_bytes())
    document = open_document(source)
    assert document.assembly is not None
    assert [instance.name for instance in document.assembly.instances] == [
        "I_4876.2",
        "I_4876.3",
        "I_4784.5",
        "I_Brake_bias_90_degree_coupler.1",
    ]
    assert len(document.assembly.definitions) == 5
    assert [payload.schema for payload in document.brep_payloads[2:]] == [
        declaration.class_name for declaration in archive.declarations()
    ]
    assert document.capabilities == frozenset(
        {
            Capability.ASSEMBLIES,
            Capability.PARAMETRIC_HISTORY,
            Capability.SUPPORT_PLANES,
            Capability.BODY_STRUCTURE,
            Capability.COMPONENT_DOCUMENTS,
            Capability.CONFIGURATIONS,
            Capability.EXTERNAL_REFERENCES,
            Capability.BREP,
            Capability.TESSELLATION,
            Capability.NATIVE_PAYLOADS,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
        }
    )
    assert Capability.BREP in document.capabilities


def test_pedal_body_exposes_native_parametric_symbols() -> None:
    document = open_document(CATPARTS / "Pedal_Body.CATPart")
    assert document.metadata["catia.product_name"] == "Brake_pedal"
    assert document.metadata["catia.internal_part_name"] == "Part2"
    assert document.metadata["catia.body_name"] == "Brake_pedal"
    native_symbols = document.metadata["catia.native_symbols"]
    assert native_symbols == tuple(
        dict.fromkeys(
            value for value in document.metadata["catia.part_symbols"] if value
        )
    )
    assert {
        "GSMPlane",
        "GSMPoint",
        "GSMPointCoord",
        "GSMAxisToAxis",
        "GSMTranslate",
        "AxisSystem",
        "SectioningPlane",
    } <= set(native_symbols)
    assert document.feature_timeline[0].attributes["native_symbols"] == native_symbols
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


def test_unresolved_catpart_visibility_fails_closed_and_reverses_exactly(
    tmp_path: Path,
) -> None:
    source = CATPARTS / "Banjo.CATPart"
    original = open_document(source)
    output = tmp_path / "Banjo.FCStd"
    result = convert(source, output)
    transfers = {value.capability: value for value in result.transfers}
    assert result.application_usable is False
    assert result.vendor_loadable is True
    assert result.near_lossless is False
    for capability in (Capability.BREP, Capability.TESSELLATION):
        assert transfers[capability].mode is TransferMode.CARRIER
        assert transfers[capability].carrier_reason is CarrierReason.SOURCE_OPAQUE
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        root = ET.fromstring(archive.read("Document.xml"))
        assert not any(name.endswith(".Shape.brp") for name in names)
        assert not any(name.endswith(".MeshKernel.bms") for name in names)
        assert not any(
            value.get("type") == "Mesh::Feature"
            for value in root.findall("./Objects/Object")
        )
        assert not root.findall(".//Part[@file]")
        assert not root.findall(".//Mesh[@file]")
    assert open_document(output) == original
    reversed_part = tmp_path / "Banjo.CATPart"
    reversed_result = convert(output, reversed_part)
    assert reversed_result.application_usable is True
    assert reversed_result.vendor_loadable is True
    assert reversed_part.read_bytes() == source.read_bytes()


def test_solidworks_part_roundtrips_through_generated_catpart(
    tmp_path: Path,
) -> None:
    source = open_document(SLDPRT)
    output = tmp_path / "example.CATPart"
    with pytest.raises(ApplicationUsabilityError):
        convert(SLDPRT, output, allow_carrier=False)
    result = convert(SLDPRT, output, allow_carrier=True)
    assert result.destination_format == "catia.v5"
    assert result.output.metadata["mode"] == "generated_cfv2"
    assert result.output.metadata["compatibility"] == "kit-neutral-only"
    assert result.output.metadata["vendor_loadable"] is False
    assert result.output.metadata["native_geometry"] is False
    assert result.output.metadata["native_history"] is False
    assert result.output.metadata["native_assembly"] is False
    assert result.output.metadata["native_self_contained"] is False
    assert result.output.metadata["referenced_files_written"] == 0
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
    retained = tuple(
        payload
        for payload in restored.brep_payloads
        if payload.kind not in {"native_document", "native_document_binding"}
    )
    assert retained == source.brep_payloads
    assert (
        sum(
            payload.kind == "native_document_binding"
            for payload in restored.brep_payloads
        )
        == 1
    )
    assert (
        sum(payload.kind == "native_document" for payload in restored.brep_payloads)
        == 1
    )


def test_solidworks_assembly_roundtrips_through_generated_catproduct(
    tmp_path: Path,
) -> None:
    source = open_document(SLDASM)
    output = tmp_path / "Piston.CATProduct"
    result = convert(
        SLDASM,
        output,
        allow_carrier=True,
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


def test_catia_destinations_enforce_document_kind(tmp_path: Path) -> None:
    adapter = CatiaAdapter()
    part = open_document(SLDPRT)
    assembly = open_document(SLDASM)
    assert adapter.supports(part, tmp_path / "part.CATPart")
    assert not adapter.supports(part, tmp_path / "part.CATProduct")
    assert adapter.supports(assembly, tmp_path / "assembly.CATProduct")
    assert not adapter.supports(assembly, tmp_path / "assembly.CATPart")
    assert adapter.supports(part, BytesIO())
    assert not adapter.supports(part, StringIO())
    with pytest.raises(ValueError, match=r"\.CATPart"):
        write_catia(part, tmp_path / "part.CATProduct")
    with pytest.raises(ValueError, match=r"\.CATProduct"):
        write_catia(assembly, tmp_path / "assembly.CATPart")


@pytest.mark.parametrize(
    ("source", "wrong_suffix"),
    (
        (CATPARTS / "Banjo.CATPart", ".CATProduct"),
        (CATPRODUCTS / "Tilton_Set.CATProduct", ".CATPart"),
    ),
)
def test_catia_reader_rejects_native_suffix_kind_mismatch(
    source: Path, wrong_suffix: str, tmp_path: Path
) -> None:
    renamed = tmp_path / f"renamed{wrong_suffix}"
    renamed.write_bytes(source.read_bytes())
    with pytest.raises(CatiaAdapterError, match="content requires"):
        read_catia(renamed)


def test_catia_reader_rejects_carrier_suffix_kind_mismatch(tmp_path: Path) -> None:
    valid = tmp_path / "valid.CATPart"
    convert(SLDPRT, valid, allow_carrier=True)
    renamed = tmp_path / "renamed.CATProduct"
    renamed.write_bytes(valid.read_bytes())
    with pytest.raises(CatiaAdapterError, match="content requires"):
        read_catia(renamed)


@pytest.mark.parametrize(
    ("marker", "wrong_suffix"),
    ((b"CATPart", ".CATProduct"), (b"CATProduct", ".CATPart")),
)
def test_catia_reader_uses_content_before_suffix_without_declarations(
    marker: bytes, wrong_suffix: str, tmp_path: Path
) -> None:
    renamed = tmp_path / f"declarationless{wrong_suffix}"
    renamed.write_bytes(build_cfv2((("Format", marker),)))
    with pytest.raises(CatiaAdapterError, match="content requires"):
        read_catia(renamed)


def test_catia_reader_rejects_contradictory_part_and_product_roots() -> None:
    product_stream_name = "1000_00000001_1"
    part_stream_name = "1000_00000002_2"
    declarations = b"".join(
        (
            build_declaration(
                "CATProdCont",
                "CATFeatCont",
                product_stream_name,
                1,
            ),
            build_declaration(
                "CATPrtCont",
                "CATFeatCont",
                part_stream_name,
                2,
            ),
        )
    )
    data = build_cfv2(
        (
            ("Format", b"CATPart"),
            ("Data", declarations),
            (product_stream_name, b"product-root"),
            (part_stream_name, b"part-root"),
        )
    )
    with pytest.raises(CatiaAdapterError, match="contradictory document roots"):
        CatiaAdapter().read(data)


def test_modified_native_document_preserves_native_base_with_neutral_edits(
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
        allow_carrier=True,
    )
    assert result.metadata["mode"] == "native_base_with_neutral_edits"
    assert result.metadata["compatibility"] == "native-base-neutral-overlay"
    assert result.metadata["vendor_loadable"] is False
    assert result.metadata["native_geometry"] is False
    assert result.metadata["native_history"] is False
    assert result.metadata["native_base_vendor_loadable"] is True
    assert result.metadata["native_base_preserved"] is True
    assert result.metadata["native_streams_preserved"] is True
    assert output.read_bytes() != source.read_bytes()
    original_archive = Cfv2Archive.from_bytes(source.read_bytes())
    output_archive = Cfv2Archive.from_bytes(output.read_bytes())
    assert tuple(
        (stream.name, output_archive.stream_bytes(stream, output_archive.outer))
        for stream in output_archive.outer.streams
        if stream.name != "KitInterchange"
    ) == tuple(
        (stream.name, original_archive.stream_bytes(stream, original_archive.outer))
        for stream in original_archive.outer.streams
    )
    restored = open_document(output)
    assert restored.source.format_id == "catia.v5"
    assert (
        restored.metadata["catia.container_compatibility"]
        == "native-base-neutral-overlay"
    )
    assert restored.configurations == changed.configurations
    retained = tuple(
        payload
        for payload in changed.brep_payloads
        if payload.kind not in {"native_document", "native_document_binding"}
    )
    restored_retained = tuple(
        payload
        for payload in restored.brep_payloads
        if payload.kind not in {"native_document", "native_document_binding"}
    )
    assert restored_retained == retained
    assert (
        sum(
            payload.kind == "native_document_binding"
            for payload in restored.brep_payloads
        )
        == 2
    )
    assert (
        sum(payload.kind == "native_document" for payload in restored.brep_payloads)
        == 2
    )
    preserved = next(
        payload
        for payload in restored.brep_payloads
        if payload.id.startswith("catia:preserved-native-document:")
    )
    assert "catia.replay_semantic_sha256" not in preserved.attributes
    replay = tmp_path / "ChangedReplay.CATPart"
    replay_result = write_document(restored, replay, allow_carrier=True)
    assert replay_result.metadata["mode"] == "exact_carrier_roundtrip"
    assert replay_result.metadata["compatibility"] == "native-base-neutral-overlay"
    assert replay.read_bytes() == output.read_bytes()
    tampered = bytearray(output.read_bytes())
    tolerance = output_archive.outer.stream("GesToler")
    assert tolerance is not None
    assert len(tolerance.extents) == 1
    tampered[tolerance.extents[0].physical_offset + 10] ^= 1
    tampered_document = read_catia(bytes(tampered))
    assert tampered_document.metadata["catia.container_compatibility"] == (
        "kit-neutral-only"
    )


def test_embedded_manifest_applies_read_options_and_replays_exactly(
    tmp_path: Path,
) -> None:
    source = open_document(SLDPRT)
    output = tmp_path / "Filtered.CATPart"
    convert(SLDPRT, output, allow_carrier=True)
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
    assert all(
        payload.data is None
        for payload in filtered.brep_payloads
        if payload.role in {PayloadRole.BREP, PayloadRole.DOCUMENT}
    )
    binding = next(
        payload
        for payload in filtered.brep_payloads
        if payload.kind == "native_document_binding"
    )
    assert binding.role == PayloadRole.VERIFICATION
    assert binding.data is None
    assert Capability.BREP not in filtered.capabilities
    assert Capability.NATIVE_PAYLOADS in filtered.capabilities
    assert Capability.TESSELLATION not in filtered.capabilities
    assert filtered.capabilities == source.capabilities - {Capability.BREP}
    assert [item.id for item in filtered.configurations if item.active] == [
        configuration.id
    ]
    complete = open_document(output)
    replay = tmp_path / "Replay.CATPart"
    result = write_catia(complete, replay)
    assert result.metadata["mode"] == "exact_carrier_roundtrip"
    assert replay.read_bytes() == output.read_bytes()


def test_generated_carrier_preserves_declared_sparse_capabilities() -> None:
    source = document()
    output = BytesIO()
    write_catia(source, output, allow_non_native=True)
    restored = CatiaAdapter().read(output.getvalue())
    assert restored.capabilities == source.capabilities


def test_embedded_manifest_preserves_foreign_document_and_auxiliary_payloads(
    tmp_path: Path,
) -> None:
    source = open_document(SLDPRT)
    foreign_document = BrepPayload(
        "future:document",
        "future.cad",
        "native_document",
        "future",
        hashlib.sha256(b"foreign-document").hexdigest(),
        data=b"foreign-document",
        role=PayloadRole.DOCUMENT,
        file_extension=".future",
    )
    unknown_auxiliary = BrepPayload(
        "future:declaration",
        "catia.v5.cfv2.stream",
        "native_container",
        "CustomerContainer",
        hashlib.sha256(b"customer-container").hexdigest(),
        data=b"customer-container",
        role=PayloadRole.AUXILIARY,
        file_extension=".bin",
    )
    carried = replace(
        source,
        brep_payloads=(*source.brep_payloads, foreign_document, unknown_auxiliary),
    )
    output = tmp_path / "ForeignPayloads.CATPart"
    write_catia(carried, output, allow_non_native=True)
    restored = CatiaAdapter().read(output, ReadOptions(include_brep=False))
    by_id = {payload.id: payload for payload in restored.brep_payloads}
    assert by_id[foreign_document.id] == foreign_document
    assert by_id[unknown_auxiliary.id] == unknown_auxiliary
    assert all(
        payload.data is None
        for payload in restored.brep_payloads
        if payload.role == PayloadRole.BREP
    )


def test_embedded_manifest_rejects_unknown_configuration(tmp_path: Path) -> None:
    output = tmp_path / "Configured.CATPart"
    convert(SLDPRT, output, allow_carrier=True)
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
    convert(SLDPRT, catpart, allow_carrier=True)
    result = convert(catpart, output)
    assert result.source_format == "catia.v5"
    assert result.document.source.format_id == "catia.v5"
    assert result.document.metadata["catia.embedded_source_format_id"] == (
        "solidworks.sldprt"
    )


def test_changed_cgm_bytes_disable_exact_native_replay(tmp_path: Path) -> None:
    document = open_document(CATPARTS / "Banjo.CATPart")
    cgm = next(
        payload
        for payload in document.brep_payloads
        if payload.id == "catia:native-cgm"
    )
    changed = replace(
        document,
        brep_payloads=tuple(
            (
                replace(payload, data=(cgm.data or b"") + b"\x00")
                if payload.id == cgm.id
                else payload
            )
            for payload in document.brep_payloads
        ),
    )
    output = tmp_path / "ChangedGeometry.CATPart"
    result = write_catia(changed, output, allow_non_native=True)
    assert result.metadata["mode"] == "native_base_with_neutral_edits"
    assert result.metadata["native_base_preserved"] is True
    assert result.metadata["native_geometry"] is False


def test_recomputed_roundtrip_digest_cannot_forge_native_catpart_semantics() -> None:
    document = open_document(CATPARTS / "Banjo.CATPart")
    feature = document.feature_timeline[0]
    changed = replace(
        document,
        feature_timeline=(replace(feature, name="Forged CATIA feature"),),
    )
    changed = replace(
        changed,
        metadata=frozen_mapping(
            {
                **changed.metadata,
                "catia.roundtrip_sha256": _semantic_digest(changed),
            }
        ),
    )
    output = BytesIO()
    result = write_catia(changed, output, allow_non_native=True)
    assert result.metadata["mode"] == "native_base_with_neutral_edits"
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert read_catia(output.getvalue()).feature_timeline[0].name == (
        "Forged CATIA feature"
    )


def test_swapped_native_document_cannot_exact_replay() -> None:
    document = open_document(CATPARTS / "Banjo.CATPart")
    replacement = (CATPARTS / "Bolt_M5x40.CATPart").read_bytes()
    changed = replace(
        document,
        brep_payloads=tuple(
            (
                replace(
                    payload,
                    data=replacement,
                    sha256=hashlib.sha256(replacement).hexdigest(),
                )
                if payload.kind == "native_document"
                else payload
            )
            for payload in document.brep_payloads
        ),
    )
    output = BytesIO()
    result = write_catia(changed, output, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"
    assert output.getvalue() != replacement


def test_mutated_native_catproduct_cannot_exact_replay() -> None:
    source = CATPRODUCTS / "Tilton_Set.CATProduct"
    document = open_document(source)
    mutated = bytearray(source.read_bytes())
    archive = Cfv2Archive.from_bytes(mutated)
    data_stream = archive.outer.stream("Data")
    assert data_stream is not None
    assert len(data_stream.extents) == 1
    mutated[data_stream.extents[0].physical_offset + 100] ^= 1
    native = bytes(mutated)
    changed = replace(
        document,
        brep_payloads=tuple(
            (
                replace(
                    payload,
                    data=native,
                    sha256=hashlib.sha256(native).hexdigest(),
                )
                if payload.kind == "native_document"
                else payload
            )
            for payload in document.brep_payloads
        ),
    )
    output = BytesIO()
    result = write_catia(changed, output, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"
    assert output.getvalue() != native


def test_generated_carrier_binding_rejects_mutated_physical_stream() -> None:
    source = open_document(SLDPRT)
    carrier = BytesIO()
    write_catia(source, carrier, allow_non_native=True)
    carrier_data = carrier.getvalue()
    document = CatiaAdapter().read(carrier_data)
    unchanged = BytesIO()
    result = write_catia(document, unchanged)
    assert result.metadata["mode"] == "exact_carrier_roundtrip"
    assert result.metadata["compatibility"] == "kit-neutral-only"
    assert result.metadata["vendor_loadable"] is False
    assert unchanged.getvalue() == carrier_data
    mutated = bytearray(carrier_data)
    archive = Cfv2Archive.from_bytes(mutated)
    summary = archive.outer.stream("CATSummaryInformation")
    assert summary is not None
    assert len(summary.extents) == 1
    mutated[summary.extents[0].physical_offset + 10] ^= 1
    native = bytes(mutated)
    changed = replace(
        document,
        brep_payloads=tuple(
            (
                replace(
                    payload,
                    data=native,
                    sha256=hashlib.sha256(native).hexdigest(),
                )
                if payload.kind == "native_document"
                else payload
            )
            for payload in document.brep_payloads
        ),
    )
    rebuilt = BytesIO()
    result = write_catia(changed, rebuilt, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"
    assert rebuilt.getvalue() != native


def test_generated_carrier_binding_rejects_coordinated_mutation() -> None:
    source = open_document(SLDPRT)
    carrier = BytesIO()
    write_catia(source, carrier, allow_non_native=True)
    carrier_data = carrier.getvalue()
    document = CatiaAdapter().read(carrier_data)
    mutated = bytearray(carrier_data)
    archive = Cfv2Archive.from_bytes(mutated)
    summary = archive.outer.stream("CATSummaryInformation")
    assert summary is not None
    assert len(summary.extents) == 1
    mutated[summary.extents[0].physical_offset + 10] ^= 1
    native = bytes(mutated)
    native_digest = hashlib.sha256(native).digest()
    changed = replace(
        document,
        brep_payloads=tuple(
            (
                replace(
                    payload,
                    data=native,
                    sha256=hashlib.sha256(native).hexdigest(),
                )
                if payload.kind == "native_document"
                else (
                    replace(
                        payload,
                        data=native_digest,
                        sha256=hashlib.sha256(native_digest).hexdigest(),
                    )
                    if payload.kind == "native_document_binding"
                    else payload
                )
            )
            for payload in document.brep_payloads
        ),
    )
    rebuilt = BytesIO()
    result = write_catia(changed, rebuilt, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"
    assert rebuilt.getvalue() != native


@pytest.mark.parametrize("change", ("capabilities", "metadata", "diagnostics"))
def test_generated_carrier_semantic_edits_disable_exact_replay(change: str) -> None:
    source = open_document(SLDPRT)
    carrier = BytesIO()
    write_catia(source, carrier, allow_non_native=True)
    document = CatiaAdapter().read(carrier.getvalue())
    if change == "capabilities":
        changed = replace(
            document,
            capabilities=document.capabilities | {Capability.MATERIALS},
        )
    elif change == "metadata":
        changed = replace(
            document,
            metadata=frozen_mapping({**document.metadata, "user.tag": "changed"}),
        )
    else:
        changed = replace(
            document,
            diagnostics=(
                *document.diagnostics,
                Diagnostic("user.changed", "changed", Severity.INFO),
            ),
        )
    rebuilt = BytesIO()
    result = write_catia(changed, rebuilt, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"
    restored = CatiaAdapter().read(rebuilt.getvalue())
    if change == "capabilities":
        assert Capability.MATERIALS in restored.capabilities
    elif change == "metadata":
        assert restored.metadata["user.tag"] == "changed"
    else:
        assert restored.diagnostics[-1].code == "user.changed"


@pytest.mark.parametrize(
    "role",
    (PayloadRole.DOCUMENT, PayloadRole.VERIFICATION),
)
def test_foreign_envelope_role_payload_mutation_invalidates_replay(
    role: PayloadRole,
) -> None:
    source = open_document(SLDPRT)
    payload_data = b"foreign-payload"
    foreign = BrepPayload(
        f"foreign:{role.value}",
        "future.cad",
        "foreign_payload",
        "1",
        hashlib.sha256(payload_data).hexdigest(),
        data=payload_data,
        role=role,
        file_extension=".bin",
    )
    carried = replace(
        source,
        brep_payloads=(*source.brep_payloads, foreign),
    )
    carrier = BytesIO()
    write_catia(carried, carrier, allow_non_native=True)
    document = CatiaAdapter().read(carrier.getvalue())
    changed_data = b"changed-foreign-payload"
    changed = replace(
        document,
        brep_payloads=tuple(
            (
                replace(
                    payload,
                    data=changed_data,
                    sha256=hashlib.sha256(changed_data).hexdigest(),
                )
                if payload.id == foreign.id
                else payload
            )
            for payload in document.brep_payloads
        ),
    )
    rebuilt = BytesIO()
    result = write_catia(changed, rebuilt, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"


def test_legacy_document_binding_is_normalized_once() -> None:
    source = open_document(SLDPRT)
    legacy_data = b"x" * hashlib.sha256().digest_size
    legacy = BrepPayload(
        "catia:native-document-binding",
        "catia.v5.sha256",
        "native_document_binding",
        "sha256",
        hashlib.sha256(legacy_data).hexdigest(),
        data=legacy_data,
        role=PayloadRole.DOCUMENT,
        file_extension=".sha256",
    )
    carried = replace(
        source,
        brep_payloads=(*source.brep_payloads, legacy),
    )
    carrier = BytesIO()
    write_catia(carried, carrier, allow_non_native=True)
    restored = CatiaAdapter().read(carrier.getvalue())
    bindings = tuple(
        payload
        for payload in restored.brep_payloads
        if payload.kind == "native_document_binding"
    )
    assert len(bindings) == 1
    assert bindings[0].role == PayloadRole.VERIFICATION


def test_foreign_payload_fields_disable_exact_replay() -> None:
    source = open_document(SLDPRT)
    payload_data = b"foreign-payload"
    foreign = BrepPayload(
        "foreign:auxiliary",
        "future.cad",
        "foreign_payload",
        "1",
        hashlib.sha256(payload_data).hexdigest(),
        data=payload_data,
        role=PayloadRole.AUXILIARY,
        file_extension=".bin",
    )
    carried = replace(source, brep_payloads=(*source.brep_payloads, foreign))
    carrier = BytesIO()
    write_catia(carried, carrier, allow_non_native=True)
    document = CatiaAdapter().read(carrier.getvalue())
    changed = replace(
        document,
        brep_payloads=tuple(
            (
                replace(
                    payload,
                    source_stream="changed",
                    provenance=Provenance("future.cad", "changed"),
                    attributes=frozen_mapping({"user.tag": "changed"}),
                )
                if payload.id == foreign.id
                else payload
            )
            for payload in document.brep_payloads
        ),
    )
    rebuilt = BytesIO()
    result = write_catia(changed, rebuilt, allow_non_native=True)
    assert result.metadata["mode"] == "generated_cfv2"
    restored = CatiaAdapter().read(rebuilt.getvalue())
    payload = next(item for item in restored.brep_payloads if item.id == foreign.id)
    assert payload.source_stream == "changed"
    assert payload.provenance == Provenance("future.cad", "changed")
    assert payload.attributes == {"user.tag": "changed"}


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
    result = convert(
        SLDASM,
        output,
    )
    assert result.source_format == "solidworks.sldasm"
    assert result.destination_format == "solidworks.sldasm"
    assert result.output.adapter == "solidworks.sldasm"
    assert result.requirements == ()


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


def test_cfv2_ignores_nested_magic_away_from_stream_boundaries() -> None:
    data = bytearray((CATPARTS / "Banjo.CATPart").read_bytes())
    archive = Cfv2Archive.from_bytes(data)
    preview = archive.outer.stream("CATPreview")
    assert preview is not None
    assert len(preview.extents) == 1
    injected = build_cfv2((("Injected", b"value"),))
    start = preview.extents[0].physical_offset + 32
    assert start + len(injected) < (
        preview.extents[0].physical_offset + preview.logical_length
    )
    data[start : start + len(injected)] = injected
    restored = Cfv2Archive.from_bytes(data)
    assert len(restored.nested) == 1


def test_osmx_rejects_excessive_symbol_count() -> None:
    symbols = b"\x02A" * 65_550
    section = b"\x7c\x02" + struct.pack("<I", 6 + len(symbols)) + symbols
    data = bytearray(0x68)
    data[:4] = b"OSMX"
    struct.pack_into("<I", data, 0x64, 0x68)
    data.extend(section)
    with pytest.raises(OsmxFormatError, match="safety limit"):
        OsmxArchive.from_bytes(data)


@pytest.mark.parametrize(
    ("manifest", "message"),
    (
        (
            b"KITCFV2\x01"
            + struct.pack(">Q", 1 << 63)
            + bytes(32)
            + zlib.compress(b""),
            "size limit",
        ),
        (
            b"KITCFV2\x01"
            + struct.pack(">Q", 1)
            + hashlib.sha256(b"ab").digest()
            + zlib.compress(b"ab"),
            "declared length",
        ),
        (
            b"KITCFV2\x01"
            + struct.pack(">Q", 2)
            + hashlib.sha256(b"{}").digest()
            + zlib.compress(b"{}")
            + b"trailing",
            "trailing compressed data",
        ),
    ),
)
def test_manifest_decompression_is_bounded(manifest: bytes, message: str) -> None:
    data = build_cfv2((("KitInterchange", manifest),))
    with pytest.raises(CatiaAdapterError, match=message):
        CatiaAdapter().read(data)


def test_duplicate_nested_manifest_descriptors_are_rejected() -> None:
    nested = build_cfv2(
        (
            ("KitInterchange", b"short"),
            ("OtherManifestX", b"a different and longer manifest"),
        )
    )
    data = bytearray(build_cfv2((("NestedContainer", nested),)))
    archive = Cfv2Archive.from_bytes(data)
    directory = archive.nested[0]
    renamed = directory.stream("OtherManifestX")
    assert renamed is not None
    encoded = "KitInterchange".encode("utf-16le")
    start = renamed.descriptor_offset + 0x10
    data[start : start + len(encoded)] = encoded
    reproduced = Cfv2Archive.from_bytes(data)
    assert (
        sum(stream.name == "KitInterchange" for stream in reproduced.nested[0].streams)
        == 2
    )
    result = CatiaAdapter().probe(data)
    assert result.confidence == 0.0
    assert "multiple CATIA Kit manifests" in result.reason
    with pytest.raises(Cfv2FormatError, match="multiple CATIA Kit manifests"):
        CatiaAdapter().read(data)


def test_deep_manifest_json_is_rejected_without_recursion_leak() -> None:
    raw = ("[" * 2_000 + "0" + "]" * 2_000).encode("utf-8")
    data = build_cfv2((("KitInterchange", _packed_manifest(raw)),))
    result = CatiaAdapter().probe(data)
    assert result.confidence == 0.0
    assert "JSON nesting exceeds the depth limit" in result.reason
    with pytest.raises(CatiaAdapterError, match="JSON nesting exceeds the depth limit"):
        CatiaAdapter().read(data)


def test_shallow_malformed_manifest_json_is_rejected_by_probe_and_read() -> None:
    data = build_cfv2((("KitInterchange", _packed_manifest(b"not-json")),))
    result = CatiaAdapter().probe(data)
    assert result.confidence == 0.0
    assert "invalid Kit document" in result.reason
    with pytest.raises(CatiaAdapterError, match="invalid Kit document"):
        CatiaAdapter().read(data)
