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
from typing import cast as CastValue
import pytest as PytestLib
from interchange import (
    AssemblyData,
    CadDocument,
    Diagnostic,
    Capability,
    ComponentKind,
    FeatureKind,
    FeatureStep,
    PayloadRole,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.models.DocumentCaps import InferCaps
from interchange.document.models.DocumentError import DocumentError
from interchange.document.models.DocumentFilter import FilterDocument
from interchange.features.FeatureBody import DesignBody
from interchange.payloads.PayloadMigrate import GetLegacyFields
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRules import KLegacyPayloadRules
from interchange.payloads.PayloadRuleModel import PayloadRule
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from interchange.serialization.TypeRegistry import KTypeRegistry, RegisterTypes
from tests.interchange.fixtures.DocumentFixture import (
    BuildDocument as BuildFixtureDocument,
)

# dynamic package loading lets reflection inspect the facade without mixed import forms
KInterchangeApi = ImportModule("interchange")


# behavior coverage protects portable interchange semantics during structural refactors
def BuildDocument() -> CadDocument:
    return BuildFixtureDocument()


# historical imports keep conversion suites independent from helper renaming
document = BuildDocument


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRoundtrip() -> None:
    SourceValue = BuildDocument()
    RestoredValue = CadDocument.from_json(SourceValue.to_json())
    assert RestoredValue == SourceValue
    assert isinstance(RestoredValue.capabilities, frozenset)
    assert isinstance(RestoredValue.feature_timeline, tuple)


# behavior coverage protects portable interchange semantics during structural refactors
def CheckStableJson() -> None:
    PayloadValue = BuildDocument().to_json(indent=None)
    SourceRoot = FilePath(__file__).parents[3] / "src"
    ScriptText = f"from interchange import CadDocument;print(CadDocument.from_json({PayloadValue!r}).to_json(indent=None))"
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
    CadSource = EnumBase("CadSource", {"VALUE": "value"})
    with PytestLib.raises(ValueError, match="duplicate interchange type name"):
        RegisterTypes(CadSource)
    from interchange.records.RecordSource import CadSource as CadSourceModel

    RegisterTypes(CadSourceModel)


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
    RestoredValue = CadDocument.from_json(
        ReplaceValue(BuildDocument(), brep_payloads=(PayloadValue,)).to_json()
    )
    assert RestoredValue.brep_payloads == (PayloadValue,)


# behavior coverage protects portable interchange semantics during structural refactors
@PytestLib.mark.parametrize("RuleValue", KLegacyPayloadRules)
def CheckRules(RuleValue: PayloadRule) -> None:
    FormatId = sorted(RuleValue.format_ids)[0] if RuleValue.format_ids else ""
    KindValue = sorted(RuleValue.kinds)[0] if RuleValue.kinds else ""
    SchemaText = sorted(RuleValue.schemas)[0] if RuleValue.schemas else ""
    SuffixText = (
        sorted(RuleValue.source_suffixes)[0] if RuleValue.source_suffixes else ""
    )
    RoleValue, FileExtension = GetLegacyFields(
        {
            "format_id": FormatId,
            "kind": KindValue,
            "schema": SchemaText,
            "source_stream": f"legacy{SuffixText}" if SuffixText else "",
        }
    )
    assert RoleValue == RuleValue.role
    assert FileExtension == (RuleValue.file_extension or ".bin")


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
    assert isinstance(RawValue, dict)
    RawValue.pop("role")
    RawValue.pop("file_extension")
    RestoredValue = FromData(RawValue)
    assert isinstance(RestoredValue, BrepPayload)
    RestoredPayload = RestoredValue
    assert RestoredPayload.ValueRole == RoleValue
    assert RestoredPayload.FileExtension == ExtensionText
    assert RestoredPayload.PayloadData == b"legacy payload"
    assert (
        RestoredPayload.SourceDigest == HashCodec.sha256(b"legacy payload").hexdigest()
    )


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
    assert isinstance(RawValue, dict)
    WithoutRole = dict(RawValue)
    WithoutRole.pop("role")
    RestoredRole = FromData(WithoutRole)
    assert isinstance(RestoredRole, BrepPayload)
    RolePayload = RestoredRole
    assert RolePayload.ValueRole == PayloadRole.KBrep
    assert RolePayload.FileExtension == ".custom"
    WithoutExt = dict(RawValue)
    WithoutExt.pop("file_extension")
    RestoredExt = FromData(WithoutExt)
    assert isinstance(RestoredExt, BrepPayload)
    ExtPayload = RestoredExt
    assert ExtPayload.ValueRole == PayloadRole.KAuxiliary
    assert ExtPayload.FileExtension == ".x_b"
    RestoredValue = FromData(RawValue)
    assert isinstance(RestoredValue, BrepPayload)
    RestoredPayload = RestoredValue
    assert RestoredPayload.ValueRole == PayloadRole.KAuxiliary
    assert RestoredPayload.FileExtension == ".custom"
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
    assert isinstance(BindingValue, dict)
    BindingValue.pop("file_extension")
    RestoredBinding = FromData(BindingValue)
    assert isinstance(RestoredBinding, BrepPayload)
    BindingPayload = RestoredBinding
    assert BindingPayload.ValueRole == PayloadRole.KDocument
    assert BindingPayload.FileExtension == ".sha256"


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
    assert isinstance(RawValue, dict)
    RawValue.pop("role")
    RawValue.pop("file_extension")
    RestoredValue = FromData(RawValue)
    assert isinstance(RestoredValue, BrepPayload)
    RestoredPayload = RestoredValue
    assert RestoredPayload.ValueRole == PayloadRole.KAuxiliary
    assert RestoredPayload.FileExtension == ".future"
    assert RestoredPayload.PayloadData == b"unknown"


# malformed wire values must fail before they can reach model constructors
def CheckWireData() -> None:
    with PytestLib.raises(TypeError, match="wire object keys must be strings"):
        ToData({1: "invalid"})
    with PytestLib.raises(TypeError, match="wire object keys must be strings"):
        FromData({1: "invalid"})
    with PytestLib.raises(ValueError, match="value must be a list"):
        FromData({"$tuple": "invalid"})
    with PytestLib.raises(ValueError, match="type must be nonempty text"):
        FromData({"$enum": 1, "value": "invalid"})


# behavior coverage protects portable interchange semantics during structural refactors
def CheckAllCaps() -> None:
    Capabilities = frozenset(Capability)
    RestoredValue = CadDocument.from_json(
        ReplaceValue(BuildDocument(), capabilities=Capabilities).to_json()
    )
    assert RestoredValue.capabilities == Capabilities


# behavior coverage protects portable interchange semantics during structural refactors
def CheckFiltering() -> None:
    from tests.interchange.fixtures.AssemblyFixture import BuildAssembly

    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.assembly
    assert AssemblyValue is not None
    ComponentValue = AssemblyValue.documents[0]
    ChildValue = ComponentValue.document
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
        brep_payloads=PayloadValues,
        capabilities=ChildValue.capabilities
        | {Capability.KBrep, Capability.KTessellation, Capability.KNativePayloads},
    )
    SourceValue = ReplaceValue(
        SourceValue,
        capabilities=SourceValue.capabilities
        | {Capability.KBrep, Capability.KTessellation, Capability.KNativePayloads},
        assembly=ReplaceValue(
            AssemblyValue,
            documents=(ReplaceValue(ComponentValue, document=ChildValue),),
        ),
    )
    FilteredValue = FilterDocument(
        SourceValue, IncludeBrep=False, IncludeMesh=False, KeepPayloads=False
    )
    assert Capability.KBrep not in FilteredValue.capabilities
    assert Capability.KTessellation not in FilteredValue.capabilities
    FilteredAssembly = FilteredValue.assembly
    assert FilteredAssembly is not None
    FilteredChild = FilteredAssembly.documents[0].document
    assert isinstance(FilteredChild, CadDocument)
    assert tuple(
        (PayloadValue.role for PayloadValue in FilteredChild.brep_payloads)
    ) == (PayloadRole.KAuxiliary,)
    assert Capability.KBrep not in FilteredChild.capabilities
    assert Capability.KTessellation not in FilteredChild.capabilities
    DescribedValue = FilterDocument(
        SourceValue, IncludeBrep=False, IncludeMesh=False, KeepPayloads=True
    )
    DescribedAssembly = DescribedValue.assembly
    assert DescribedAssembly is not None
    DescribedChild = DescribedAssembly.documents[0].document
    assert isinstance(DescribedChild, CadDocument)
    assert tuple(
        (PayloadValue.role for PayloadValue in DescribedChild.brep_payloads)
    ) == tuple((PayloadValue.role for PayloadValue in PayloadValues))
    assert tuple(
        (PayloadValue.data for PayloadValue in DescribedChild.brep_payloads)
    ) == (None, None, b"auxiliary")


# behavior coverage protects portable interchange semantics during structural refactors
def CheckCapTypes() -> None:
    InvalidValue = ReplaceValue(
        BuildDocument(),
        capabilities=frozenset({CastValue(Capability, "parameters")}),
    )
    with PytestLib.raises(DocumentError, match="Capability values"):
        InvalidValue.assert_valid()


# diagnostic links may target the same entity without becoming duplicate identities
def CheckDiagLinks() -> None:
    SourceValue = BuildDocument()
    FirstValue = Diagnostic("first", "first message", EntityId="body:1")
    SecondValue = Diagnostic("second", "second message", EntityId="body:1")
    ReplaceValue(SourceValue, diagnostics=(FirstValue, SecondValue)).assert_valid()


# behavior coverage protects portable interchange semantics during structural refactors
def CheckInferCaps() -> None:
    SourceValue = ReplaceValue(BuildDocument(), capabilities=frozenset())
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
        feature_timeline=(
            ReplaceValue(SourceValue.feature_timeline[0], kind=FeatureKind.KImported),
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
    Capabilities = InferCaps(ReplaceValue(BuildDocument(), assembly=AssemblyValue))
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
        input_feature_ids=("feature:1",),
    )
    SecondValue = FeatureStep("feature:1", "Later", FeatureKind.KExtrusion, 1)
    InvalidValue = CadDocument(
        source=SourceValue.source,
        configurations=SourceValue.configurations,
        parameters=(),
        support_planes=SourceValue.support_planes,
        sketches=(),
        selections=(),
        feature_timeline=(FirstValue, SecondValue),
        bodies=(DesignBody("body:1", "Body", SecondValue.EntityId),),
    )
    with PytestLib.raises(DocumentError, match="forward dependency"):
        InvalidValue.assert_valid()
