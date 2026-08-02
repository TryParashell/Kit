from __future__ import annotations

from types import MappingProxyType

from convert.adapters.base import AdapterInfo, CarrierReason
from interchange import Capability

from .protocol import (
    ASSEMBLY_JOINT_GROUP_TYPE_ID,
    ASSEMBLY_LINK_TYPE_ID,
    ASSEMBLY_ROOT_TYPE_ID,
    FEATURE_WRITE_TYPE_IDS,
    SKETCH_TYPE_ID,
)


SUFFIX = ".FCStd"
CAPABILITY_WRITE_TYPE_IDS = MappingProxyType(
    {
        Capability.PARAMETERS: frozenset({"Spreadsheet::Sheet"}),
        Capability.PARAMETRIC_HISTORY: frozenset().union(
            *FEATURE_WRITE_TYPE_IDS.values()
        ),
        Capability.SUPPORT_PLANES: frozenset(),
        Capability.EDITABLE_SKETCHES: frozenset({SKETCH_TYPE_ID}),
        Capability.SELECTIONS: frozenset(),
        Capability.BODY_STRUCTURE: frozenset(),
        Capability.CONFIGURATIONS: frozenset(),
        Capability.EXPRESSIONS: frozenset(),
        Capability.BREP: frozenset({"Part::PropertyPartShape"}),
        Capability.TESSELLATION: frozenset(
            {"Mesh::Feature", "Mesh::PropertyMeshKernel"}
        ),
        Capability.ASSEMBLIES: frozenset(
            {ASSEMBLY_ROOT_TYPE_ID, ASSEMBLY_LINK_TYPE_ID, "App::Link"}
        ),
        Capability.ASSEMBLY_MATES: frozenset(
            {ASSEMBLY_JOINT_GROUP_TYPE_ID, "App::PropertyEnumeration:JointType"}
        ),
        Capability.COMPONENT_DOCUMENTS: frozenset({"App::PropertyXLink"}),
        Capability.EXTERNAL_REFERENCES: frozenset({"App::PropertyXLink"}),
        Capability.MATERIALS: frozenset(),
        Capability.NATIVE_PAYLOADS: frozenset(),
        Capability.PROVENANCE: frozenset(),
        Capability.ROUNDTRIP_METADATA: frozenset(),
    }
)
if CAPABILITY_WRITE_TYPE_IDS.keys() != set(Capability):
    raise RuntimeError("FreeCAD capability write types are not exhaustive")
CAPABILITY_CARRIER_REASONS = MappingProxyType(
    {
        Capability.PARAMETERS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.PARAMETRIC_HISTORY: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.SUPPORT_PLANES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.EDITABLE_SKETCHES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.SELECTIONS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.BODY_STRUCTURE: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.CONFIGURATIONS: CarrierReason.TARGET_UNSUPPORTED,
        Capability.EXPRESSIONS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.BREP: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.TESSELLATION: CarrierReason.SOURCE_OPAQUE,
        Capability.ASSEMBLIES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.ASSEMBLY_MATES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.COMPONENT_DOCUMENTS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.EXTERNAL_REFERENCES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.MATERIALS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.NATIVE_PAYLOADS: CarrierReason.SOURCE_OPAQUE,
        Capability.PROVENANCE: CarrierReason.TARGET_UNSUPPORTED,
        Capability.ROUNDTRIP_METADATA: CarrierReason.TARGET_UNSUPPORTED,
    }
)
if CAPABILITY_CARRIER_REASONS.keys() != set(Capability):
    raise RuntimeError("FreeCAD capability carrier reasons are not exhaustive")
NATIVE_CAPABILITIES = frozenset(
    capability for capability, type_ids in CAPABILITY_WRITE_TYPE_IDS.items() if type_ids
)


INFO = AdapterInfo(
    format_id="freecad.fcstd",
    name="FreeCAD FCStd",
    version="1.0",
    extensions=(SUFFIX,),
    capabilities=frozenset(Capability),
    native_capabilities=NATIVE_CAPABILITIES,
    media_types=("application/x-extension-fcstd",),
    part_extensions=(SUFFIX,),
    assembly_extensions=(SUFFIX,),
)
FORMAT_ID = INFO.format_id
