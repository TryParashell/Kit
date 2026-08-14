# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import replace as Replace
import hashlib as Hashlib
from io import BytesIO as BytesIo, StringIO as StringIo
import json as JsonValue
from pathlib import Path as FilePath
import struct as Struct
from xml.etree import ElementTree as XmlTree
import zipfile as Zipfile
import zlib as ZlibValue
import pytest as Pytest
from convert import (
    ApplicationUsabilityError as AppUsabilityError,
    convert as Convert,
    open_document as OpenDoc,
    registry as Registry,
    write_document as WriteDoc,
)
from convert.adapters import ReadOptions, WriteOptions
from convert.adapters.base import CarrierReason, TransferMode
from convert.adapters.catia import (
    CatiaAdapter,
    CatiaAdapterError,
    Cfv2Archive as CfvTwoArchive,
    Cfv2FormatError as CfvTwoFormatError,
    OsmxArchive,
    OsmxFormatError,
    append_cfv2_stream as AppendCfvTwoStream,
    build_cfv2 as BuildCfvTwo,
    build_declaration as BuildDecl,
    read_catia as ReadCatia,
    write_catia as WriteCatia,
)
from convert.adapters.catia.Adapter import _semantic_digest as SemanticDigest
from convert.adapters.catia.Format import (
    DOCUMENT_TYPE_BY_SUFFIX as DocTypeBySuffix,
    INFO as InfoValue,
    PART_DOCUMENT_TYPE as PartDocType,
    PRODUCT_DOCUMENT_TYPE as ProductDocType,
    SUFFIX_BY_DOCUMENT_TYPE as SuffixByDocType,
)
from convert.adapters.freecad.Brep import brep_model_brep as BrepModelBrep
from convert.adapters.solidworks import (
    read_sldprt as ReadSldprt,
    write_sldprt as WriteSldprt,
)
from convert.geometry.Parasolid import encode_brep_model as EncodeBrepModel
from interchange import (
    BrepPayload,
    Capability,
    Configuration as Config,
    Diagnostic as DiagValue,
    NativeFeatureDefinition,
    PayloadRole,
    Provenance,
    Severity,
    frozen_mapping as FrozenMapping,
)
from tests.interchange.document.DocumentTests import document as DocValue
from tests.interchange.brep.BrepTests import triangle_brep as TriangleBrep

# this binding exists because shared behavior needs one stable value
KRootValue = FilePath(__file__).parents[3]

# this binding exists because shared behavior needs one stable value
KCatparts = KRootValue / "examples" / ".CATPart"

# this binding exists because shared behavior needs one stable value
KCatproducts = KRootValue / "examples" / ".CATProduct"

# this binding exists because shared behavior needs one stable value
KSldprt = KRootValue / "examples" / ".SLDPRT" / "example.SLDPRT"

# this binding exists because shared behavior needs one stable value
KSldasm = KRootValue / "examples" / "Random" / "Pistons" / "Piston.SLDASM"


# this definition exists because focused behavior needs one stable owner
def TestFormatNames() -> None:
    assert CatiaAdapter().info is InfoValue
    assert tuple(DocTypeBySuffix) == InfoValue.extensions
    assert tuple(DocTypeBySuffix.values()) == (PartDocType, ProductDocType)
    assert SuffixByDocType == {
        DocType: Suffix for Suffix, DocType in DocTypeBySuffix.items()
    }


# this definition exists because focused behavior needs one stable owner
def PackedManifest(RawValue: bytes) -> bytes:
    return b"".join(
        (
            b"KITCFV2\x01",
            Struct.pack(">Q", len(RawValue)),
            Hashlib.sha256(RawValue).digest(),
            ZlibValue.compress(RawValue),
        )
    )


# this definition exists because focused behavior needs one stable owner
def Parasolid(
    PayloadId: str,
    DataValue: bytes,
    *,
    KindValue: str = "partition",
    FormatId: str = "parasolid",
) -> BrepPayload:
    return BrepPayload(
        PayloadId,
        FormatId,
        KindValue,
        "SCH_SW_32001_11000",
        Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        source_stream=PayloadId,
        role=PayloadRole.BREP,
        file_extension=".x_b" if FormatId != "catia.cgm" else ".cgm",
    )


# this definition exists because focused behavior needs one stable owner
def Opencascade(
    PayloadId: str,
    DataValue: bytes,
    *,
    KindValue: str = "shape",
    FormatId: str = "opencascade",
) -> BrepPayload:
    return BrepPayload(
        PayloadId,
        FormatId,
        KindValue,
        "CASCADE Topology V1",
        Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        source_stream=f"{PayloadId}.brep",
        role=PayloadRole.BREP,
        file_extension=".brep",
    )


# this definition exists because focused behavior needs one stable owner
def TestCarrierOne() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    Payload = Parasolid("partition", Encoded)
    Source = Replace(DocValue(), brep_payloads=(Payload,))
    Output = BytesIo()
    WriteCatia(Source, Output, allow_non_native=True)
    Restored = ReadCatia(Output.getvalue())
    assert Restored.brep is not None
    assert Restored.brep.validate(frozenset({"body:1"})) == ()
    assert (
        next(
            (
                ItemValue
                for ItemValue in Restored.brep_payloads
                if ItemValue.id == Payload.id
            )
        )
        == Payload
    )


# this definition exists because focused behavior needs one stable owner
def TestCarrierOrA() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    for Payloads in (
        (Parasolid("partition:1", Encoded), Parasolid("partition:2", Encoded)),
        (
            Parasolid("partition", Encoded),
            Parasolid("delta", Encoded, KindValue="deltas"),
        ),
    ):
        Output = BytesIo()
        WriteCatia(
            Replace(DocValue(), brep_payloads=Payloads), Output, allow_non_native=True
        )
        Restored = ReadCatia(Output.getvalue())
        assert Restored.brep is None
        assert (
            tuple(
                (
                    ItemValue
                    for ItemValue in Restored.brep_payloads
                    if ItemValue.id in {PointValue.id for PointValue in Payloads}
                )
            )
            == Payloads
        )


# this definition exists because focused behavior needs one stable owner
def TestCgmPayload() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    Payload = Parasolid(
        "catia:native-cgm", Encoded, KindValue="native_brep", FormatId="catia.cgm"
    )
    Output = BytesIo()
    WriteCatia(
        Replace(DocValue(), brep_payloads=(Payload,)), Output, allow_non_native=True
    )
    Restored = ReadCatia(Output.getvalue())
    assert Restored.brep is None
    assert (
        next(
            (
                ItemValue
                for ItemValue in Restored.brep_payloads
                if ItemValue.id == Payload.id
            )
        )
        == Payload
    )


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    "FormatId", ("freecad.brep", "opencascade", "opencascade.brep")
)
def TestCarrier(FormatId: str) -> None:
    Encoded = BrepModelBrep(TriangleBrep())
    Payload = Opencascade("shape", Encoded, FormatId=FormatId)
    Output = BytesIo()
    WriteCatia(
        Replace(DocValue(), brep_payloads=(Payload,)), Output, allow_non_native=True
    )
    Restored = ReadCatia(Output.getvalue())
    assert Restored.brep is not None
    assert Restored.brep.validate(frozenset({"body:1"})) == ()
    assert Restored.brep.bodies[0].design_body_id == "body:1"
    assert (
        next(
            (
                ItemValue
                for ItemValue in Restored.brep_payloads
                if ItemValue.id == Payload.id
            )
        )
        == Payload
    )


# this definition exists because focused behavior needs one stable owner
def TestCarrierOr() -> None:
    Encoded = BrepModelBrep(TriangleBrep())
    for Payloads in (
        (Opencascade("shape:1", Encoded), Opencascade("shape:2", Encoded)),
        (
            Opencascade("shape", Encoded),
            Opencascade("delta", Encoded, KindValue="delta"),
        ),
        (
            Opencascade("shape", Encoded),
            Parasolid("partition", EncodeBrepModel(TriangleBrep())),
        ),
    ):
        Output = BytesIo()
        WriteCatia(
            Replace(DocValue(), brep_payloads=Payloads), Output, allow_non_native=True
        )
        Restored = ReadCatia(Output.getvalue())
        assert Restored.brep is None
        assert (
            tuple(
                (
                    ItemValue
                    for ItemValue in Restored.brep_payloads
                    if ItemValue.id in {Payload.id for Payload in Payloads}
                )
            )
            == Payloads
        )


# this definition exists because focused behavior needs one stable owner
def TestPrePayload(TmpPath: Path) -> None:
    NativeData = b"legacy CATPart envelope"
    NativeDigest = Hashlib.sha256(NativeData).digest()
    Source = Replace(
        DocValue(),
        brep_payloads=(
            BrepPayload(
                "catia:native-document",
                "catia.v5.cfv2",
                "native_document",
                "CATPart",
                Hashlib.sha256(NativeData).hexdigest(),
                data=NativeData,
                source_stream="V5_CFV2",
                role=PayloadRole.DOCUMENT,
                file_extension=".catpart",
            ),
            BrepPayload(
                "catia:native-document-binding",
                "catia.v5.sha256",
                "native_document_binding",
                "sha256",
                Hashlib.sha256(NativeDigest).hexdigest(),
                data=NativeDigest,
                source_stream="V5_CFV2",
                role=PayloadRole.VERIFICATION,
                file_extension=".sha256",
            ),
            BrepPayload(
                "catia:native-cgm",
                "catia.cgm",
                "native_brep",
                "CGMGeom",
                Hashlib.sha256(b"legacy CGM").hexdigest(),
                data=b"legacy CGM",
                source_stream="1000_00000003_3",
                role=PayloadRole.BREP,
                file_extension=".cgm",
            ),
        ),
    )
    Manifest = JsonValue.loads(Source.to_json(indent=None))
    for Payload in Manifest["brep_payloads"]["$tuple"]:
        Payload.pop("role")
        Payload.pop("file_extension")
    Carrier = BuildCfvTwo(
        (("KitInterchange", PackedManifest(JsonValue.dumps(Manifest).encode("utf-8"))),)
    )
    PathValue = TmpPath / "legacy.CATPart"
    PathValue.write_bytes(Carrier)
    Restored = ReadCatia(PathValue)
    ByKind = {Payload.kind: Payload for Payload in Restored.brep_payloads}
    assert set(ByKind) == {"native_document", "native_document_binding", "native_brep"}
    assert ByKind["native_brep"].role == PayloadRole.BREP
    assert ByKind["native_brep"].file_extension == ".cgm"
    assert ByKind["native_brep"].data == b"legacy CGM"
    assert ByKind["native_document"].role == PayloadRole.DOCUMENT
    assert ByKind["native_document"].file_extension == ".catpart"
    assert ByKind["native_document"].data == Carrier
    assert ByKind["native_document_binding"].role == PayloadRole.VERIFICATION
    assert ByKind["native_document_binding"].file_extension == ".sha256"
    assert ByKind["native_document_binding"].data == Hashlib.sha256(Carrier).digest()


# every corpus archive needs the same boundary proof before deeper semantic checks
def CheckArchive(PathValue: FilePath) -> None:
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    assert Archive.outer.offset + Archive.outer.length == PathValue.stat().st_size
    assert Archive.outer.streams
    assert Archive.named_stream("Data")


# physical stream relationships need isolation from document model assertions
def LoadPartState(
    PathValue: FilePath,
    ExpectedClasses: tuple[str, ...],
    FragmentedGeom: set[str],
) -> tuple[bytes, CfvTwoArchive, tuple, object, object]:
    Source = PathValue.read_bytes()
    Archive = CfvTwoArchive.from_bytes(Source)
    Declarations = Archive.declarations()
    assert len(Archive.outer.streams) == 41
    assert (
        tuple((ItemValue.class_name for ItemValue in Declarations)) == ExpectedClasses
    )
    assert tuple((ItemValue.ordinal for ItemValue in Declarations)) == tuple(
        range(1, 9)
    )
    assert all(
        (
            sum(
                (
                    Stream.name == ItemValue.stream_name
                    for Stream in Archive.outer.streams
                )
            )
            == 2
            for ItemValue in Declarations
        )
    )
    assert len(Archive.nested) == 1
    CgrDecl = next(
        (
            ItemValue
            for ItemValue in Declarations
            if ItemValue.class_name == "CATCGRCont"
        )
    )
    CgrStream = Archive.outer.stream(CgrDecl.stream_name)
    assert CgrStream is not None
    assert len(CgrStream.extents) == 1
    assert Archive.nested[0].physical_base == CgrStream.extents[0].physical_offset
    assert (
        Archive.nested[0].offset + Archive.nested[0].length
        == CgrStream.extents[0].physical_offset + CgrStream.logical_length
    )
    CgmDecl = next(
        (ItemValue for ItemValue in Declarations if ItemValue.class_name == "CGMGeom")
    )
    CgmStream = Archive.outer.stream(CgmDecl.stream_name)
    assert CgmStream is not None
    assert len(CgmStream.extents) == (3 if PathValue.name in FragmentedGeom else 1)
    assert len(Archive.stream_bytes(CgmStream)) == CgmStream.logical_length
    PartDecl = next(
        (
            ItemValue
            for ItemValue in Declarations
            if ItemValue.class_name == "CATPrtCont"
        )
    )
    PartStream = Archive.outer.stream(PartDecl.stream_name)
    assert PartStream is not None
    Graph = OsmxArchive.from_bytes(Archive.stream_bytes(PartStream))
    assert Graph.version == "V5R28SP6HF0"
    assert {"MechanicalPart", "xy-plane", "yz-plane", "zx-plane"} <= set(Graph.values)
    return Source, Archive, Declarations, CgmStream, PartStream


# declaration payloads need byte level checks independent from document metadata checks
def CheckDeclData(Archive, DocValue, Declarations: tuple) -> None:
    DeclPayloads = DocValue.brep_payloads[2:]
    assert len(DeclPayloads) == len(Declarations)
    for DeclValue, Payload in zip(Declarations, DeclPayloads):
        DeclaredStream = Archive.outer.stream(DeclValue.stream_name)
        assert DeclaredStream is not None
        DeclaredData = Archive.stream_bytes(DeclaredStream)
        assert Payload.schema == DeclValue.class_name
        assert Payload.source_stream == DeclValue.stream_name
        assert Payload.sha256 == Hashlib.sha256(DeclaredData).hexdigest()
        assert Payload.data == DeclaredData


# native document semantics need one focused proof after physical stream validation
def CheckPartDoc(
    PathValue: FilePath,
    Source: bytes,
    Archive,
    Declarations: tuple,
    CgmStream,
    PartStream,
) -> None:
    DocValue = OpenDoc(PathValue)
    assert len(DocValue.support_planes) == 3
    assert len(DocValue.feature_timeline) == 1
    assert len(DocValue.bodies) == 1
    assert DocValue.metadata["catia.product_name"]
    assert DocValue.metadata["catia.internal_part_name"]
    assert len(DocValue.metadata["catia.container_declarations"]) == 8
    CgmPayload = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.id == "catia:native-cgm"
        )
    )
    assert CgmPayload.data == Archive.stream_bytes(CgmStream)
    FeaturePayload = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.id == "catia:native-feature-graph"
        )
    )
    assert FeaturePayload.data == Archive.stream_bytes(PartStream)
    CheckDeclData(Archive, DocValue, Declarations)
    assert DocValue.validate() == ()
    Output = BytesIo()
    Result = CatiaAdapter().write(DocValue, Output)
    assert Result.metadata["mode"] == "exact_native_roundtrip"
    assert Output.getvalue() == Source


# this definition exists because focused behavior needs one stable owner
def TestRealCorpus() -> None:
    Parts = tuple(sorted(KCatparts.glob("*.CATPart")))
    Products = tuple(sorted(KCatproducts.glob("*.CATProduct")))
    assert len(Parts) == 27
    assert len(Products) == 3
    for PathValue in Parts + Products:
        CheckArchive(PathValue)
    ExpectedClasses = (
        "CATProdCont",
        "CATPrtCont",
        "CGMGeom",
        "CATMFBRP",
        "CATSeeBodyCont",
        "CATBRepModeContainer",
        "CATStdCont",
        "CATCGRCont",
    )
    FragmentedGeom = {
        "4784.CATPart",
        "4876.CATPart",
        "4876_1.CATPart",
        "Pedal_Body.CATPart",
    }
    for PathValue in Parts:
        Source, Archive, Declarations, CgmStream, PartStream = LoadPartState(
            PathValue, ExpectedClasses, FragmentedGeom
        )
        CheckPartDoc(PathValue, Source, Archive, Declarations, CgmStream, PartStream)


# this definition exists because focused behavior needs one stable owner
def TestCfvTwoEvery() -> None:
    Source = (KCatparts / "Banjo.CATPart").read_bytes()
    Original = CfvTwoArchive.from_bytes(Source)
    Generated = CfvTwoArchive.from_bytes(
        AppendCfvTwoStream(Source, "KitInterchange", b"manifest")
    )
    assert Generated.named_stream("KitInterchange") == b"manifest"
    assert tuple(
        (
            (Stream.name, Generated.stream_bytes(Stream, Generated.outer))
            for Stream in Generated.outer.streams
            if Stream.name != "KitInterchange"
        )
    ) == tuple(
        (
            (Stream.name, Original.stream_bytes(Stream, Original.outer))
            for Stream in Original.outer.streams
        )
    )


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    "Source", (KCatparts / "Banjo.CATPart", KCatproducts / "Tilton_Set.CATProduct")
)
def TestRoundtripIs(Source: Path, TmpPath: Path) -> None:
    DocValue = OpenDoc(Source)
    Output = TmpPath / Source.name
    if DocValue.assembly is not None:
        with Pytest.raises(AppUsabilityError) as Captured:
            Registry.write(
                DocValue, Output, options=WriteOptions(values={"portable": False})
            )
        assert Captured.value.requirements == ("referenced CATIA component files",)
        assert not Output.exists()
    Result = Registry.write(
        DocValue,
        Output,
        options=WriteOptions(
            values={
                "portable": False,
                "allow_carrier": DocValue.assembly is not None,
                "require_self_contained": DocValue.assembly is None,
            }
        ),
    )
    assert Result.metadata["mode"] == "exact_native_roundtrip"
    assert Result.metadata["vendor_loadable"] is True
    assert Result.metadata["native_geometry"] is True
    assert Result.metadata["native_history"] is True
    assert Result.metadata["native_assembly"] is (DocValue.assembly is not None)
    assert Result.metadata["native_self_contained"] is (DocValue.assembly is None)
    assert Result.metadata["referenced_files_written"] == 0
    assert Result.requirements == (
        ("referenced CATIA component files",) if DocValue.assembly is not None else ()
    )
    assert Result.near_lossless is (DocValue.assembly is None)
    assert Output.read_bytes() == Source.read_bytes()


# this definition exists because focused behavior needs one stable owner
def TestPublicSdkTo(TmpPath: Path) -> None:
    Source = KCatproducts / "Tilton_Set.CATProduct"
    DocValue = OpenDoc(Source)
    Output = TmpPath / Source.name
    Result = WriteDoc(DocValue, Output)
    assert Result.metadata["mode"] == "generated_cfv2"
    assert Result.metadata["compatibility"] == "kit-neutral-only"
    assert Result.metadata["vendor_loadable"] is False
    assert Result.metadata["native_self_contained"] is False
    assert OpenDoc(Output).assembly == DocValue.assembly
    Blocked = TmpPath / f"blocked{Source.suffix}"
    with Pytest.raises(AppUsabilityError):
        WriteDoc(DocValue, Blocked, allow_carrier=False)
    assert not Blocked.exists()


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Source", "WriteValues"),
    (
        (KCatparts / "Banjo.CATPart", {"rebuild": True}),
        (KCatproducts / "Tilton_Set.CATProduct", {}),
    ),
)
def TestGeneratedC(Source: Path, WriteValues: dict[str, bool], TmpPath: Path) -> None:
    Carrier = TmpPath / f"carrier{Source.suffix}"
    Result = WriteDoc(OpenDoc(Source), Carrier, allow_carrier=True, values=WriteValues)
    assert Result.metadata["mode"] == "generated_cfv2"
    Restored = OpenDoc(Carrier)
    SavedDoc = next(
        (
            Payload
            for Payload in Restored.brep_payloads
            if Payload.id.startswith("catia:preserved-native-document:")
        )
    )
    Token = SavedDoc.id.removeprefix("catia:preserved-native-document:")
    SavedBinding = next(
        (
            Payload
            for Payload in Restored.brep_payloads
            if Payload.id == f"catia:preserved-native-document-binding:{Token}"
        )
    )
    NativeData = Source.read_bytes()
    NativeDigest = Hashlib.sha256(NativeData).digest()
    assert SavedDoc.data == NativeData
    assert SavedDoc.sha256 == NativeDigest.hex()
    assert SavedBinding.data == NativeDigest
    assert SavedBinding.sha256 == Hashlib.sha256(NativeDigest).hexdigest()
    assert isinstance(SavedDoc.attributes["catia.replay_semantic_sha256"], str)
    Replay = TmpPath / f"replay{Source.suffix}"
    ReplayResult = Registry.write(
        Restored,
        Replay,
        options=WriteOptions(
            values={
                "portable": False,
                "allow_carrier": Source.suffix.casefold() == ".catproduct",
                "require_self_contained": Source.suffix.casefold() != ".catproduct",
            }
        ),
    )
    assert ReplayResult.metadata["mode"] == "exact_native_roundtrip"
    assert ReplayResult.requirements == (
        ("referenced CATIA component files",)
        if Source.suffix.casefold() == ".catproduct"
        else ()
    )
    assert Replay.read_bytes() == NativeData
    if Source.suffix.casefold() == ".catproduct":
        Regenerated = TmpPath / "regenerated.CATProduct"
        WriteDoc(Restored, Regenerated, allow_carrier=True)
        RegeneratedDoc = OpenDoc(Regenerated)
        assert tuple(
            (
                Payload
                for Payload in RegeneratedDoc.brep_payloads
                if Payload.id.startswith("catia:preserved-native-document")
            )
        ) == (SavedDoc, SavedBinding)


# this definition exists because focused behavior needs one stable owner
def TestStripped(TmpPath: Path) -> None:
    Original = OpenDoc(KCatparts / "Banjo.CATPart")
    Changed = Replace(
        Original, metadata=FrozenMapping({**Original.metadata, "audit_change": True})
    )
    Carrier = TmpPath / "carrier.CATPart"
    First = WriteDoc(Changed, Carrier, allow_carrier=True)
    assert First.vendor_loadable is False
    Restored = OpenDoc(Carrier)
    MetaValue = dict(Restored.metadata)
    assert (
        MetaValue.pop("catia.container_compatibility") == "native-base-neutral-overlay"
    )
    Stripped = Replace(Restored, metadata=FrozenMapping(MetaValue))
    Blocked = TmpPath / "blocked.CATPart"
    with Pytest.raises(AppUsabilityError) as Captured:
        WriteDoc(Stripped, Blocked, allow_carrier=False)
    assert Captured.value.vendor_loadable is False
    assert not Blocked.exists()
    Explicit = TmpPath / "explicit.CATPart"
    Result = WriteDoc(Stripped, Explicit, allow_carrier=True)
    assert Result.vendor_loadable is False
    assert Result.near_lossless is False
    assert Explicit.read_bytes() == Carrier.read_bytes()
    assert OpenDoc(Explicit).feature_timeline == Restored.feature_timeline


# native geometry payloads need focused validation against their declared source streams
def CheckCgmPayload(Archive, DocValue) -> None:
    NativeContainers = DocValue.brep_payloads[2:]
    assert [Payload.schema for Payload in NativeContainers] == [
        DeclValue.class_name for DeclValue in Archive.declarations()
    ]
    assert [Payload.source_stream for Payload in NativeContainers] == [
        DeclValue.stream_name for DeclValue in Archive.declarations()
    ]
    CgmDecl = next(
        (
            ItemValue
            for ItemValue in Archive.declarations()
            if ItemValue.class_name == "CGMGeom"
        )
    )
    CgmStream = Archive.outer.stream(CgmDecl.stream_name)
    assert CgmStream is not None
    CgmValue = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.id == "catia:native-cgm"
        )
    )
    assert CgmValue.data == Archive.stream_bytes(CgmStream)
    assert CgmValue.sha256 == Hashlib.sha256(CgmValue.data or b"").hexdigest()
    assert CgmValue.source_stream == CgmDecl.stream_name
    CgmMeta = next(
        (
            ItemValue
            for ItemValue in DocValue.metadata["catia.container_declarations"]
            if ItemValue["class_name"] == "CGMGeom"
        )
    )
    assert CgmMeta["sha256"] == CgmValue.sha256
    assert CgmMeta["logical_length"] == len(CgmValue.data or b"")


# parametric feature metadata needs isolation from native geometry payload checks
def CheckFeatData(DocValue) -> None:
    FeatureGraph = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.id == "catia:native-feature-graph"
        )
    )
    assert FeatureGraph.kind == "native_feature_graph"
    assert OsmxArchive.from_bytes(FeatureGraph.data or b"").version == "V5R28SP6HF0"
    assert [Plane.name for Plane in DocValue.support_planes] == [
        "xy-plane",
        "yz-plane",
        "zx-plane",
    ]
    assert DocValue.bodies[0].name == "Body.2"
    assert (
        DocValue.feature_timeline[0].attributes["native_payload_id"] == FeatureGraph.id
    )
    Definition = DocValue.feature_timeline[0].definition
    assert isinstance(Definition, NativeFeatureDefinition)
    assert Definition.format_id == "catia.v5.osmx"
    assert Definition.type_id == "CATPrtCont"
    assert Definition.object_data["symbols"] == DocValue.metadata["catia.part_symbols"]
    assert DocValue.capabilities == frozenset(
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


# filtered reads need a separate proof that role specific payload retention remains exact
def CheckFiltered(Source: FilePath) -> None:
    WithoutData = CatiaAdapter().read(
        Source, ReadOptions(include_brep=False, include_tessellation=False)
    )
    NativeDoc = next(
        (
            Payload
            for Payload in WithoutData.brep_payloads
            if Payload.kind == "native_document"
        )
    )
    assert NativeDoc.data is None
    assert {
        Payload.kind
        for Payload in WithoutData.brep_payloads
        if Payload.kind != "native_document"
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
        (
            Payload.data is None
            for Payload in WithoutData.brep_payloads
            if Payload.role
            in {PayloadRole.BREP, PayloadRole.TESSELLATION, PayloadRole.DOCUMENT}
        )
    )
    assert all(
        (
            Payload.data is not None
            for Payload in WithoutData.brep_payloads
            if Payload.role
            in {
                PayloadRole.FEATURE_HISTORY,
                PayloadRole.ASSEMBLY_STRUCTURE,
                PayloadRole.AUXILIARY,
            }
        )
    )
    assert Capability.BREP not in WithoutData.capabilities


# this definition exists because focused behavior needs one stable owner
def TestCatpartGeom() -> None:
    Source = KCatparts / "Banjo.CATPart"
    Archive = CfvTwoArchive.from_bytes(Source.read_bytes())
    DocValue = OpenDoc(Source)
    assert DocValue.source.format_id == "catia.v5"
    assert DocValue.source.application_version == "V5R28SP6HF0"
    assert DocValue.metadata["catia.document_type"] == "CATPart"
    CheckCgmPayload(Archive, DocValue)
    CheckFeatData(DocValue)
    CheckFiltered(Source)


# this definition exists because focused behavior needs one stable owner
def TestCatpart() -> None:
    Source = CfvTwoArchive.from_bytes((KCatparts / "Banjo.CATPart").read_bytes())
    Product = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATProdCont")
    )
    PartValue = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATPrtCont")
    )
    ProductStream = Source.outer.stream(Product.stream_name)
    PartStream = Source.outer.stream(PartValue.stream_name)
    assert ProductStream is not None
    assert PartStream is not None
    ProductStreamName = "1000_00000001_1"
    PartStreamName = "1000_00000002_2"
    CustomStreamName = "1000_00000003_3"
    CustomData = b"company-native-feature-container"
    Declarations = b"".join(
        (
            BuildDecl(Product.class_name, Product.base_class, ProductStreamName, 1),
            BuildDecl(PartValue.class_name, PartValue.base_class, PartStreamName, 2),
            BuildDecl("CompanyFeatureCont", "CATFeatCont", CustomStreamName, 3),
        )
    )
    Generated = BuildCfvTwo(
        (
            ("Format", b"CATPart"),
            ("Data", Declarations),
            (ProductStreamName, Source.stream_bytes(ProductStream)),
            (PartStreamName, Source.stream_bytes(PartStream)),
            (CustomStreamName, CustomData),
        )
    )
    DocValue = CatiaAdapter().read(Generated, ReadOptions(include_brep=False))
    Custom = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.schema == "CompanyFeatureCont"
        )
    )
    assert Custom.kind == "native_container"
    assert Custom.format_id == "catia.v5.cfv2.stream"
    assert Custom.role == PayloadRole.AUXILIARY
    assert Custom.file_extension == ".bin"
    assert Custom.data == CustomData
    ChangedData = b"changed-company-native-feature-container"
    Changed = Replace(
        Custom, data=ChangedData, sha256=Hashlib.sha256(ChangedData).hexdigest()
    )
    Modified = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                Changed if Payload.id == Custom.id else Payload
                for Payload in DocValue.brep_payloads
            )
        ),
    )
    Output = BytesIo()
    Result = CatiaAdapter().write(Modified, Output)
    assert Result.metadata["mode"] == "generated_cfv2"
    assert Output.getvalue() != Generated


# this definition exists because focused behavior needs one stable owner
def TestCatpartRoot() -> None:
    Source = CfvTwoArchive.from_bytes((KCatparts / "Banjo.CATPart").read_bytes())
    Product = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATProdCont")
    )
    PartValue = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATPrtCont")
    )
    ProductStream = Source.outer.stream(Product.stream_name)
    PartStream = Source.outer.stream(PartValue.stream_name)
    assert ProductStream is not None
    assert PartStream is not None
    ProductStreamName = "1000_00000001_1"
    PartStreamName = "1000_00000002_2"
    Declarations = b"".join(
        (
            BuildDecl("CompanyProductRoot", "CATFeatCont", ProductStreamName, 1),
            BuildDecl("CompanyPartRoot", "CompanyProductRoot", PartStreamName, 2),
        )
    )
    Generated = BuildCfvTwo(
        (
            ("Format", b"CATPart"),
            ("Data", Declarations),
            (ProductStreamName, Source.stream_bytes(ProductStream)),
            (PartStreamName, Source.stream_bytes(PartStream)),
        )
    )
    DocValue = CatiaAdapter().read(Generated)
    Payloads = {Payload.schema: Payload for Payload in DocValue.brep_payloads}
    assert Payloads["CompanyProductRoot"].role == PayloadRole.ASSEMBLY_STRUCTURE
    assert Payloads["CompanyPartRoot"].role == PayloadRole.FEATURE_HISTORY
    Definition = DocValue.feature_timeline[0].definition
    assert isinstance(Definition, NativeFeatureDefinition)
    assert Definition.type_id == "CompanyPartRoot"
    assert tuple(
        (Stream["class_name"] for Stream in DocValue.metadata["catia.osmx_streams"])
    ) == ("CompanyProductRoot", "CompanyPartRoot")
    assert "CATPrtCont" not in DocValue.diagnostics[-1].message
    assert DocValue.validate() == ()


# this definition exists because focused behavior needs one stable owner
def TestCatpartFrom() -> None:
    Source = CfvTwoArchive.from_bytes((KCatparts / "Banjo.CATPart").read_bytes())
    Product = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATProdCont")
    )
    PartValue = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATPrtCont")
    )
    CgmValue = next(
        (Value for Value in Source.declarations() if Value.class_name == "CGMGeom")
    )
    ProductStream = Source.outer.stream(Product.stream_name)
    PartStream = Source.outer.stream(PartValue.stream_name)
    CgmStream = Source.outer.stream(CgmValue.stream_name)
    assert ProductStream is not None
    assert PartStream is not None
    assert CgmStream is not None
    ProductStreamName = "1000_00000001_1"
    PartStreamName = "1000_00000002_2"
    RenamedCgmStreamName = "1000_00000003_3"
    MisleadingStreamName = "1000_00000004_4"
    Declarations = b"".join(
        (
            BuildDecl(Product.class_name, Product.base_class, ProductStreamName, 1),
            BuildDecl(PartValue.class_name, PartValue.base_class, PartStreamName, 2),
            BuildDecl(
                "CompanyGeometryContainer", "CATContainer", RenamedCgmStreamName, 3
            ),
            BuildDecl("CGMGeom", "CATContainer", MisleadingStreamName, 4),
        )
    )
    Generated = BuildCfvTwo(
        (
            ("Format", b"CATPart"),
            ("Data", Declarations),
            (ProductStreamName, Source.stream_bytes(ProductStream)),
            (PartStreamName, Source.stream_bytes(PartStream)),
            (RenamedCgmStreamName, Source.stream_bytes(CgmStream)),
            (MisleadingStreamName, b"opaque-company-payload"),
        )
    )
    DocValue = CatiaAdapter().read(Generated, ReadOptions(include_brep=False))
    RenamedCgm = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.schema == "CompanyGeometryContainer"
        )
    )
    Misleading = next(
        (Payload for Payload in DocValue.brep_payloads if Payload.schema == "CGMGeom")
    )
    assert RenamedCgm.role == PayloadRole.BREP
    assert RenamedCgm.format_id == "catia.cgm"
    assert RenamedCgm.data is None
    assert Misleading.role == PayloadRole.AUXILIARY
    assert Misleading.format_id == "catia.v5.cfv2.stream"
    assert Misleading.data == b"opaque-company-payload"


# this definition exists because focused behavior needs one stable owner
def TestCatpartC() -> None:
    Source = CfvTwoArchive.from_bytes((KCatparts / "Banjo.CATPart").read_bytes())
    Product = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATProdCont")
    )
    PartValue = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATPrtCont")
    )
    ProductStream = Source.outer.stream(Product.stream_name)
    PartStream = Source.outer.stream(PartValue.stream_name)
    assert ProductStream is not None
    assert PartStream is not None
    PartGraph = bytearray(Source.stream_bytes(PartStream))
    SymbolTableOffset = Struct.unpack_from("<I", PartGraph, 100)[0]
    FeatureType = b"CustomerDefinedFeature_99"
    PartGraph.extend(bytes((len(FeatureType) + 1,)) + FeatureType)
    Struct.pack_into(
        "<I", PartGraph, SymbolTableOffset + 2, len(PartGraph) - SymbolTableOffset
    )
    ProductStreamName = "1000_00000001_1"
    PartStreamName = "1000_00000002_2"
    Declarations = b"".join(
        (
            BuildDecl(Product.class_name, Product.base_class, ProductStreamName, 1),
            BuildDecl(PartValue.class_name, PartValue.base_class, PartStreamName, 2),
        )
    )
    Generated = BuildCfvTwo(
        (
            ("Format", b"CATPart"),
            ("Data", Declarations),
            (ProductStreamName, Source.stream_bytes(ProductStream)),
            (PartStreamName, bytes(PartGraph)),
        )
    )
    DocValue = CatiaAdapter().read(Generated, ReadOptions(include_brep=False))
    assert FeatureType.decode("ascii") in DocValue.metadata["catia.native_symbols"]
    assert (
        DocValue.feature_timeline[0].attributes["native_symbols"]
        == DocValue.metadata["catia.native_symbols"]
    )
    Definition = DocValue.feature_timeline[0].definition
    assert isinstance(Definition, NativeFeatureDefinition)
    assert FeatureType.decode("ascii") in Definition.object_data["symbols"]


# this definition exists because focused behavior needs one stable owner
def TestCatpartAre() -> None:
    Source = CfvTwoArchive.from_bytes((KCatparts / "Banjo.CATPart").read_bytes())
    Product = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATProdCont")
    )
    PartValue = next(
        (Value for Value in Source.declarations() if Value.class_name == "CATPrtCont")
    )
    ProductStream = Source.outer.stream(Product.stream_name)
    PartStream = Source.outer.stream(PartValue.stream_name)
    assert ProductStream is not None
    assert PartStream is not None
    PartData = bytearray(Source.stream_bytes(PartStream))
    Graph = OsmxArchive.from_bytes(PartData)
    PlaneTypeIndex = Graph.values.index("GSMPlane")
    AlgorithmIdIndex = Graph.values.index("_PartAlgoConfigUUID")
    Indices = (PlaneTypeIndex + 1, AlgorithmIdIndex - 2, AlgorithmIdIndex - 1)
    Names = ("PrimaryA", "PrimaryB", "PrimaryC")
    for SymbolIndex, NameValue in zip(Indices, Names, strict=True):
        Symbol = Graph.symbols[SymbolIndex]
        assert len(Symbol.value) == len(NameValue)
        PartData[Symbol.offset : Symbol.offset + len(NameValue)] = NameValue.encode(
            "ascii"
        )
    ProductStreamName = "1000_00000001_1"
    PartStreamName = "1000_00000002_2"
    Declarations = b"".join(
        (
            BuildDecl(Product.class_name, Product.base_class, ProductStreamName, 1),
            BuildDecl(PartValue.class_name, PartValue.base_class, PartStreamName, 2),
        )
    )
    Generated = BuildCfvTwo(
        (
            ("Format", b"CATPart"),
            ("Data", Declarations),
            (ProductStreamName, Source.stream_bytes(ProductStream)),
            (PartStreamName, bytes(PartData)),
        )
    )
    DocValue = CatiaAdapter().read(Generated)
    assert [Plane.name for Plane in DocValue.support_planes] == list(Names)
    assert [
        Plane.attributes["principal_index"] for Plane in DocValue.support_planes
    ] == [0, 1, 2]


# this definition exists because focused behavior needs one stable owner
def TestAdapterThe() -> None:
    assert CatiaAdapter().info.capabilities == frozenset(Capability)


# this definition exists because focused behavior needs one stable owner
def TestCatproduct() -> None:
    Source = KCatproducts / "Tilton_Set.CATProduct"
    Archive = CfvTwoArchive.from_bytes(Source.read_bytes())
    DocValue = OpenDoc(Source)
    assert DocValue.assembly is not None
    assert [Instance.name for Instance in DocValue.assembly.instances] == [
        "I_4876.2",
        "I_4876.3",
        "I_4784.5",
        "I_Brake_bias_90_degree_coupler.1",
    ]
    assert len(DocValue.assembly.definitions) == 5
    assert [Payload.schema for Payload in DocValue.brep_payloads[2:]] == [
        DeclValue.class_name for DeclValue in Archive.declarations()
    ]
    assert DocValue.capabilities == frozenset(
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
    assert Capability.BREP in DocValue.capabilities


# this definition exists because focused behavior needs one stable owner
def TestPedalBody() -> None:
    DocValue = OpenDoc(KCatparts / "Pedal_Body.CATPart")
    assert DocValue.metadata["catia.product_name"] == "Brake_pedal"
    assert DocValue.metadata["catia.internal_part_name"] == "Part2"
    assert DocValue.metadata["catia.body_name"] == "Brake_pedal"
    NativeSymbols = DocValue.metadata["catia.native_symbols"]
    assert NativeSymbols == tuple(
        dict.fromkeys(
            (Value for Value in DocValue.metadata["catia.part_symbols"] if Value)
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
    } <= set(NativeSymbols)
    assert DocValue.feature_timeline[0].attributes["native_symbols"] == NativeSymbols
    assert DocValue.feature_timeline[0].provenance is not None
    assert DocValue.bodies[0].provenance is not None


# this definition exists because focused behavior needs one stable owner
def TestCatpartCgr() -> None:
    Source = KCatparts / "Banjo.CATPart"
    Archive = CfvTwoArchive.from_bytes(Source.read_bytes())
    DocValue = CatiaAdapter().read(
        Source, ReadOptions(include_brep=False, include_tessellation=True)
    )
    Payload = next(
        (
            ItemValue
            for ItemValue in DocValue.brep_payloads
            if ItemValue.format_id == "catia.cgr"
        )
    )
    DeclValue = next(
        (
            ItemValue
            for ItemValue in Archive.declarations()
            if ItemValue.class_name == "CATCGRCont"
        )
    )
    Stream = Archive.outer.stream(DeclValue.stream_name)
    assert Stream is not None
    assert Payload.data == Archive.stream_bytes(Stream)
    assert Payload.schema == "CATCGRCont"
    assert Capability.TESSELLATION in DocValue.capabilities
    assert Capability.BREP not in DocValue.capabilities


# this definition exists because focused behavior needs one stable owner
def TestUnresolved(TmpPath: Path) -> None:
    Source = KCatparts / "Banjo.CATPart"
    Original = OpenDoc(Source)
    Output = TmpPath / "Banjo.FCStd"
    Result = Convert(Source, Output)
    Transfers = {Value.capability: Value for Value in Result.transfers}
    assert Result.application_usable is False
    assert Result.vendor_loadable is True
    assert Result.near_lossless is False
    for CapabilityValue in (Capability.BREP, Capability.TESSELLATION):
        assert Transfers[CapabilityValue].mode is TransferMode.CARRIER
        assert Transfers[CapabilityValue].carrier_reason is CarrierReason.SOURCE_OPAQUE
    with Zipfile.ZipFile(Output) as Archive:
        Names = Archive.namelist()
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        assert not any((NameValue.endswith(".Shape.brp") for NameValue in Names))
        assert not any((NameValue.endswith(".MeshKernel.bms") for NameValue in Names))
        assert not any(
            (
                Value.get("type") == "Mesh::Feature"
                for Value in RootValue.findall("./Objects/Object")
            )
        )
        assert not RootValue.findall(".//Part[@file]")
        assert not RootValue.findall(".//Mesh[@file]")
    assert OpenDoc(Output) == Original
    ReversedPart = TmpPath / "Banjo.CATPart"
    ReversedResult = Convert(Output, ReversedPart)
    assert ReversedResult.application_usable is True
    assert ReversedResult.vendor_loadable is True
    assert ReversedPart.read_bytes() == Source.read_bytes()


# generated carriers need their compatibility claims checked independently from restored content
def CheckKitMeta(Result) -> None:
    assert Result.destination_format == "catia.v5"
    assert Result.output.metadata["mode"] == "generated_cfv2"
    assert Result.output.metadata["compatibility"] == "kit-neutral-only"
    assert Result.output.metadata["vendor_loadable"] is False
    assert Result.output.metadata["native_geometry"] is False
    assert Result.output.metadata["native_history"] is False
    assert Result.output.metadata["native_assembly"] is False
    assert Result.output.metadata["native_self_contained"] is False
    assert Result.output.metadata["referenced_files_written"] == 0
    assert Result.output.metadata["native_feature_graph"] is False


# restored foreign content needs semantic equality checks separated from carrier metadata
def CheckSldRestore(Source, Restored) -> None:
    assert Restored.source.format_id == "catia.v5"
    assert (
        Restored.metadata["catia.embedded_source_format_id"] == Source.source.format_id
    )
    assert Restored.metadata["catia.embedded_source_path"] == Source.source.path
    assert Restored.metadata["catia.embedded_source_sha256"] == Source.source.sha256
    assert Restored.configurations == Source.configurations
    assert Restored.sketches == Source.sketches
    assert Restored.feature_timeline == Source.feature_timeline
    Retained = tuple(
        (
            Payload
            for Payload in Restored.brep_payloads
            if Payload.kind not in {"native_document", "native_document_binding"}
        )
    )
    assert Retained == Source.brep_payloads
    assert (
        sum(
            (
                Payload.kind == "native_document_binding"
                for Payload in Restored.brep_payloads
            )
        )
        == 1
    )
    assert (
        sum((Payload.kind == "native_document" for Payload in Restored.brep_payloads))
        == 1
    )


# this definition exists because focused behavior needs one stable owner
def TestSolidworksA(TmpPath: Path) -> None:
    Source = OpenDoc(KSldprt)
    Output = TmpPath / "example.CATPart"
    with Pytest.raises(AppUsabilityError):
        Convert(KSldprt, Output, allow_carrier=False)
    Result = Convert(KSldprt, Output, allow_carrier=True)
    CheckKitMeta(Result)
    Archive = CfvTwoArchive.from_bytes(Output.read_bytes())
    assert [Value.class_name for Value in Archive.declarations()] == [
        "CATProdCont",
        "CATPrtCont",
    ]
    assert any(
        (Folder.stream("KitInterchange") is not None for Folder in Archive.nested)
    )
    CheckSldRestore(Source, OpenDoc(Output))


# this definition exists because focused behavior needs one stable owner
def TestSolidworks(TmpPath: Path) -> None:
    Source = OpenDoc(KSldasm)
    Output = TmpPath / "Piston.CATProduct"
    Result = Convert(KSldasm, Output, allow_carrier=True)
    assert Result.source_format == "solidworks.sldasm"
    assert Result.destination_format == "catia.v5"
    Archive = CfvTwoArchive.from_bytes(Output.read_bytes())
    assert [Value.class_name for Value in Archive.declarations()] == ["CATProdCont"]
    Restored = OpenDoc(Output)
    assert Restored.source.format_id == "catia.v5"
    assert (
        Restored.metadata["catia.embedded_source_format_id"] == Source.source.format_id
    )
    assert Restored.assembly is not None
    assert Restored.assembly == Source.assembly
    assert len(Restored.assembly.mates) == 6


# this definition exists because focused behavior needs one stable owner
def TestEnforceDoc(TmpPath: Path) -> None:
    Adapter = CatiaAdapter()
    PartValue = OpenDoc(KSldprt)
    AsmValue = OpenDoc(KSldasm)
    assert Adapter.supports(PartValue, TmpPath / "part.CATPart")
    assert not Adapter.supports(PartValue, TmpPath / "part.CATProduct")
    assert Adapter.supports(AsmValue, TmpPath / "assembly.CATProduct")
    assert not Adapter.supports(AsmValue, TmpPath / "assembly.CATPart")
    assert Adapter.supports(PartValue, BytesIo())
    assert not Adapter.supports(PartValue, StringIo())
    with Pytest.raises(ValueError, match="\\.CATPart"):
        WriteCatia(PartValue, TmpPath / "part.CATProduct")
    with Pytest.raises(ValueError, match="\\.CATProduct"):
        WriteCatia(AsmValue, TmpPath / "assembly.CATPart")


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Source", "WrongSuffix"),
    (
        (KCatparts / "Banjo.CATPart", ".CATProduct"),
        (KCatproducts / "Tilton_Set.CATProduct", ".CATPart"),
    ),
)
def TestReaderKindA(Source: Path, WrongSuffix: str, TmpPath: Path) -> None:
    Renamed = TmpPath / f"renamed{WrongSuffix}"
    Renamed.write_bytes(Source.read_bytes())
    with Pytest.raises(CatiaAdapterError, match="content requires"):
        ReadCatia(Renamed)


# this definition exists because focused behavior needs one stable owner
def TestReaderKind(TmpPath: Path) -> None:
    Valid = TmpPath / "valid.CATPart"
    Convert(KSldprt, Valid, allow_carrier=True)
    Renamed = TmpPath / "renamed.CATProduct"
    Renamed.write_bytes(Valid.read_bytes())
    with Pytest.raises(CatiaAdapterError, match="content requires"):
        ReadCatia(Renamed)


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Marker", "WrongSuffix"),
    ((b"CATPart", ".CATProduct"), (b"CATProduct", ".CATPart")),
)
def TestReaderUses(Marker: bytes, WrongSuffix: str, TmpPath: Path) -> None:
    Renamed = TmpPath / f"declarationless{WrongSuffix}"
    Renamed.write_bytes(BuildCfvTwo((("Format", Marker),)))
    with Pytest.raises(CatiaAdapterError, match="content requires"):
        ReadCatia(Renamed)


# this definition exists because focused behavior needs one stable owner
def TestReaderPart() -> None:
    ProductStreamName = "1000_00000001_1"
    PartStreamName = "1000_00000002_2"
    Declarations = b"".join(
        (
            BuildDecl("CATProdCont", "CATFeatCont", ProductStreamName, 1),
            BuildDecl("CATPrtCont", "CATFeatCont", PartStreamName, 2),
        )
    )
    DataValue = BuildCfvTwo(
        (
            ("Format", b"CATPart"),
            ("Data", Declarations),
            (ProductStreamName, b"product-root"),
            (PartStreamName, b"part-root"),
        )
    )
    with Pytest.raises(CatiaAdapterError, match="contradictory document roots"):
        CatiaAdapter().read(DataValue)


# edited carriers need compatibility claims checked separately from archive byte retention
def CheckEditMeta(Result, Source: FilePath, Output: FilePath) -> None:
    assert Result.metadata["mode"] == "native_base_with_neutral_edits"
    assert Result.metadata["compatibility"] == "native-base-neutral-overlay"
    assert Result.metadata["vendor_loadable"] is False
    assert Result.metadata["native_geometry"] is False
    assert Result.metadata["native_history"] is False
    assert Result.metadata["native_base_vendor_loadable"] is True
    assert Result.metadata["native_base_preserved"] is True
    assert Result.metadata["native_streams_preserved"] is True
    assert Output.read_bytes() != Source.read_bytes()


# native streams must remain byte exact while the neutral overlay changes
def CheckStreamCopy(Source: FilePath, Output: FilePath):
    OriginalArchive = CfvTwoArchive.from_bytes(Source.read_bytes())
    OutputArchive = CfvTwoArchive.from_bytes(Output.read_bytes())
    assert tuple(
        (
            (Stream.name, OutputArchive.stream_bytes(Stream, OutputArchive.outer))
            for Stream in OutputArchive.outer.streams
            if Stream.name != "KitInterchange"
        )
    ) == tuple(
        (
            (Stream.name, OriginalArchive.stream_bytes(Stream, OriginalArchive.outer))
            for Stream in OriginalArchive.outer.streams
        )
    )
    return OutputArchive


# restored edits need semantic checks independent from physical archive preservation
def CheckEditState(Changed, Restored) -> None:
    assert Restored.source.format_id == "catia.v5"
    assert (
        Restored.metadata["catia.container_compatibility"]
        == "native-base-neutral-overlay"
    )
    assert Restored.configurations == Changed.configurations
    Retained = tuple(
        (
            Payload
            for Payload in Changed.brep_payloads
            if Payload.kind not in {"native_document", "native_document_binding"}
        )
    )
    RestoredRetained = tuple(
        (
            Payload
            for Payload in Restored.brep_payloads
            if Payload.kind not in {"native_document", "native_document_binding"}
        )
    )
    assert RestoredRetained == Retained
    assert (
        sum(
            (
                Payload.kind == "native_document_binding"
                for Payload in Restored.brep_payloads
            )
        )
        == 2
    )
    assert (
        sum((Payload.kind == "native_document" for Payload in Restored.brep_payloads))
        == 2
    )
    Saved = next(
        (
            Payload
            for Payload in Restored.brep_payloads
            if Payload.id.startswith("catia:preserved-native-document:")
        )
    )
    assert "catia.replay_semantic_sha256" not in Saved.attributes


# exact carrier replay needs proof separate from edited model restoration
def CheckEditReplay(TmpPath: FilePath, Output: FilePath, Restored) -> None:
    Replay = TmpPath / "ChangedReplay.CATPart"
    ReplayResult = WriteDoc(Restored, Replay, allow_carrier=True)
    assert ReplayResult.metadata["mode"] == "exact_carrier_roundtrip"
    assert ReplayResult.metadata["compatibility"] == "native-base-neutral-overlay"
    assert Replay.read_bytes() == Output.read_bytes()


# archive tampering needs an isolated proof that native compatibility is revoked
def CheckTampered(Output: FilePath, OutputArchive) -> None:
    Tampered = bytearray(Output.read_bytes())
    Tolerance = OutputArchive.outer.stream("GesToler")
    assert Tolerance is not None
    assert len(Tolerance.extents) == 1
    Tampered[Tolerance.extents[0].physical_offset + 10] ^= 1
    TamperedDoc = ReadCatia(bytes(Tampered))
    assert TamperedDoc.metadata["catia.container_compatibility"] == "kit-neutral-only"


# this definition exists because focused behavior needs one stable owner
def TestModifiedDoc(TmpPath: Path) -> None:
    Source = KCatparts / "Banjo.CATPart"
    DocValue = OpenDoc(Source)
    Changed = Replace(
        DocValue, configurations=(Config("catia:changed", "Changed", active=True),)
    )
    Output = TmpPath / "Changed.CATPart"
    Result = WriteDoc(Changed, Output, allow_carrier=True)
    CheckEditMeta(Result, Source, Output)
    OutputArchive = CheckStreamCopy(Source, Output)
    Restored = OpenDoc(Output)
    CheckEditState(Changed, Restored)
    CheckEditReplay(TmpPath, Output, Restored)
    CheckTampered(Output, OutputArchive)


# this definition exists because focused behavior needs one stable owner
def TestEmbeddedAnd(TmpPath: Path) -> None:
    Source = OpenDoc(KSldprt)
    Output = TmpPath / "Filtered.CATPart"
    Convert(KSldprt, Output, allow_carrier=True)
    Config = Source.configurations[0]
    Filtered = CatiaAdapter().read(
        Output, ReadOptions(configuration=Config.id, include_brep=False)
    )
    assert Filtered.source.format_id == "catia.v5"
    assert Filtered.metadata["catia.embedded_source_format_id"] == "solidworks.sldprt"
    assert all(
        (
            Payload.data is None
            for Payload in Filtered.brep_payloads
            if Payload.role in {PayloadRole.BREP, PayloadRole.DOCUMENT}
        )
    )
    Binding = next(
        (
            Payload
            for Payload in Filtered.brep_payloads
            if Payload.kind == "native_document_binding"
        )
    )
    assert Binding.role == PayloadRole.VERIFICATION
    assert Binding.data is None
    assert Capability.BREP not in Filtered.capabilities
    assert Capability.NATIVE_PAYLOADS in Filtered.capabilities
    assert Capability.TESSELLATION not in Filtered.capabilities
    assert Filtered.capabilities == Source.capabilities - {Capability.BREP}
    assert [
        ItemValue.id for ItemValue in Filtered.configurations if ItemValue.active
    ] == [Config.id]
    Complete = OpenDoc(Output)
    Replay = TmpPath / "Replay.CATPart"
    Result = WriteCatia(Complete, Replay)
    assert Result.metadata["mode"] == "exact_carrier_roundtrip"
    assert Replay.read_bytes() == Output.read_bytes()


# this definition exists because focused behavior needs one stable owner
def TestGeneratedB() -> None:
    Source = DocValue()
    Output = BytesIo()
    WriteCatia(Source, Output, allow_non_native=True)
    Restored = CatiaAdapter().read(Output.getvalue())
    assert Restored.capabilities == Source.capabilities


# this definition exists because focused behavior needs one stable owner
def TestEmbeddedDoc(TmpPath: Path) -> None:
    Source = OpenDoc(KSldprt)
    ForeignDoc = BrepPayload(
        "future:document",
        "future.cad",
        "native_document",
        "future",
        Hashlib.sha256(b"foreign-document").hexdigest(),
        data=b"foreign-document",
        role=PayloadRole.DOCUMENT,
        file_extension=".future",
    )
    UnknownAuxiliary = BrepPayload(
        "future:declaration",
        "catia.v5.cfv2.stream",
        "native_container",
        "CustomerContainer",
        Hashlib.sha256(b"customer-container").hexdigest(),
        data=b"customer-container",
        role=PayloadRole.AUXILIARY,
        file_extension=".bin",
    )
    Carried = Replace(
        Source, brep_payloads=(*Source.brep_payloads, ForeignDoc, UnknownAuxiliary)
    )
    Output = TmpPath / "ForeignPayloads.CATPart"
    WriteCatia(Carried, Output, allow_non_native=True)
    Restored = CatiaAdapter().read(Output, ReadOptions(include_brep=False))
    ByIdValue = {Payload.id: Payload for Payload in Restored.brep_payloads}
    assert ByIdValue[ForeignDoc.id] == ForeignDoc
    assert ByIdValue[UnknownAuxiliary.id] == UnknownAuxiliary
    assert all(
        (
            Payload.data is None
            for Payload in Restored.brep_payloads
            if Payload.role == PayloadRole.BREP
        )
    )


# this definition exists because focused behavior needs one stable owner
def TestEmbedded(TmpPath: Path) -> None:
    Output = TmpPath / "Configured.CATPart"
    Convert(KSldprt, Output, allow_carrier=True)
    with Pytest.raises(CatiaAdapterError, match="configuration"):
        CatiaAdapter().read(Output, ReadOptions(configuration="missing-configuration"))


# this definition exists because focused behavior needs one stable owner
def TestCatpartA() -> None:
    with Pytest.raises(CatiaAdapterError, match="configuration"):
        CatiaAdapter().read(
            KCatparts / "Banjo.CATPart",
            ReadOptions(configuration="missing-configuration"),
        )


# this definition exists because focused behavior needs one stable owner
def TestConversion(TmpPath: Path) -> None:
    Catpart = TmpPath / "Reader.CATPart"
    Output = TmpPath / "Reader.json"
    Convert(KSldprt, Catpart, allow_carrier=True)
    Result = Convert(Catpart, Output)
    assert Result.source_format == "catia.v5"
    assert Result.document.source.format_id == "catia.v5"
    assert (
        Result.document.metadata["catia.embedded_source_format_id"]
        == "solidworks.sldprt"
    )


# this definition exists because focused behavior needs one stable owner
def TestChangedCgm(TmpPath: Path) -> None:
    DocValue = OpenDoc(KCatparts / "Banjo.CATPart")
    CgmValue = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.id == "catia:native-cgm"
        )
    )
    Changed = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                (
                    Replace(Payload, data=(CgmValue.data or b"") + b"\x00")
                    if Payload.id == CgmValue.id
                    else Payload
                )
                for Payload in DocValue.brep_payloads
            )
        ),
    )
    Output = TmpPath / "ChangedGeometry.CATPart"
    Result = WriteCatia(Changed, Output, allow_non_native=True)
    assert Result.metadata["mode"] == "native_base_with_neutral_edits"
    assert Result.metadata["native_base_preserved"] is True
    assert Result.metadata["native_geometry"] is False


# this definition exists because focused behavior needs one stable owner
def TestRecomputed() -> None:
    DocValue = OpenDoc(KCatparts / "Banjo.CATPart")
    Feature = DocValue.feature_timeline[0]
    Changed = Replace(
        DocValue, feature_timeline=(Replace(Feature, name="Forged CATIA feature"),)
    )
    Changed = Replace(
        Changed,
        metadata=FrozenMapping(
            {**Changed.metadata, "catia.roundtrip_sha256": SemanticDigest(Changed)}
        ),
    )
    Output = BytesIo()
    Result = WriteCatia(Changed, Output, allow_non_native=True)
    assert Result.metadata["mode"] == "native_base_with_neutral_edits"
    assert Result.application_usable is False
    assert Result.vendor_loadable is False
    assert (
        ReadCatia(Output.getvalue()).feature_timeline[0].name == "Forged CATIA feature"
    )


# this definition exists because focused behavior needs one stable owner
def TestSwappedDoc() -> None:
    DocValue = OpenDoc(KCatparts / "Banjo.CATPart")
    Replacement = (KCatparts / "Bolt_M5x40.CATPart").read_bytes()
    Changed = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                (
                    Replace(
                        Payload,
                        data=Replacement,
                        sha256=Hashlib.sha256(Replacement).hexdigest(),
                    )
                    if Payload.kind == "native_document"
                    else Payload
                )
                for Payload in DocValue.brep_payloads
            )
        ),
    )
    Output = BytesIo()
    Result = WriteCatia(Changed, Output, allow_non_native=True)
    assert Result.metadata["mode"] == "generated_cfv2"
    assert Output.getvalue() != Replacement


# this definition exists because focused behavior needs one stable owner
def TestMutated() -> None:
    Source = KCatproducts / "Tilton_Set.CATProduct"
    DocValue = OpenDoc(Source)
    Mutated = bytearray(Source.read_bytes())
    Archive = CfvTwoArchive.from_bytes(Mutated)
    DataStream = Archive.outer.stream("Data")
    assert DataStream is not None
    assert len(DataStream.extents) == 1
    Mutated[DataStream.extents[0].physical_offset + 100] ^= 1
    Native = bytes(Mutated)
    Changed = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                (
                    Replace(
                        Payload, data=Native, sha256=Hashlib.sha256(Native).hexdigest()
                    )
                    if Payload.kind == "native_document"
                    else Payload
                )
                for Payload in DocValue.brep_payloads
            )
        ),
    )
    Output = BytesIo()
    Result = WriteCatia(Changed, Output, allow_non_native=True)
    assert Result.metadata["mode"] == "generated_cfv2"
    assert Output.getvalue() != Native


# this definition exists because focused behavior needs one stable owner
def TestGeneratedA() -> None:
    Source = OpenDoc(KSldprt)
    Carrier = BytesIo()
    WriteCatia(Source, Carrier, allow_non_native=True)
    CarrierData = Carrier.getvalue()
    DocValue = CatiaAdapter().read(CarrierData)
    Unchanged = BytesIo()
    Result = WriteCatia(DocValue, Unchanged)
    assert Result.metadata["mode"] == "exact_carrier_roundtrip"
    assert Result.metadata["compatibility"] == "kit-neutral-only"
    assert Result.metadata["vendor_loadable"] is False
    assert Unchanged.getvalue() == CarrierData
    Mutated = bytearray(CarrierData)
    Archive = CfvTwoArchive.from_bytes(Mutated)
    Summary = Archive.outer.stream("CATSummaryInformation")
    assert Summary is not None
    assert len(Summary.extents) == 1
    Mutated[Summary.extents[0].physical_offset + 10] ^= 1
    Native = bytes(Mutated)
    Changed = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                (
                    Replace(
                        Payload, data=Native, sha256=Hashlib.sha256(Native).hexdigest()
                    )
                    if Payload.kind == "native_document"
                    else Payload
                )
                for Payload in DocValue.brep_payloads
            )
        ),
    )
    Rebuilt = BytesIo()
    Result = WriteCatia(Changed, Rebuilt, allow_non_native=True)
    assert Result.metadata["mode"] == "generated_cfv2"
    assert Rebuilt.getvalue() != Native


# this definition exists because focused behavior needs one stable owner
def TestGenerated() -> None:
    Source = OpenDoc(KSldprt)
    Carrier = BytesIo()
    WriteCatia(Source, Carrier, allow_non_native=True)
    CarrierData = Carrier.getvalue()
    DocValue = CatiaAdapter().read(CarrierData)
    Mutated = bytearray(CarrierData)
    Archive = CfvTwoArchive.from_bytes(Mutated)
    Summary = Archive.outer.stream("CATSummaryInformation")
    assert Summary is not None
    assert len(Summary.extents) == 1
    Mutated[Summary.extents[0].physical_offset + 10] ^= 1
    Native = bytes(Mutated)
    NativeDigest = Hashlib.sha256(Native).digest()
    Changed = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                (
                    Replace(
                        Payload, data=Native, sha256=Hashlib.sha256(Native).hexdigest()
                    )
                    if Payload.kind == "native_document"
                    else (
                        Replace(
                            Payload,
                            data=NativeDigest,
                            sha256=Hashlib.sha256(NativeDigest).hexdigest(),
                        )
                        if Payload.kind == "native_document_binding"
                        else Payload
                    )
                )
                for Payload in DocValue.brep_payloads
            )
        ),
    )
    Rebuilt = BytesIo()
    Result = WriteCatia(Changed, Rebuilt, allow_non_native=True)
    assert Result.metadata["mode"] == "generated_cfv2"
    assert Rebuilt.getvalue() != Native


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("Change", ("capabilities", "metadata", "diagnostics"))
def TestGeneratedD(Change: str) -> None:
    Source = OpenDoc(KSldprt)
    Carrier = BytesIo()
    WriteCatia(Source, Carrier, allow_non_native=True)
    DocValue = CatiaAdapter().read(Carrier.getvalue())
    if Change == "capabilities":
        Changed = Replace(
            DocValue, capabilities=DocValue.capabilities | {Capability.MATERIALS}
        )
    elif Change == "metadata":
        Changed = Replace(
            DocValue,
            metadata=FrozenMapping({**DocValue.metadata, "user.tag": "changed"}),
        )
    else:
        Changed = Replace(
            DocValue,
            diagnostics=(
                *DocValue.diagnostics,
                DiagValue("user.changed", "changed", Severity.INFO),
            ),
        )
    Rebuilt = BytesIo()
    Result = WriteCatia(Changed, Rebuilt, allow_non_native=True)
    assert Result.metadata["mode"] == "generated_cfv2"
    Restored = CatiaAdapter().read(Rebuilt.getvalue())
    if Change == "capabilities":
        assert Capability.MATERIALS in Restored.capabilities
    elif Change == "metadata":
        assert Restored.metadata["user.tag"] == "changed"
    else:
        assert Restored.diagnostics[-1].code == "user.changed"


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("RoleValue", (PayloadRole.DOCUMENT, PayloadRole.VERIFICATION))
def TestForeignRole(RoleValue: PayloadRole) -> None:
    Source = OpenDoc(KSldprt)
    PayloadData = b"foreign-payload"
    Foreign = BrepPayload(
        f"foreign:{RoleValue.value}",
        "future.cad",
        "foreign_payload",
        "1",
        Hashlib.sha256(PayloadData).hexdigest(),
        data=PayloadData,
        role=RoleValue,
        file_extension=".bin",
    )
    Carried = Replace(Source, brep_payloads=(*Source.brep_payloads, Foreign))
    Carrier = BytesIo()
    WriteCatia(Carried, Carrier, allow_non_native=True)
    DocValue = CatiaAdapter().read(Carrier.getvalue())
    ChangedData = b"changed-foreign-payload"
    Changed = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                (
                    Replace(
                        Payload,
                        data=ChangedData,
                        sha256=Hashlib.sha256(ChangedData).hexdigest(),
                    )
                    if Payload.id == Foreign.id
                    else Payload
                )
                for Payload in DocValue.brep_payloads
            )
        ),
    )
    Rebuilt = BytesIo()
    Result = WriteCatia(Changed, Rebuilt, allow_non_native=True)
    assert Result.metadata["mode"] == "generated_cfv2"


# this definition exists because focused behavior needs one stable owner
def TestLegacyDocIs() -> None:
    Source = OpenDoc(KSldprt)
    LegacyData = b"x" * Hashlib.sha256().digest_size
    Legacy = BrepPayload(
        "catia:native-document-binding",
        "catia.v5.sha256",
        "native_document_binding",
        "sha256",
        Hashlib.sha256(LegacyData).hexdigest(),
        data=LegacyData,
        role=PayloadRole.DOCUMENT,
        file_extension=".sha256",
    )
    Carried = Replace(Source, brep_payloads=(*Source.brep_payloads, Legacy))
    Carrier = BytesIo()
    WriteCatia(Carried, Carrier, allow_non_native=True)
    Restored = CatiaAdapter().read(Carrier.getvalue())
    Bindings = tuple(
        (
            Payload
            for Payload in Restored.brep_payloads
            if Payload.kind == "native_document_binding"
        )
    )
    assert len(Bindings) == 1
    assert Bindings[0].role == PayloadRole.VERIFICATION


# this definition exists because focused behavior needs one stable owner
def TestForeign() -> None:
    Source = OpenDoc(KSldprt)
    PayloadData = b"foreign-payload"
    Foreign = BrepPayload(
        "foreign:auxiliary",
        "future.cad",
        "foreign_payload",
        "1",
        Hashlib.sha256(PayloadData).hexdigest(),
        data=PayloadData,
        role=PayloadRole.AUXILIARY,
        file_extension=".bin",
    )
    Carried = Replace(Source, brep_payloads=(*Source.brep_payloads, Foreign))
    Carrier = BytesIo()
    WriteCatia(Carried, Carrier, allow_non_native=True)
    DocValue = CatiaAdapter().read(Carrier.getvalue())
    Changed = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                (
                    Replace(
                        Payload,
                        source_stream="changed",
                        provenance=Provenance("future.cad", "changed"),
                        attributes=FrozenMapping({"user.tag": "changed"}),
                    )
                    if Payload.id == Foreign.id
                    else Payload
                )
                for Payload in DocValue.brep_payloads
            )
        ),
    )
    Rebuilt = BytesIo()
    Result = WriteCatia(Changed, Rebuilt, allow_non_native=True)
    assert Result.metadata["mode"] == "generated_cfv2"
    Restored = CatiaAdapter().read(Rebuilt.getvalue())
    Payload = next(
        (
            ItemValue
            for ItemValue in Restored.brep_payloads
            if ItemValue.id == Foreign.id
        )
    )
    assert Payload.source_stream == "changed"
    assert Payload.provenance == Provenance("future.cad", "changed")
    assert Payload.attributes == {"user.tag": "changed"}


# this definition exists because focused behavior needs one stable owner
def TestCatpartB(TmpPath: Path) -> None:
    SourcePath = KCatparts / "Banjo.CATPart"
    Source = OpenDoc(SourcePath)
    Carrier = TmpPath / "Banjo.SLDPRT"
    Output = TmpPath / "Banjo.CATPart"
    WriteSldprt(Source, Carrier, allow_non_native=True)
    Restored = ReadSldprt(Carrier)
    Result = WriteCatia(Restored, Output)
    assert Result.metadata["mode"] == "exact_native_roundtrip"
    assert Output.read_bytes() == SourcePath.read_bytes()


# this definition exists because focused behavior needs one stable owner
def TestEngineAlias(TmpPath: Path) -> None:
    Output = TmpPath / "Piston.SLDASM"
    Result = Convert(KSldasm, Output)
    assert Result.source_format == "solidworks.sldasm"
    assert Result.destination_format == "solidworks.sldasm"
    assert Result.output.adapter == "solidworks.sldasm"
    assert Result.requirements == ()


# this definition exists because focused behavior needs one stable owner
def TestCfvTwoOuter() -> None:
    DataValue = bytearray((KCatparts / "Banjo.CATPart").read_bytes())
    DataValue[15] ^= 1
    with Pytest.raises(CfvTwoFormatError):
        CfvTwoArchive.from_bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
def TestCfvTwo() -> None:
    DataValue = bytearray((KCatparts / "Banjo.CATPart").read_bytes())
    Archive = CfvTwoArchive.from_bytes(DataValue)
    Stream = Archive.outer.stream("Data")
    assert Stream is not None
    Struct.pack_into(
        ">I", DataValue, Stream.descriptor_offset + 84, Archive.outer.offset
    )
    with Pytest.raises(CfvTwoFormatError, match="payload region"):
        CfvTwoArchive.from_bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
def TestCfvTwoA() -> None:
    DataValue = bytearray((KCatparts / "Banjo.CATPart").read_bytes())
    Archive = CfvTwoArchive.from_bytes(DataValue)
    First = Archive.outer.stream("Format")
    Second = Archive.outer.stream("GesToler")
    assert First is not None
    assert Second is not None
    Struct.pack_into(
        ">I", DataValue, Second.descriptor_offset + 84, First.extents[0].physical_offset
    )
    with Pytest.raises(CfvTwoFormatError, match="overlap"):
        CfvTwoArchive.from_bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
def TestCfvTwoB() -> None:
    DataValue = bytearray((KCatparts / "Banjo.CATPart").read_bytes())
    Archive = CfvTwoArchive.from_bytes(DataValue)
    Preview = Archive.outer.stream("CATPreview")
    assert Preview is not None
    assert len(Preview.extents) == 1
    Injected = BuildCfvTwo((("Injected", b"value"),))
    assert len(Injected) < Preview.logical_length
    Start = Preview.extents[0].physical_offset
    DataValue[Start : Start + len(Injected)] = Injected
    with Pytest.raises(CfvTwoFormatError, match="owning stream"):
        CfvTwoArchive.from_bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
def TestCfvTwoMagic() -> None:
    DataValue = bytearray((KCatparts / "Banjo.CATPart").read_bytes())
    Archive = CfvTwoArchive.from_bytes(DataValue)
    Preview = Archive.outer.stream("CATPreview")
    assert Preview is not None
    assert len(Preview.extents) == 1
    Injected = BuildCfvTwo((("Injected", b"value"),))
    Start = Preview.extents[0].physical_offset + 32
    assert (
        Start + len(Injected)
        < Preview.extents[0].physical_offset + Preview.logical_length
    )
    DataValue[Start : Start + len(Injected)] = Injected
    Restored = CfvTwoArchive.from_bytes(DataValue)
    assert len(Restored.nested) == 1


# this definition exists because focused behavior needs one stable owner
def TestOsmxRejects() -> None:
    Symbols = b"\x02A" * 65550
    Section = b"|\x02" + Struct.pack("<I", 6 + len(Symbols)) + Symbols
    DataValue = bytearray(104)
    DataValue[:4] = b"OSMX"
    Struct.pack_into("<I", DataValue, 100, 104)
    DataValue.extend(Section)
    with Pytest.raises(OsmxFormatError, match="safety limit"):
        OsmxArchive.from_bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Manifest", "Message"),
    (
        (
            b"KITCFV2\x01"
            + Struct.pack(">Q", 1 << 63)
            + bytes(32)
            + ZlibValue.compress(b""),
            "size limit",
        ),
        (
            b"KITCFV2\x01"
            + Struct.pack(">Q", 1)
            + Hashlib.sha256(b"ab").digest()
            + ZlibValue.compress(b"ab"),
            "declared length",
        ),
        (
            b"KITCFV2\x01"
            + Struct.pack(">Q", 2)
            + Hashlib.sha256(b"{}").digest()
            + ZlibValue.compress(b"{}")
            + b"trailing",
            "trailing compressed data",
        ),
    ),
)
def TestManifestIs(Manifest: bytes, Message: str) -> None:
    DataValue = BuildCfvTwo((("KitInterchange", Manifest),))
    with Pytest.raises(CatiaAdapterError, match=Message):
        CatiaAdapter().read(DataValue)


# this definition exists because focused behavior needs one stable owner
def TestDuplicate() -> None:
    Nested = BuildCfvTwo(
        (
            ("KitInterchange", b"short"),
            ("OtherManifestX", b"a different and longer manifest"),
        )
    )
    DataValue = bytearray(BuildCfvTwo((("NestedContainer", Nested),)))
    Archive = CfvTwoArchive.from_bytes(DataValue)
    Folder = Archive.nested[0]
    Renamed = Folder.stream("OtherManifestX")
    assert Renamed is not None
    Encoded = "KitInterchange".encode("utf-16le")
    Start = Renamed.descriptor_offset + 16
    DataValue[Start : Start + len(Encoded)] = Encoded
    Reproduced = CfvTwoArchive.from_bytes(DataValue)
    assert (
        sum(
            (Stream.name == "KitInterchange" for Stream in Reproduced.nested[0].streams)
        )
        == 2
    )
    Result = CatiaAdapter().probe(DataValue)
    assert Result.confidence == 0.0
    assert "multiple CATIA Kit manifests" in Result.reason
    with Pytest.raises(CfvTwoFormatError, match="multiple CATIA Kit manifests"):
        CatiaAdapter().read(DataValue)


# this definition exists because focused behavior needs one stable owner
def TestDeepIsLeak() -> None:
    RawValue = ("[" * 2000 + "0" + "]" * 2000).encode("utf-8")
    DataValue = BuildCfvTwo((("KitInterchange", PackedManifest(RawValue)),))
    Result = CatiaAdapter().probe(DataValue)
    assert Result.confidence == 0.0
    assert "JSON nesting exceeds the depth limit" in Result.reason
    with Pytest.raises(CatiaAdapterError, match="JSON nesting exceeds the depth limit"):
        CatiaAdapter().read(DataValue)


# this definition exists because focused behavior needs one stable owner
def TestShallowIsBy() -> None:
    DataValue = BuildCfvTwo((("KitInterchange", PackedManifest(b"not-json")),))
    Result = CatiaAdapter().probe(DataValue)
    assert Result.confidence == 0.0
    assert "invalid Kit document" in Result.reason
    with Pytest.raises(CatiaAdapterError, match="invalid Kit document"):
        CatiaAdapter().read(DataValue)


# this binding exists because shared behavior needs one stable value
globals()["ApplicationUsabilityError"] = AppUsabilityError

# this binding exists because shared behavior needs one stable value
globals()["BytesIO"] = BytesIo

# this binding exists because shared behavior needs one stable value
globals()["CATPARTS"] = KCatparts

# this binding exists because shared behavior needs one stable value
globals()["CATPRODUCTS"] = KCatproducts

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Archive"] = CfvTwoArchive

# this binding exists because shared behavior needs one stable value
globals()["Cfv2FormatError"] = CfvTwoFormatError

# this binding exists because shared behavior needs one stable value
globals()["Configuration"] = Config

# this binding exists because shared behavior needs one stable value
globals()["DOCUMENT_TYPE_BY_SUFFIX"] = DocTypeBySuffix

# this binding exists because shared behavior needs one stable value
globals()["Diagnostic"] = DiagValue

# this binding exists because shared behavior needs one stable value
globals()["ET"] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()["INFO"] = InfoValue

# this binding exists because shared behavior needs one stable value
globals()["PART_DOCUMENT_TYPE"] = PartDocType

# this binding exists because shared behavior needs one stable value
globals()["PRODUCT_DOCUMENT_TYPE"] = ProductDocType

# this binding exists because shared behavior needs one stable value
globals()["Path"] = FilePath

# this binding exists because shared behavior needs one stable value
globals()["ROOT"] = KRootValue

# this binding exists because shared behavior needs one stable value
globals()["SLDASM"] = KSldasm

# this binding exists because shared behavior needs one stable value
globals()["SLDPRT"] = KSldprt

# this binding exists because shared behavior needs one stable value
globals()["SUFFIX_BY_DOCUMENT_TYPE"] = SuffixByDocType

# this binding exists because shared behavior needs one stable value
globals()["StringIO"] = StringIo

# this binding exists because shared behavior needs one stable value
globals()["_opencascade_payload"] = Opencascade

# this binding exists because shared behavior needs one stable value
globals()["_packed_manifest"] = PackedManifest

# this binding exists because shared behavior needs one stable value
globals()["_parasolid_payload"] = Parasolid

# this binding exists because shared behavior needs one stable value
globals()["_semantic_digest"] = SemanticDigest

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["append_cfv2_stream"] = AppendCfvTwoStream

# this binding exists because shared behavior needs one stable value
globals()["brep_model_brep"] = BrepModelBrep

# this binding exists because shared behavior needs one stable value
globals()["build_cfv2"] = BuildCfvTwo

# this binding exists because shared behavior needs one stable value
globals()["build_declaration"] = BuildDecl

# this binding exists because shared behavior needs one stable value
globals()["convert"] = Convert

# this binding exists because shared behavior needs one stable value
globals()["document"] = DocValue

# this binding exists because shared behavior needs one stable value
globals()["encode_brep_model"] = EncodeBrepModel

# this binding exists because shared behavior needs one stable value
globals()["frozen_mapping"] = FrozenMapping

# this binding exists because shared behavior needs one stable value
globals()["hashlib"] = Hashlib

# this binding exists because shared behavior needs one stable value
globals()["json"] = JsonValue

# this binding exists because shared behavior needs one stable value
globals()["open_document"] = OpenDoc

# this binding exists because shared behavior needs one stable value
globals()["pytest"] = Pytest

# this binding exists because shared behavior needs one stable value
globals()["read_catia"] = ReadCatia

# this binding exists because shared behavior needs one stable value
globals()["read_sldprt"] = ReadSldprt

# this binding exists because shared behavior needs one stable value
globals()["registry"] = Registry

# this binding exists because shared behavior needs one stable value
globals()["replace"] = Replace

# this binding exists because shared behavior needs one stable value
globals()["struct"] = Struct

# this binding exists because shared behavior needs one stable value
globals()["triangle_brep"] = TriangleBrep

# this binding exists because shared behavior needs one stable value
globals()["write_catia"] = WriteCatia

# this binding exists because shared behavior needs one stable value
globals()["write_document"] = WriteDoc

# this binding exists because shared behavior needs one stable value
globals()["write_sldprt"] = WriteSldprt

# this binding exists because shared behavior needs one stable value
globals()["zipfile"] = Zipfile

# this binding exists because shared behavior needs one stable value
globals()["zlib"] = ZlibValue
