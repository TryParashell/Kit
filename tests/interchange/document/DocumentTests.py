# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import is_dataclass as IsDataClass
from dataclasses import replace as ReplaceValue
from enum import Enum as EnumBase
import hashlib as HashCodec
from importlib import import_module as ImportModule
import os as OsSystem
from pathlib import Path as FilePath
import subprocess as Subprocess
import sys as System
import pytest as PytestLib
from interchange import (
    AssemblyData,
    DesignBody,
    BrepPayload,
    CadDocument,
    Diagnostic,
    DocumentError,
    CadSource,
    Capability,
    ComponentDef,
    ComponentInst,
    ComponentKind,
    FeatureKind,
    FeatureStep,
    PayloadRole,
    FilterDocument,
    InferCaps,
)
from interchange.payloads.PayloadMigrate import GetLegacyFields
from interchange.payloads.PayloadRules import KLegacyPayloadRules
from interchange.serialization import FromData, KTypeRegistry, RegisterTypes, ToData
from tests.interchange.fixtures.DocumentFixture import (
    BuildDocument as BuildFixtureDocument,
)

# dynamic package loading lets reflection inspect the facade without mixed import forms
KInterchangeApi = ImportModule("interchange")


# behavior coverage protects portable interchange semantics during structural refactors
def BuildDocument() -> CadDocument:
    return BuildFixtureDocument()


# historical imports keep conversion suites independent from helper renaming
def __getattr__(NameText: str) -> object:
    if NameText == "document":
        return BuildDocument
    raise AttributeError(f"module {__name__!r} has no attribute {NameText!r}")


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRoundtrip() -> None:
    SourceValue = BuildDocument()
    RestoredValue = CadDocument.FromJson(SourceValue.ToJson())
    assert RestoredValue == SourceValue
    assert isinstance(RestoredValue.Capabilities, frozenset)
    assert isinstance(RestoredValue.FeatureTimeline, tuple)


# behavior coverage protects portable interchange semantics during structural refactors
def CheckStableJson() -> None:
    PayloadValue = BuildDocument().ToJson(IndentSize=None)
    SourceRoot = FilePath(__file__).parents[3] / "src"
    ScriptText = f"from interchange import CadDocument;print(CadDocument.FromJson({PayloadValue!r}).ToJson(IndentSize=None))"
    OutputValues = {
        Subprocess.check_output(
            [System.executable, "-c", ScriptText],
            cwd=SourceRoot.parent,
            env={**OsSystem.environ, "PYTHONHASHSEED": str(SeedValue)},
            text=True,
        )
        for SeedValue in (1, 7, 31)
    }
    assert len(OutputValues) == 1


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRegistry() -> None:
    ExpectedValues = {
        ItemValue
        for NameValue in KInterchangeApi.__all__
        for ItemValue in (getattr(KInterchangeApi, NameValue),)
        if isinstance(ItemValue, type)
        and (IsDataClass(ItemValue) or issubclass(ItemValue, EnumBase))
    }
    assert set(KTypeRegistry.values()) == ExpectedValues


# behavior coverage protects portable interchange semantics during structural refactors
def CheckDuplicate() -> None:
    ConflictType = EnumBase("CadSource", {"VALUE": "value"})
    with PytestLib.raises(ValueError, match="duplicate interchange type name"):
        RegisterTypes(ConflictType)
    RegisterTypes(CadSource)


# behavior coverage protects portable interchange semantics during structural refactors
@PytestLib.mark.parametrize("RoleValue", tuple(PayloadRole))
def CheckPayRole(RoleValue: PayloadRole) -> None:
    PayloadValue = BrepPayload(
        "geometry",
        "future.kernel",
        "custom",
        "v1",
        "0" * 64,
        PayloadData=b"geometry",
        ValueRole=RoleValue,
        FileExtension=".geo",
    )
    RestoredValue = CadDocument.FromJson(
        ReplaceValue(BuildDocument(), BrepPayloads=(PayloadValue,)).ToJson()
    )
    assert RestoredValue.BrepPayloads == (PayloadValue,)


# behavior coverage protects portable interchange semantics during structural refactors
@PytestLib.mark.parametrize("RuleValue", KLegacyPayloadRules)
def CheckRules(RuleValue) -> None:
    FormatId = sorted(RuleValue.FormatIds)[0] if RuleValue.FormatIds else ""
    KindValue = sorted(RuleValue.Kinds)[0] if RuleValue.Kinds else ""
    SchemaText = sorted(RuleValue.Schemas)[0] if RuleValue.Schemas else ""
    SuffixText = sorted(RuleValue.SourceSuffixes)[0] if RuleValue.SourceSuffixes else ""
    RoleValue, FileExtension = GetLegacyFields(
        {
            "format_id": FormatId,
            "kind": KindValue,
            "schema": SchemaText,
            "source_stream": f"legacy{SuffixText}" if SuffixText else "",
        }
    )
    assert RoleValue == RuleValue.ValueRole
    assert FileExtension == (RuleValue.FileExtension or ".bin")


# behavior coverage protects portable interchange semantics during structural refactors
@PytestLib.mark.parametrize(
    (
        "FormatId",
        "KindValue",
        "SchemaText",
        "SourceStream",
        "RoleValue",
        "ExtensionText",
    ),
    (
        ("parasolid", "binary", "SCH_3500040", "Partition", PayloadRole.KBrep, ".x_b"),
        (
            "catia.cgr",
            "native_tessellation",
            "CATCGRCont",
            "3",
            PayloadRole.KTessellation,
            ".cgr",
        ),
        (
            "catia.v5.osmx",
            "native_feature_graph",
            "CATPrtCont",
            "1",
            PayloadRole.KFeatureHistory,
            ".osmx",
        ),
        (
            "solidworks.mates",
            "mate-list",
            "solidworks.serialized-object-stream",
            "Mates",
            PayloadRole.KAssemblyStructure,
            ".bin",
        ),
        (
            "freecad.fcstd",
            "native_document",
            "FreeCAD Schema 4",
            "Legacy.FCStd",
            PayloadRole.KDocument,
            ".FCStd",
        ),
        (
            "catia.v5.sha256",
            "native_document_binding",
            "sha256",
            "V5_CFV2",
            PayloadRole.KVerification,
            ".sha256",
        ),
        ("future.cad", "opaque", "v9", "Data", PayloadRole.KAuxiliary, ".bin"),
    ),
)
def CheckOldPayload(
    FormatId: str,
    KindValue: str,
    SchemaText: str,
    SourceStream: str,
    RoleValue: PayloadRole,
    ExtensionText: str,
) -> None:
    RawValue = ToData(
        BrepPayload(
            "legacy",
            FormatId,
            KindValue,
            SchemaText,
            HashCodec.sha256(b"legacy payload").hexdigest(),
            PayloadData=b"legacy payload",
            SourceStream=SourceStream,
        )
    )
    RawValue.pop("role")
    RawValue.pop("file_extension")
    RestoredValue = FromData(RawValue)
    assert isinstance(RestoredValue, BrepPayload)
    assert RestoredValue.ValueRole == RoleValue
    assert RestoredValue.FileExtension == ExtensionText
    assert RestoredValue.PayloadData == b"legacy payload"
    assert RestoredValue.SourceDigest == HashCodec.sha256(b"legacy payload").hexdigest()


# behavior coverage protects portable interchange semantics during structural refactors
def CheckPartial() -> None:
    RawValue = ToData(
        BrepPayload(
            "legacy",
            "parasolid",
            "binary",
            "SCH_3500040",
            HashCodec.sha256(b"payload").hexdigest(),
            PayloadData=b"payload",
            ValueRole=PayloadRole.KAuxiliary,
            FileExtension=".custom",
        )
    )
    WithoutRole = dict(RawValue)
    WithoutRole.pop("role")
    RestoredRole = FromData(WithoutRole)
    assert RestoredRole.ValueRole == PayloadRole.KBrep
    assert RestoredRole.FileExtension == ".custom"
    WithoutExt = dict(RawValue)
    WithoutExt.pop("file_extension")
    RestoredExt = FromData(WithoutExt)
    assert RestoredExt.ValueRole == PayloadRole.KAuxiliary
    assert RestoredExt.FileExtension == ".x_b"
    assert FromData(RawValue).ValueRole == PayloadRole.KAuxiliary
    assert FromData(RawValue).FileExtension == ".custom"
    BindingValue = ToData(
        BrepPayload(
            "binding",
            "catia.v5.sha256",
            "native_document_binding",
            "sha256",
            HashCodec.sha256(b"binding").hexdigest(),
            PayloadData=b"binding",
            ValueRole=PayloadRole.KDocument,
            FileExtension=".bin",
        )
    )
    BindingValue.pop("file_extension")
    RestoredBinding = FromData(BindingValue)
    assert RestoredBinding.ValueRole == PayloadRole.KDocument
    assert RestoredBinding.FileExtension == ".sha256"


# behavior coverage protects portable interchange semantics during structural refactors
def CheckUnknown() -> None:
    RawValue = ToData(
        BrepPayload(
            "unknown",
            "future.cad",
            "opaque",
            "v9",
            HashCodec.sha256(b"unknown").hexdigest(),
            PayloadData=b"unknown",
            SourceStream="Container/Opaque.future",
        )
    )
    RawValue.pop("role")
    RawValue.pop("file_extension")
    RestoredValue = FromData(RawValue)
    assert RestoredValue.ValueRole == PayloadRole.KAuxiliary
    assert RestoredValue.FileExtension == ".future"
    assert RestoredValue.PayloadData == b"unknown"


# behavior coverage protects portable interchange semantics during structural refactors
def CheckAllCaps() -> None:
    Capabilities = frozenset(Capability)
    RestoredValue = CadDocument.FromJson(
        ReplaceValue(BuildDocument(), Capabilities=Capabilities).ToJson()
    )
    assert RestoredValue.Capabilities == Capabilities


# behavior coverage protects portable interchange semantics during structural refactors
def CheckFiltering() -> None:
    from tests.interchange.fixtures.AssemblyFixture import BuildAssembly

    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.Assembly
    assert AssemblyValue is not None
    ComponentValue = AssemblyValue.Documents[0]
    ChildValue = ComponentValue.Document
    assert isinstance(ChildValue, CadDocument)
    PayloadValues = tuple(
        (
            BrepPayload(
                f"payload:{RoleValue.value}",
                "future.cad",
                RoleValue.value,
                "1",
                HashCodec.sha256(RoleValue.value.encode("ascii")).hexdigest(),
                PayloadData=RoleValue.value.encode("ascii"),
                ValueRole=RoleValue,
            )
            for RoleValue in (
                PayloadRole.KBrep,
                PayloadRole.KTessellation,
                PayloadRole.KAuxiliary,
            )
        )
    )
    ChildValue = ReplaceValue(
        ChildValue,
        BrepPayloads=PayloadValues,
        Capabilities=ChildValue.Capabilities
        | {Capability.KBrep, Capability.KTessellation, Capability.KNativePayloads},
    )
    SourceValue = ReplaceValue(
        SourceValue,
        Capabilities=SourceValue.Capabilities
        | {Capability.KBrep, Capability.KTessellation, Capability.KNativePayloads},
        Assembly=ReplaceValue(
            AssemblyValue,
            Documents=(ReplaceValue(ComponentValue, Document=ChildValue),),
        ),
    )
    FilteredValue = FilterDocument(
        SourceValue, IncludeBrep=False, IncludeMesh=False, KeepPayloads=False
    )
    assert Capability.KBrep not in FilteredValue.Capabilities
    assert Capability.KTessellation not in FilteredValue.Capabilities
    FilteredChild = FilteredValue.Assembly.Documents[0].Document
    assert isinstance(FilteredChild, CadDocument)
    assert tuple(
        (PayloadValue.ValueRole for PayloadValue in FilteredChild.BrepPayloads)
    ) == (PayloadRole.KAuxiliary,)
    assert Capability.KBrep not in FilteredChild.Capabilities
    assert Capability.KTessellation not in FilteredChild.Capabilities
    DescribedValue = FilterDocument(
        SourceValue, IncludeBrep=False, IncludeMesh=False, KeepPayloads=True
    )
    DescribedChild = DescribedValue.Assembly.Documents[0].Document
    assert isinstance(DescribedChild, CadDocument)
    assert tuple(
        (PayloadValue.ValueRole for PayloadValue in DescribedChild.BrepPayloads)
    ) == tuple((PayloadValue.ValueRole for PayloadValue in PayloadValues))
    assert tuple(
        (PayloadValue.PayloadData for PayloadValue in DescribedChild.BrepPayloads)
    ) == (None, None, b"auxiliary")


# behavior coverage protects portable interchange semantics during structural refactors
def CheckCapTypes() -> None:
    InvalidValue = ReplaceValue(BuildDocument(), Capabilities=frozenset({"parameters"}))
    with PytestLib.raises(DocumentError, match="Capability values"):
        InvalidValue.AssertValid()


# diagnostic links may target the same entity without becoming duplicate identities
def CheckDiagLinks() -> None:
    SourceValue = BuildDocument()
    FirstValue = Diagnostic("first", "first message", EntityId="body:1")
    SecondValue = Diagnostic("second", "second message", EntityId="body:1")
    ReplaceValue(SourceValue, Diagnostics=(FirstValue, SecondValue)).AssertValid()


# behavior coverage protects portable interchange semantics during structural refactors
def CheckInferCaps() -> None:
    SourceValue = ReplaceValue(BuildDocument(), Capabilities=frozenset())
    assert InferCaps(SourceValue) == frozenset(
        {
            Capability.KParamHistory,
            Capability.KSupportPlanes,
            Capability.KEditableSketches,
            Capability.KBodyStructure,
            Capability.KConfigurations,
        }
    )
    ImportedValue = ReplaceValue(
        SourceValue,
        FeatureTimeline=(
            ReplaceValue(
                SourceValue.FeatureTimeline[0], EntityKind=FeatureKind.KImported
            ),
        ),
    )
    assert Capability.KParamHistory not in InferCaps(ImportedValue)


# behavior coverage protects portable interchange semantics during structural refactors
def CheckOrdering() -> None:
    Definitions = (
        ComponentDef("root", "Root", ComponentKind.KAssembly),
        ComponentDef("part", "Part", ComponentKind.KPart),
    )
    SecondValue = ComponentInst("second", "Second", "part", "root", Order=1)
    FirstValue = ComponentInst("first", "First", "part", "root", Order=1)
    AssemblyValue = AssemblyData("root", Definitions, (SecondValue, FirstValue))
    assert AssemblyValue.GetChildren("root") == (FirstValue, SecondValue)
    Capabilities = InferCaps(ReplaceValue(BuildDocument(), Assembly=AssemblyValue))
    assert Capability.KAssemblies in Capabilities
    assert Capability.KAssemblyMates not in Capabilities


# behavior coverage protects portable interchange semantics during structural refactors
@PytestLib.mark.parametrize(
    "ExtensionText",
    (
        "brep",
        ".",
        "..",
        "../brep",
        ".x/b",
        ".x:stream",
        ".x*",
        ".x?",
        '.x"',
        ".x<",
        ".x>",
        ".x|",
        ".x.",
        ".é",
    ),
)
def CheckExtensions(ExtensionText: str) -> None:
    with PytestLib.raises(ValueError, match="file extension"):
        BrepPayload("geometry", "kernel", "shape", "", "", FileExtension=ExtensionText)


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRoleType() -> None:
    with PytestLib.raises(TypeError, match="PayloadRole"):
        BrepPayload(
            "geometry",
            "kernel",
            "shape",
            "",
            "",
            ValueRole="brep",
            FileExtension=".brep",
        )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckForwardRef() -> None:
    SourceValue = BuildDocument()
    FirstValue = FeatureStep(
        "feature:0",
        "Invalid",
        FeatureKind.KExtrusion,
        0,
        InputFeatureIds=("feature:1",),
    )
    SecondValue = FeatureStep("feature:1", "Later", FeatureKind.KExtrusion, 1)
    InvalidValue = CadDocument(
        Source=SourceValue.Source,
        Configurations=SourceValue.Configurations,
        Parameters=(),
        SupportPlanes=SourceValue.SupportPlanes,
        Sketches=(),
        Selections=(),
        FeatureTimeline=(FirstValue, SecondValue),
        Bodies=(DesignBody("body:1", "Body", SecondValue.EntityId),),
    )
    with PytestLib.raises(DocumentError, match="forward dependency"):
        InvalidValue.AssertValid()
