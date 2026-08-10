# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import suppress
from dataclasses import dataclass, replace
import hashlib
from io import BytesIO
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import struct
import tempfile
from typing import Any, Mapping, Sequence
import xml.etree.ElementTree as ET

from convert.adapters.base import (
    AdapterInfo,
    CapabilityTransfer,
    CarrierReason,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    TransferMode,
    WriteOptions,
    WriteResult,
    is_binary_destination,
)
from interchange import (
    ArcEllipseGeometry,
    ArcGeometry,
    ArcParabolaGeometry,
    AssemblyData,
    Body,
    BooleanOperation,
    BoundingBox,
    BrepModel,
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    ChamferFeature,
    CircleGeometry,
    CombineFeature,
    ComponentDefinition,
    ComponentDocument,
    ComponentInstance,
    ComponentKind,
    Configuration,
    ConstraintReference,
    Diagnostic,
    DomeFeature,
    ExtrusionEndCondition,
    ExtrusionFeature,
    Expression,
    EllipseGeometry,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    GeometryKind,
    HoleFeature,
    LineGeometry,
    MateAlignment,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4,
    Mesh,
    MoveBodyFeature,
    NativeFeatureDefinition,
    NativeGeometry,
    Parameter,
    ParameterRole,
    ParameterValue,
    PointGeometry,
    PayloadRole,
    Provenance,
    ProvenanceSpan,
    ReferencePlaneFeature,
    RevolutionFeature,
    ScaleFeature,
    Selection,
    SelectionPathElement,
    Severity,
    ShellFeature,
    Sketch,
    SketchConstraint,
    SketchEntity,
    SplineGeometry,
    SupportPlane,
    TopologySummary,
    Transform,
    UnitSystem,
    ValueKind,
    Vector2,
    Vector3,
    frozen_mapping,
    filter_document,
    infer_capabilities,
    retained_capabilities,
    semantic_metadata,
    source_payload_indexes,
    with_wrapper_metadata,
)

from .assembly import (
    MATE_VALUE_SEMANTICS,
    NATIVE_MATE_ALIGNMENT_BY_CODE,
    NATIVE_MATE_ENTITY_MARKERS,
    NATIVE_MATE_NEUTRAL_KIND_ALIASES,
    NativeAssembly,
    NativeAssemblyDefinition,
    NativeAssemblyEncoding,
    NativeAssemblyOccurrence,
    NativeMate,
    NativeMateEntity,
    NativeMateList,
    decode_mate_list,
    decode_native_assembly,
    encode_native_assembly,
)
from .assembly_core import AsmCoreItem, EncodeAsmCore
from .container import SldprtArchive, SldprtFormatError, build_sldprt
from .format import (
    COMPONENT_TREE_STREAM,
    CONTAINER_VERSIONS,
    CONTENT_TYPES_STREAM,
    DISPLAY_LISTS_STREAM,
    FEATURES_STREAM,
    FORMAT_ID_BY_SUFFIX,
    INFO,
    KEYWORDS_STREAM,
    KIT_DOCUMENT_STREAM,
    KIT_NATIVE_STREAM,
    KIT_RESOLVED_STREAM,
    MATES_STREAM_NAME,
    MATES_STREAM_SUFFIX,
    PARTITION_STREAM,
    PLANE_FEATURE_TYPES,
    RELATIONSHIPS_STREAM,
    RESOLVED_FEATURES_STREAM,
    SOLIDWORKS_STREAM,
    SOLID_BODY_FEATURE_TYPES,
    SUFFIX_BY_FORMAT_ID,
)
from .native import (
    NativeDimension,
    NativeEquation,
    NativeFeature,
    NativeMarker,
    NativeModel,
    NativeOperation,
    NativeProfile,
    NativeSketch,
    NativeAssemblyEnvelope,
    DIRECTION_AXIS_ROLE,
    decode_native_model,
    encode_native_assembly_envelope,
    encode_native_part,
    operation_axis_subelement,
)
from .parasolid import (
    ParasolidPayload,
    ParasolidWriteError,
    contains_parasolid_payload,
    decode_brep_model,
    decode_partition_stream,
    encode_blank_partition_stream,
    encode_brep_model,
    encode_partition_stream,
    is_native_parasolid_payload,
)

_FORMAT_ID = INFO.format_id
_ASSEMBLY_FORMAT_ID = INFO.aliases[0]
_SOURCE_BYTES_KEY = "solidworks_source_bytes"
_SOURCE_SHA256_KEY = "solidworks_source_sha256"
_SOURCE_SEMANTIC_SHA256_KEY = "solidworks_source_semantic_sha256"
_SOURCE_FORMAT_KEY = "solidworks_source_format_id"
_UNSYNTHESISED_ASSEMBLY_STREAMS = (
    "Contents/Config-0-LWDATA",
    DISPLAY_LISTS_STREAM,
    "Contents/User Units Table",
    "SwDocContentMgr/SwDocContentMgrInfo",
    "docProps/ISolidWorksInformation.xml",
    KEYWORDS_STREAM,
)
_ASSEMBLY_READER_REQUIRED_STREAMS = (
    "Contents/CMgr",
    "Contents/Config-0",
    RESOLVED_FEATURES_STREAM,
    "Contents/Definition",
)
_ASSEMBLY_DONOR_CARRIED_STREAMS = (
    *_ASSEMBLY_READER_REQUIRED_STREAMS,
    "Contents/Config-0-ModelHeader",
    "Header2",
)
_ASSEMBLY_REWRITABLE_DONOR_STREAMS = frozenset(
    {
        KIT_DOCUMENT_STREAM,
        KIT_NATIVE_STREAM,
        KIT_RESOLVED_STREAM,
        COMPONENT_TREE_STREAM,
    }
)
_VENDOR_REJECTED_ASSEMBLY_RECORDS: tuple[str, ...] = ()
_ATTESTED_COMPATIBILITIES = frozenset(
    {
        "kit-neutral-only",
        "native-assembly-with-kit-neutral",
        "native-brep-with-kit-neutral",
        "native-metadata-with-kit-neutral",
        "native-source-with-kit-neutral",
        "native-template",
    }
)
_SOURCE_KEYS = frozenset(
    {
        _SOURCE_BYTES_KEY,
        _SOURCE_SHA256_KEY,
        _SOURCE_SEMANTIC_SHA256_KEY,
        _SOURCE_FORMAT_KEY,
    }
)
_NUMBER_TEXT = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
_RESOLVED_CONFIGURATION_STREAM = re.compile(r"^Contents/Config-(\d+)-ResolvedFeatures$")
_TARGET_UNSUPPORTED_CAPABILITIES = frozenset(
    {
        Capability.NATIVE_PAYLOADS,
        Capability.PROVENANCE,
        Capability.ROUNDTRIP_METADATA,
    }
)


@dataclass(frozen=True, slots=True)
class _GeneratedStreams:
    streams: dict[str, bytes]
    native_brep: str
    native_capabilities: frozenset[Capability]
    compatibility: str
    application_usable: bool
    vendor_loadable: bool
    mixed_capabilities: frozenset[Capability] = frozenset()
    unexpressed: tuple[str, ...] = ()
    donor_notes: tuple[str, ...] = ()
    reader_gaps: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _AssemblyTemplatePatch:
    capabilities: frozenset[Capability]
    divergences: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _AssemblyBundle:
    names: Mapping[str, str]
    payloads: Mapping[Path, bytes]
    complete: bool


_WRAPPER_METADATA_KEYS = _SOURCE_KEYS | frozenset(
    {
        "adapter",
        "embedded_source_format_id",
        "embedded_source_path",
        "embedded_source_sha256",
        "file_id",
        "solidworks.container_compatibility",
        "stream_names",
    }
)
_FEATURE_KIND_BY_NATIVE = {
    "3dprofilefeature": FeatureKind.REFERENCE,
    "3dsplinecurve": FeatureKind.REFERENCE,
    "advholewzd": FeatureKind.HOLE,
    "advstructmember": FeatureKind.SWEEP,
    "aem3dcontact": FeatureKind.NATIVE,
    "aemgravity": FeatureKind.NATIVE,
    "aemlineardamper": FeatureKind.NATIVE,
    "aemlinearmotor": FeatureKind.NATIVE,
    "aemlinearspring": FeatureKind.NATIVE,
    "aemrotationalmotor": FeatureKind.NATIVE,
    "aemtorque": FeatureKind.NATIVE,
    "aemtorsionaldamper": FeatureKind.NATIVE,
    "aemtorsionalspring": FeatureKind.NATIVE,
    "ambientlight": FeatureKind.REFERENCE,
    "apattern": FeatureKind.PATTERN,
    "asmexploder": FeatureKind.NATIVE,
    "attribute": FeatureKind.REFERENCE,
    "axis": FeatureKind.REFERENCE,
    "basebody": FeatureKind.EXTRUSION,
    "bending": FeatureKind.REFINE,
    "bendtableachor": FeatureKind.REFERENCE,
    "blend": FeatureKind.LOFT,
    "blendcut": FeatureKind.LOFT,
    "blendregion": FeatureKind.LOFT,
    "blendrefsurface": FeatureKind.SURFACE,
    "blockdef": FeatureKind.REFERENCE,
    "blockfolder": FeatureKind.REFERENCE,
    "body-delete/keep": FeatureKind.BOOLEAN,
    "body-move/copy": FeatureKind.NATIVE,
    "bodyexplodestep": FeatureKind.NATIVE,
    "bomfeat": FeatureKind.NATIVE,
    "bomtemplate": FeatureKind.REFERENCE,
    "boss": FeatureKind.EXTRUSION,
    "bossthin": FeatureKind.EXTRUSION,
    "boundingbox": FeatureKind.REFERENCE,
    "breakcorner": FeatureKind.CHAMFER,
    "camerafeature": FeatureKind.REFERENCE,
    "cavity": FeatureKind.BOOLEAN,
    "centerofmass": FeatureKind.REFERENCE,
    "chamfer": FeatureKind.CHAMFER,
    "cirpattern": FeatureKind.PATTERN,
    "combine": FeatureKind.BOOLEAN,
    "combinebodies": FeatureKind.BOOLEAN,
    "commentsfolder": FeatureKind.REFERENCE,
    "compexplodestep": FeatureKind.NATIVE,
    "compositecurve": FeatureKind.REFERENCE,
    "coordsys": FeatureKind.REFERENCE,
    "cornertrim": FeatureKind.NATIVE,
    "cosmeticthread": FeatureKind.NATIVE,
    "cosmeticweldbead": FeatureKind.NATIVE,
    "cosmeticweldsubfolder": FeatureKind.REFERENCE,
    "createassemfeat": FeatureKind.NATIVE,
    "crossbreak": FeatureKind.NATIVE,
    "curveinfile": FeatureKind.REFERENCE,
    "curvepattern": FeatureKind.PATTERN,
    "cut": FeatureKind.EXTRUSION,
    "cut-revolve": FeatureKind.REVOLUTION,
    "cut-sweep": FeatureKind.SWEEP,
    "cutlistfolder": FeatureKind.REFERENCE,
    "cutthin": FeatureKind.EXTRUSION,
    "deform": FeatureKind.REFINE,
    "deletebody": FeatureKind.BOOLEAN,
    "delface": FeatureKind.SURFACE,
    "derivedcirpattern": FeatureKind.PATTERN,
    "derivedholepattern": FeatureKind.PATTERN,
    "derivedlpattern": FeatureKind.PATTERN,
    "detailcircle": FeatureKind.REFERENCE,
    "dimpattern": FeatureKind.PATTERN,
    "directionlight": FeatureKind.REFERENCE,
    "dome": FeatureKind.REFINE,
    "draft": FeatureKind.DRAFT,
    "drbreakoutsectionline": FeatureKind.REFERENCE,
    "drsectionline": FeatureKind.REFERENCE,
    "edgeflange": FeatureKind.EXTRUSION,
    "edgemerge": FeatureKind.REFINE,
    "emboss": FeatureKind.REFINE,
    "endcap": FeatureKind.EXTRUSION,
    "explodelineprofilefeature": FeatureKind.REFERENCE,
    "extendrefsurface": FeatureKind.SURFACE,
    "extrusion": FeatureKind.EXTRUSION,
    "extrurefsurface": FeatureKind.SURFACE,
    "familytablefeat": FeatureKind.REFERENCE,
    "featsurfacebodyfolder": FeatureKind.REFERENCE,
    "fillrefsurface": FeatureKind.SURFACE,
    "fillet": FeatureKind.FILLET,
    "flatpattern": FeatureKind.NATIVE,
    "flattenbends": FeatureKind.NATIVE,
    "flattensurface": FeatureKind.SURFACE,
    "fold": FeatureKind.NATIVE,
    "formtoolinstance": FeatureKind.NATIVE,
    "ftrfolder": FeatureKind.REFERENCE,
    "generaltableanchor": FeatureKind.REFERENCE,
    "gridfeature": FeatureKind.REFERENCE,
    "groundplane": FeatureKind.REFERENCE,
    "gusset": FeatureKind.EXTRUSION,
    "hem": FeatureKind.NATIVE,
    "helix": FeatureKind.HELIX,
    "helix/spiral": FeatureKind.HELIX,
    "holeseries": FeatureKind.HOLE,
    "holetableanchor": FeatureKind.REFERENCE,
    "holewizard": FeatureKind.HOLE,
    "holewzd": FeatureKind.HOLE,
    "imported": FeatureKind.IMPORTED,
    "importedcurve": FeatureKind.REFERENCE,
    "incontextfeatholder": FeatureKind.REFERENCE,
    "insertedfeaturefolder": FeatureKind.REFERENCE,
    "jog": FeatureKind.NATIVE,
    "libraryfeature": FeatureKind.NATIVE,
    "livesection": FeatureKind.REFERENCE,
    "localchainpattern": FeatureKind.PATTERN,
    "localcirpattern": FeatureKind.PATTERN,
    "localcurvepattern": FeatureKind.PATTERN,
    "locallpattern": FeatureKind.PATTERN,
    "localsketchpattern": FeatureKind.PATTERN,
    "loft": FeatureKind.LOFT,
    "loft-thin": FeatureKind.LOFT,
    "loftedbend": FeatureKind.LOFT,
    "lpattern": FeatureKind.PATTERN,
    "macrofeature": FeatureKind.NATIVE,
    "magneticgroundplane": FeatureKind.REFERENCE,
    "matecamtangent": FeatureKind.NATIVE,
    "matecoincident": FeatureKind.NATIVE,
    "mateconcentric": FeatureKind.NATIVE,
    "matedistancedim": FeatureKind.NATIVE,
    "mategeardim": FeatureKind.NATIVE,
    "matehinge": FeatureKind.NATIVE,
    "mateinplace": FeatureKind.NATIVE,
    "matelimitdistancedim": FeatureKind.NATIVE,
    "matelinearcoupler": FeatureKind.NATIVE,
    "matelock": FeatureKind.NATIVE,
    "mateparallel": FeatureKind.NATIVE,
    "mateperpendicular": FeatureKind.NATIVE,
    "mateplanarangledim": FeatureKind.NATIVE,
    "mateprofilecenter": FeatureKind.NATIVE,
    "materackpiniondim": FeatureKind.NATIVE,
    "matereferencegroupfolder": FeatureKind.REFERENCE,
    "matescrew": FeatureKind.NATIVE,
    "mateslot": FeatureKind.NATIVE,
    "matesymmetric": FeatureKind.NATIVE,
    "matetangent": FeatureKind.NATIVE,
    "mateuniversaljoint": FeatureKind.NATIVE,
    "matewidth": FeatureKind.NATIVE,
    "mbimport": FeatureKind.IMPORTED,
    "midrefsurface": FeatureKind.SURFACE,
    "mirror": FeatureKind.MIRROR,
    "mirrorcompfeat": FeatureKind.MIRROR,
    "mirrorpattern": FeatureKind.MIRROR,
    "mirrorsolid": FeatureKind.MIRROR,
    "mirrorstock": FeatureKind.MIRROR,
    "moldcorecavitysolids": FeatureKind.BOOLEAN,
    "moldpartinggeom": FeatureKind.SURFACE,
    "moldpartline": FeatureKind.REFERENCE,
    "moldshutoffsrf": FeatureKind.SURFACE,
    "movecopybody": FeatureKind.NATIVE,
    "netblend": FeatureKind.LOFT,
    "normalcut": FeatureKind.EXTRUSION,
    "offsetrefsurface": FeatureKind.OFFSET,
    "offsetrefsuface": FeatureKind.OFFSET,
    "onebend": FeatureKind.NATIVE,
    "planarsurface": FeatureKind.SURFACE,
    "pline": FeatureKind.REFERENCE,
    "pointlight": FeatureKind.REFERENCE,
    "posgroupfolder": FeatureKind.REFERENCE,
    "processbends": FeatureKind.NATIVE,
    "profilefeature": FeatureKind.REFERENCE,
    "profileftrfolder": FeatureKind.REFERENCE,
    "prtexploder": FeatureKind.NATIVE,
    "punch": FeatureKind.NATIVE,
    "punchtableanchor": FeatureKind.REFERENCE,
    "radiaterefsurface": FeatureKind.SURFACE,
    "refaxis": FeatureKind.REFERENCE,
    "refaxisftrfolder": FeatureKind.REFERENCE,
    "refcurve": FeatureKind.REFERENCE,
    "refplaneftrfolder": FeatureKind.REFERENCE,
    "refpoint": FeatureKind.REFERENCE,
    "reference": FeatureKind.REFERENCE,
    "referencepattern": FeatureKind.PATTERN,
    "refsurface": FeatureKind.SURFACE,
    "replaceface": FeatureKind.SURFACE,
    "revisiontableanchor": FeatureKind.REFERENCE,
    "rib": FeatureKind.EXTRUSION,
    "rip": FeatureKind.NATIVE,
    "revolve": FeatureKind.REVOLUTION,
    "revolution": FeatureKind.REVOLUTION,
    "revolutionthin": FeatureKind.REVOLUTION,
    "revcut": FeatureKind.REVOLUTION,
    "revolvrefsurf": FeatureKind.SURFACE,
    "ruledsrffromedge": FeatureKind.SURFACE,
    "round fillet corner": FeatureKind.FILLET,
    "scale": FeatureKind.SCALE,
    "sculpt": FeatureKind.BOOLEAN,
    "sensor": FeatureKind.REFERENCE,
    "sewrefsurface": FeatureKind.SURFACE,
    "shape": FeatureKind.NATIVE,
    "sheetmetal": FeatureKind.NATIVE,
    "shell": FeatureKind.SHELL,
    "sidecore": FeatureKind.BOOLEAN,
    "simplotfeature": FeatureKind.NATIVE,
    "simplotxaxisfeature": FeatureKind.NATIVE,
    "simplotyaxisfeature": FeatureKind.NATIVE,
    "simresultfolder": FeatureKind.NATIVE,
    "sketch": FeatureKind.REFERENCE,
    "sketchbend": FeatureKind.NATIVE,
    "sketchbitmap": FeatureKind.REFERENCE,
    "sketchblockdef": FeatureKind.REFERENCE,
    "sketchblockinst": FeatureKind.REFERENCE,
    "sketchhole": FeatureKind.HOLE,
    "sketchpattern": FeatureKind.PATTERN,
    "sketchslicefolder": FeatureKind.REFERENCE,
    "sm3dbend": FeatureKind.NATIVE,
    "smbaseflange": FeatureKind.EXTRUSION,
    "smgusset": FeatureKind.NATIVE,
    "smmiteredflange": FeatureKind.EXTRUSION,
    "smartcomponentfeature": FeatureKind.NATIVE,
    "solidtosheetmetal": FeatureKind.NATIVE,
    "split": FeatureKind.BOOLEAN,
    "splitbody": FeatureKind.BOOLEAN,
    "spotlight": FeatureKind.REFERENCE,
    "stock": FeatureKind.IMPORTED,
    "strctsysbtwptsmbrfeat": FeatureKind.NATIVE,
    "strctsyscnrfeat": FeatureKind.NATIVE,
    "strctsyscnrgrpfeat": FeatureKind.REFERENCE,
    "strctsyscnrmgmtfeat": FeatureKind.REFERENCE,
    "strctsysfeat": FeatureKind.REFERENCE,
    "strctsysgrpfeat": FeatureKind.REFERENCE,
    "strctsyspathsegmbrfeat": FeatureKind.NATIVE,
    "strctsyspttomem": FeatureKind.NATIVE,
    "strctsysrefplnmbrfeat": FeatureKind.NATIVE,
    "strctsysskptlenmbrfeat": FeatureKind.NATIVE,
    "strctsyssupplnmbrfeat": FeatureKind.NATIVE,
    "strctsyssurfplnmbrfeat": FeatureKind.NATIVE,
    "subatomfolder": FeatureKind.REFERENCE,
    "subweldfolder": FeatureKind.REFERENCE,
    "surfacebodyfolder": FeatureKind.REFERENCE,
    "surface-extrude": FeatureKind.SURFACE,
    "surfcut": FeatureKind.SURFACE,
    "sweep": FeatureKind.SWEEP,
    "sweepcut": FeatureKind.SWEEP,
    "sweeprefsurface": FeatureKind.SURFACE,
    "sweepthread": FeatureKind.SWEEP,
    "tablepattern": FeatureKind.PATTERN,
    "templateflatpattern": FeatureKind.REFERENCE,
    "templatesheetmetal": FeatureKind.REFERENCE,
    "thicken": FeatureKind.SURFACE,
    "thickencut": FeatureKind.SURFACE,
    "toroidalbend": FeatureKind.NATIVE,
    "trimrefsurface": FeatureKind.SURFACE,
    "unfold": FeatureKind.NATIVE,
    "untrimrefsurf": FeatureKind.SURFACE,
    "varfillet": FeatureKind.FILLET,
    "viewbodyfeature": FeatureKind.REFERENCE,
    "weldbeadfeat": FeatureKind.NATIVE,
    "weldcornerfeat": FeatureKind.NATIVE,
    "weldmemberfeat": FeatureKind.SWEEP,
    "weldmentfeature": FeatureKind.NATIVE,
    "weldmenttableanchor": FeatureKind.REFERENCE,
    "weldmenttablefeat": FeatureKind.REFERENCE,
    "weldtableanchor": FeatureKind.REFERENCE,
    "xformstock": FeatureKind.IMPORTED,
    **{
        native_type: FeatureKind.REFERENCE
        for native_type in (*PLANE_FEATURE_TYPES, *SOLID_BODY_FEATURE_TYPES)
    },
}


class SldprtAdapter:
    @property
    def info(self) -> AdapterInfo:
        return INFO

    def probe(self, source: Source) -> ProbeResult:
        try:
            data, label = _source_bytes(source)
            if len(data) < 8:
                return ProbeResult(
                    _FORMAT_ID, 0.0, "file is shorter than the container header"
                )
            version = struct.unpack_from(">I", data, 4)[0]
            if version not in CONTAINER_VERSIONS:
                return ProbeResult(
                    _FORMAT_ID, 0.0, f"unsupported container version {version}"
                )
            archive = SldprtArchive.from_bytes(data, label)
        except (OSError, SldprtFormatError, TypeError, ValueError) as exc:
            return ProbeResult(_FORMAT_ID, 0.0, str(exc))
        names = archive.streams
        if KEYWORDS_STREAM in names and any(
            _RESOLVED_CONFIGURATION_STREAM.fullmatch(name) for name in names
        ):
            return ProbeResult(
                _FORMAT_ID, 1.0, "native history and resolved-feature streams found"
            )
        return ProbeResult(
            _FORMAT_ID, 0.6, "recognized SOLIDWORKS compound stream container"
        )

    def read(self, source: Source, options: ReadOptions | None = None) -> CadDocument:
        settings = options or ReadOptions()
        data, label = _source_bytes(source)
        archive = SldprtArchive.from_bytes(data, label)
        embedded = archive.get(KIT_DOCUMENT_STREAM)
        if embedded is not None:
            document = _embedded_document(
                self, archive, data, label, embedded, settings
            )
            _validate_source_suffix(label, document.assembly is not None)
            return document
        if archive.get(COMPONENT_TREE_STREAM) is not None:
            document = _retain_source(
                _assembly_document(self, archive, data, label, settings),
                data,
            )
            _validate_source_suffix(label, True)
            return document
        model = _native_part_model(archive, settings.configuration)
        configurations = _configurations(model, settings.configuration)
        parameters = _parameters(model)
        parameter_ids = {parameter.id for parameter in parameters}
        planes = _planes(model, parameter_ids)
        sketches = _sketches(model, parameter_ids)
        selections = _selections(model)
        timeline = _timeline(model, selections)
        payloads, payload_diagnostics = _brep_payloads(archive, settings)
        brep = _typed_brep(payloads)
        solid_operation_ids = frozenset(
            _feature_id(operation.object_id)
            for operation in model.operations
            if operation.kind != "surface"
        )
        final_feature = _final_body_feature_id(timeline, solid_operation_ids)
        body_feature = _solid_body_feature(model.features)
        bodies = (
            Body(
                id="sldprt:body:1",
                name=body_feature.name if body_feature is not None else "Body 1",
                final_feature_id=final_feature,
                topology=TopologySummary(
                    solid_count=1 if solid_operation_ids else 0,
                    bounding_box=_bounding_box(model),
                ),
                provenance=(
                    _feature_provenance(body_feature)
                    if body_feature is not None
                    else None
                ),
                attributes=frozen_mapping(
                    {
                        "native_object_id": (
                            body_feature.object_id if body_feature is not None else None
                        ),
                        "parasolid_payload_ids": tuple(
                            payload.id for payload in payloads
                        ),
                    }
                ),
            ),
        )
        diagnostics = (
            tuple(
                Diagnostic(
                    code="sldprt.native_record_unresolved",
                    message=message,
                    severity=Severity.INFO,
                )
                for message in model.diagnostics
            )
            + payload_diagnostics
        )
        document = CadDocument(
            source=CadSource(
                format_id=_FORMAT_ID,
                path=label,
                sha256=hashlib.sha256(data).hexdigest(),
                container_version=str(archive.format_version),
                attributes=frozen_mapping(
                    {
                        "file_id": archive.file_id,
                        "stream_count": len(archive.records),
                    }
                ),
            ),
            configurations=configurations,
            parameters=parameters,
            support_planes=planes,
            sketches=sketches,
            selections=selections,
            feature_timeline=timeline,
            bodies=bodies,
            brep=brep,
            brep_payloads=payloads,
            diagnostics=diagnostics,
            capabilities=self.info.capabilities,
            metadata=frozen_mapping(
                {
                    "adapter": _FORMAT_ID,
                    "file_id": archive.file_id,
                    "native_class_names": tuple(
                        dict.fromkeys(item.name for item in model.classes)
                    ),
                    "native_feature_count": len(model.features),
                    "native_name_record_count": len(model.names),
                    "native_scalar_count": len(model.scalars),
                    "stream_names": tuple(record.name for record in archive.records),
                }
            ),
            units=UnitSystem.MILLIMETER,
        )
        document.assert_valid()
        _validate_source_suffix(label, False)
        return _retain_source(document, data)

    def supports(self, document: CadDocument, destination: Destination) -> bool:
        path = _destination_path(destination)
        if path is None:
            return is_binary_destination(destination)
        expected = SUFFIX_BY_FORMAT_ID[_destination_format_id(document)]
        return path.suffix.casefold() == expected

    def write(
        self,
        document: CadDocument,
        destination: Destination,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        settings = options or WriteOptions()
        if settings.validate:
            document.assert_valid()
        expected_format = (
            _ASSEMBLY_FORMAT_ID if document.assembly is not None else _FORMAT_ID
        )
        if (
            settings.destination_format is not None
            and settings.destination_format != expected_format
        ):
            raise ValueError(
                f"{settings.destination_format} does not support this document kind"
            )
        if not self.supports(document, destination):
            expected = SUFFIX_BY_FORMAT_ID[expected_format].upper()
            raise ValueError(f"SOLIDWORKS destination must end in {expected}")
        path = _destination_path(destination)
        format_id = _destination_format_id(document)
        preserved = (
            None
            if (
                document.assembly is not None
                and (
                    settings.values.get("portable") is True
                    or settings.values.get("bundle_member") is True
                )
            )
            else _preserved_source(document, path)
        )
        diagnostics = document.diagnostics
        required = _required_capabilities(document)
        referenced_files_written = 0
        bundle = _AssemblyBundle({}, {}, False)
        portable_carrier = False
        if preserved is None:
            template = _source_template(document, path)
            if settings.values.get("allow_non_native", True) is not True:
                kind = "edited native-backed" if template is not None else "source-less"
                raise SldprtFormatError(
                    f"{kind} SOLIDWORKS writing requires "
                    "WriteOptions(values={'allow_non_native': True})"
                )
            if (
                document.assembly is not None
                and path is not None
                and settings.values.get("portable") is True
            ):
                bundle = _assembly_bundle(document, path, settings)
            portable_carrier = (
                document.assembly is not None
                and settings.values.get("portable") is True
                and settings.values.get("allow_carrier") is True
                and not bundle.complete
            )
            configured_bundle_names = settings.values.get("bundle_names")
            selected_bundle_names = (
                bundle.names
                if bundle.names
                else (
                    configured_bundle_names
                    if isinstance(configured_bundle_names, Mapping)
                    else {}
                )
            )
            generated = _generated_streams(
                document,
                template,
                selected_bundle_names,
            )
            if portable_carrier:
                generated = replace(
                    generated,
                    compatibility=(
                        "native-source-with-kit-neutral"
                        if generated.compatibility == "native-template"
                        else generated.compatibility
                    ),
                    application_usable=False,
                    vendor_loadable=False,
                )
            transfers = _solidworks_transfers(
                required,
                generated.native_capabilities,
                generated.mixed_capabilities,
            )
            streams = generated.streams
            streams[KIT_NATIVE_STREAM] = _native_attestation_bytes(
                streams,
                generated.compatibility,
                generated.application_usable,
                generated.vendor_loadable,
                transfers,
                generated.native_brep,
            )
            file_id = (
                SldprtArchive.from_bytes(template).file_id
                if template is not None
                else None
            )
            data = build_sldprt(streams, file_id=file_id, template=template)
            mode = "template" if template is not None else "generated"
            native_content = (
                "source-preserved"
                if template is not None
                else (
                    (
                        "native-metadata-and-neutral-brep"
                        if document.assembly is None
                        else "neutral-brep"
                    )
                    if generated.native_brep == "generated"
                    else (
                        (
                            "native-metadata-and-parasolid-import"
                            if document.assembly is None
                            else "parasolid-import"
                        )
                        if generated.native_brep == "preserved"
                        else (
                            "native-metadata" if document.assembly is None else "none"
                        )
                    )
                )
            )
            if not generated.application_usable:
                diagnostics = (
                    *diagnostics,
                    Diagnostic(
                        code="sldprt.neutral_write",
                        message=(
                            "one or more neutral edits are retained in the Kit "
                            "stream because their native SOLIDWORKS records could "
                            "not be reproduced"
                        ),
                        severity=Severity.WARNING,
                    ),
                )
            if generated.unexpressed:
                diagnostics = (
                    *diagnostics,
                    Diagnostic(
                        code="sldasm.unexpressed_native_records",
                        message=(
                            "generated SOLIDWORKS assembly does not express "
                            + ", ".join(generated.unexpressed)
                        ),
                        severity=Severity.WARNING,
                    ),
                )
            if generated.reader_gaps:
                diagnostics = (
                    *diagnostics,
                    Diagnostic(
                        code="sldasm.vendor_reader_rejects",
                        message=(
                            "SOLIDWORKS assembly is not reported loadable because "
                            "the vendor reader contract is unsatisfied: "
                            + ", ".join(generated.reader_gaps)
                        ),
                        severity=Severity.WARNING,
                    ),
                )
            if generated.donor_notes:
                diagnostics = (
                    *diagnostics,
                    Diagnostic(
                        code=(
                            "sldprt.donor_partial"
                            if generated.vendor_loadable
                            else "sldprt.donor_declined"
                        ),
                        message=(
                            (
                                "native SOLIDWORKS feature records omit "
                                if generated.vendor_loadable
                                else "native SOLIDWORKS feature records were not "
                                "written because "
                            )
                            + "; ".join(generated.donor_notes)
                        ),
                        severity=Severity.WARNING,
                    ),
                )
            if generated.native_brep.startswith("unsupported:"):
                diagnostics = (
                    *diagnostics,
                    Diagnostic(
                        code="sldprt.native_brep_unsupported",
                        message=generated.native_brep.removeprefix("unsupported:"),
                        severity=Severity.WARNING,
                    ),
                )
            native_brep = generated.native_brep
            compatibility = generated.compatibility
            application_usable = generated.application_usable
            vendor_loadable = generated.vendor_loadable
        else:
            data = preserved
            mode = "exact"
            native_content = "exact"
            native_brep = "exact"
            compatibility = _replay_compatibility(data)
            attestation = _native_attestation(data)
            if compatibility == "native-exact":
                transfers = tuple(
                    CapabilityTransfer(capability, TransferMode.NATIVE)
                    for capability in sorted(required, key=lambda value: value.value)
                )
                application_usable = True
                vendor_loadable = True
            elif attestation is not None:
                transfers = _attested_transfers(attestation, required)
                application_usable = attestation["application_usable"]
                vendor_loadable = attestation["vendor_loadable"]
                native_brep = str(attestation.get("native_brep", "template"))
                native_content = "source-preserved"
            else:
                transfers = _solidworks_transfers(required, frozenset())
                application_usable = False
                vendor_loadable = False
        neutral_edits_are_native = all(
            transfer.mode is TransferMode.NATIVE
            or transfer.carrier_reason is CarrierReason.TARGET_UNSUPPORTED
            for transfer in transfers
        )
        output = _write_destination(destination, data, settings.overwrite)
        for target, payload in bundle.payloads.items():
            _write_destination(target, payload, settings.overwrite)
        referenced_files_written = len(bundle.payloads)
        archive = SldprtArchive.from_bytes(data, output or "<memory>")
        requirements = (
            ("referenced SOLIDWORKS component files",)
            if document.assembly is not None
            and not bundle.complete
            and not portable_carrier
            else ()
        )
        return WriteResult(
            path=output,
            adapter=format_id,
            bytes_written=len(data),
            diagnostics=diagnostics,
            metadata=frozen_mapping(
                {
                    "mode": mode,
                    "format_id": format_id,
                    "compatibility": compatibility,
                    "native_content": native_content,
                    "neutral_edits_are_native": neutral_edits_are_native,
                    "vendor_loadable": vendor_loadable,
                    "application_usable": application_usable,
                    "native_geometry": native_brep
                    in {"exact", "generated", "preserved", "patched", "template"},
                    "native_brep": native_brep,
                    "native_history": (
                        Capability.PARAMETRIC_HISTORY not in required
                        or Capability.PARAMETRIC_HISTORY
                        in {
                            transfer.capability
                            for transfer in transfers
                            if transfer.mode is TransferMode.NATIVE
                        }
                    ),
                    "native_assembly": (
                        document.assembly is not None
                        and Capability.ASSEMBLIES
                        in {
                            transfer.capability
                            for transfer in transfers
                            if transfer.mode is TransferMode.NATIVE
                        }
                    ),
                    "native_self_contained": (
                        application_usable
                        and (document.assembly is None or bundle.complete)
                    ),
                    "referenced_files_written": referenced_files_written,
                    "container_version": archive.format_version,
                    "file_id": archive.file_id,
                    "stream_count": len(archive.records),
                    "runtime": "python-stdlib",
                }
            ),
            transfers=transfers,
            requirements=requirements,
            application_usable=application_usable,
            vendor_loadable=vendor_loadable,
        )


def read_sldprt(
    source: Source,
    *,
    configuration: str | None = None,
    include_brep: bool = True,
    include_tessellation: bool = True,
    strict: bool = True,
) -> CadDocument:
    return SldprtAdapter().read(
        source,
        ReadOptions(
            configuration=configuration,
            include_brep=include_brep,
            include_tessellation=include_tessellation,
            strict=strict,
        ),
    )


def write_sldprt(
    document: CadDocument,
    destination: Destination,
    *,
    overwrite: bool = False,
    validate: bool = True,
    allow_non_native: bool = True,
) -> WriteResult:
    return SldprtAdapter().write(
        document,
        destination,
        WriteOptions(
            overwrite=overwrite,
            validate=validate,
            values=frozen_mapping({"allow_non_native": allow_non_native}),
        ),
    )


def _embedded_document(
    adapter: SldprtAdapter,
    archive: SldprtArchive,
    data: bytes,
    label: str,
    embedded: bytes,
    settings: ReadOptions,
) -> CadDocument:
    try:
        document = CadDocument.from_json(embedded.decode("utf-8"))
    except (UnicodeDecodeError, TypeError, ValueError) as exc:
        raise SldprtFormatError("embedded Kit document is invalid") from exc
    configurations = document.configurations
    if settings.configuration is not None:
        matches = {
            item.id
            for item in configurations
            if settings.configuration in {item.id, item.name}
        }
        if not matches:
            raise SldprtFormatError(
                f"configuration {settings.configuration!r} is unavailable"
            )
        configurations = tuple(
            replace(item, active=item.id in matches) for item in configurations
        )
    original = document.source
    format_id = _ASSEMBLY_FORMAT_ID if document.assembly is not None else _FORMAT_ID
    metadata = dict(document.metadata)
    metadata.update(
        {
            "adapter": format_id,
            "file_id": archive.file_id,
            "stream_names": tuple(record.name for record in archive.records),
            "embedded_source_format_id": original.format_id,
            "embedded_source_path": original.path,
            "embedded_source_sha256": original.sha256,
            "solidworks.container_compatibility": _replay_compatibility(data),
        }
    )
    document = replace(
        document,
        source=CadSource(
            format_id=format_id,
            path=label,
            sha256=hashlib.sha256(data).hexdigest(),
            container_version=str(archive.format_version),
            attributes=frozen_mapping(
                {
                    "file_id": archive.file_id,
                    "stream_count": len(archive.records),
                    "embedded_source_format_id": original.format_id,
                }
            ),
        ),
        configurations=configurations,
        metadata=frozen_mapping(metadata),
    )
    document = filter_document(
        document,
        include_brep=settings.include_brep,
        include_tessellation=settings.include_tessellation,
        keep_payload_records=False,
    )
    if settings.strict:
        document.assert_valid()
    return _retain_source(
        document,
        data,
        retain_capabilities=True,
        read_options=settings,
    )


def _document_without_source(document: CadDocument) -> CadDocument:
    return replace(
        document,
        metadata=frozen_mapping(
            {
                key: value
                for key, value in document.metadata.items()
                if key not in _SOURCE_KEYS
            }
        ),
    )


def _semantic_sha256(document: CadDocument) -> str:
    value = _semantic_document(document).to_json(indent=None).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _semantic_document(document: CadDocument) -> CadDocument:
    envelope_indexes = source_payload_indexes(document)
    payloads = tuple(
        replace(
            payload,
            data=None,
            sha256=(
                hashlib.sha256(payload.data).hexdigest()
                if payload.data is not None
                else payload.sha256
            ),
        )
        for index, payload in enumerate(document.brep_payloads)
        if index not in envelope_indexes
    )
    assembly = document.assembly
    if assembly is not None:
        assembly = replace(
            assembly,
            documents=tuple(
                replace(
                    item,
                    document=(
                        _semantic_document(item.document)
                        if isinstance(item.document, CadDocument)
                        else item.document
                    ),
                )
                for item in assembly.documents
            ),
        )
    return replace(
        document,
        source=CadSource("", "", ""),
        brep_payloads=payloads,
        metadata=semantic_metadata(document.metadata),
        assembly=assembly,
    )


def _retain_source(
    document: CadDocument,
    data: bytes,
    *,
    retain_capabilities: bool = False,
    read_options: ReadOptions | None = None,
) -> CadDocument:
    capabilities = document.capabilities
    selected_options = read_options or ReadOptions()
    portable = _document_without_source(document)
    portable = replace(
        portable,
        metadata=with_wrapper_metadata(portable.metadata, _WRAPPER_METADATA_KEYS),
    )
    selected_capabilities = (
        retained_capabilities(
            portable,
            capabilities,
            include_brep=selected_options.include_brep,
            include_tessellation=selected_options.include_tessellation,
        )
        if retain_capabilities
        else infer_capabilities(portable, roundtrip_metadata=True)
    )
    portable = replace(portable, capabilities=selected_capabilities)
    metadata = dict(portable.metadata)
    metadata.update(
        {
            _SOURCE_BYTES_KEY: bytes(data),
            _SOURCE_SHA256_KEY: hashlib.sha256(data).hexdigest(),
            _SOURCE_SEMANTIC_SHA256_KEY: _semantic_sha256(portable),
            _SOURCE_FORMAT_KEY: document.source.format_id,
        }
    )
    return replace(
        portable,
        metadata=with_wrapper_metadata(metadata, _WRAPPER_METADATA_KEYS),
    )


def _is_geometry_brep_payload(payload: BrepPayload) -> bool:
    return payload.role == PayloadRole.BREP and payload.data is not None


def _preserved_source(document: CadDocument, destination: Path | None) -> bytes | None:
    data = _source_template(document, destination)
    if data is None:
        return None
    semantic = document.metadata.get(_SOURCE_SEMANTIC_SHA256_KEY)
    if semantic != _semantic_sha256(document):
        return None
    if _replay_compatibility(
        data
    ) == "native-exact" and not _native_source_matches_document(document, data):
        return None
    return data


def _source_template(document: CadDocument, destination: Path | None) -> bytes | None:
    data = document.metadata.get(_SOURCE_BYTES_KEY)
    if not isinstance(data, bytes):
        return None
    expected = document.metadata.get(_SOURCE_SHA256_KEY)
    if expected != hashlib.sha256(data).hexdigest():
        return None
    source_format = document.metadata.get(_SOURCE_FORMAT_KEY)
    if destination is not None:
        expected_suffix = SUFFIX_BY_FORMAT_ID.get(source_format)
        if expected_suffix is None or destination.suffix.casefold() != expected_suffix:
            return None
    try:
        SldprtArchive.from_bytes(data)
    except SldprtFormatError:
        return None
    return data


def _native_source_matches_document(document: CadDocument, data: bytes) -> bool:
    active = tuple(
        configuration.name
        for configuration in document.configurations
        if configuration.active
    )
    if len(active) > 1:
        return False
    source = BytesIO(data)
    source.name = document.source.path
    try:
        candidate = SldprtAdapter().read(
            source,
            ReadOptions(
                configuration=active[0] if active else None,
                include_brep=Capability.BREP in document.capabilities,
                include_tessellation=Capability.TESSELLATION in document.capabilities,
            ),
        )
    except (OSError, SldprtFormatError, TypeError, ValueError):
        return False
    return _semantic_sha256(candidate) == _semantic_sha256(document)


def _required_capabilities(document: CadDocument) -> frozenset[Capability]:
    return document.capabilities | infer_capabilities(
        document,
        roundtrip_metadata=Capability.ROUNDTRIP_METADATA in document.capabilities,
    )


def _assembly_bundle(
    document: CadDocument, destination: Path, settings: WriteOptions
) -> _AssemblyBundle:
    assembly = document.assembly
    if assembly is None:
        return _AssemblyBundle({}, {}, False)
    documents = {component.id: component.document for component in assembly.documents}
    definitions = tuple(
        definition
        for definition in assembly.definitions
        if definition.id != assembly.root_definition_id
    )
    names: dict[str, str] = {}
    payloads: dict[Path, bytes] = {}
    used = {destination.name.casefold()}
    complete = True
    targets: list[tuple[ComponentDefinition, CadDocument, str, Path]] = []
    for definition in definitions:
        key = definition.document_id or definition.id
        if key in names:
            names[definition.id] = names[key]
            continue
        component = documents.get(definition.document_id)
        if (
            not isinstance(component, CadDocument)
            and str(definition.kind) == ComponentKind.ASSEMBLY.value
        ):
            component = _nested_assembly_document(document, definition.id)
        if not isinstance(component, CadDocument):
            complete = False
            continue
        suffix = SUFFIX_BY_FORMAT_ID[
            _ASSEMBLY_FORMAT_ID if component.assembly is not None else _FORMAT_ID
        ]
        source_name = PureWindowsPath(
            str(
                definition.attributes.get("native_source_path")
                or definition.source_path
                or component.source.path
            )
        ).name
        candidate = Path(source_name).name if source_name else ""
        if Path(candidate).suffix.casefold() != suffix:
            candidate = f"{definition.name or key}{suffix}"
        stem = Path(candidate).stem or "component"
        index = 1
        while candidate.casefold() in used:
            index += 1
            candidate = f"{stem}-{index}{suffix}"
        used.add(candidate.casefold())
        target = (destination.parent / candidate).resolve()
        TargetName = str(target)
        names[key] = TargetName
        names[definition.id] = TargetName
        if definition.document_id:
            names[definition.document_id] = TargetName
        targets.append((definition, component, candidate, target))
    available_names = {
        PureWindowsPath(NameValue).name.casefold() for NameValue in names.values()
    }
    for definition, component, candidate, target in targets:
        buffer = BytesIO()
        values = dict(settings.values)
        values["portable"] = False
        values["bundle_member"] = component.assembly is not None
        values["bundle_names"] = frozen_mapping(names)
        result = SldprtAdapter().write(
            component,
            buffer,
            WriteOptions(
                overwrite=True,
                validate=settings.validate,
                values=frozen_mapping(values),
            ),
        )
        payload = buffer.getvalue()
        if target.exists() and not settings.overwrite:
            if target.read_bytes() != payload:
                raise FileExistsError(target)
        else:
            payloads[target] = payload
        native_result = (
            result.application_usable
            and result.vendor_loadable
            and (
                not result.requirements
                or _bundle_requirements_satisfied(component, available_names)
            )
        )
        if not native_result:
            complete = False
    if any(
        (definition.document_id or definition.id) not in names
        for definition in definitions
    ):
        complete = False
    return _AssemblyBundle(
        frozen_mapping(names),
        frozen_mapping(payloads),
        complete,
    )


def _nested_assembly_document(
    document: CadDocument,
    root_definition_id: str,
) -> CadDocument | None:
    assembly = document.assembly
    if assembly is None:
        return None
    definitions = {definition.id: definition for definition in assembly.definitions}
    root = definitions.get(root_definition_id)
    if root is None or str(root.kind) != ComponentKind.ASSEMBLY.value:
        return None
    reachable = {root_definition_id}
    pending = [root_definition_id]
    while pending:
        owner_id = pending.pop()
        for instance in assembly.instances:
            if instance.owner_definition_id != owner_id:
                continue
            if instance.definition_id not in reachable:
                reachable.add(instance.definition_id)
                pending.append(instance.definition_id)
    selected_definitions = tuple(
        (
            replace(definition, document_id="")
            if definition.id == root_definition_id
            else definition
        )
        for definition in assembly.definitions
        if definition.id in reachable
    )
    selected_instances = tuple(
        instance
        for instance in assembly.instances
        if instance.owner_definition_id in reachable
        and instance.definition_id in reachable
    )
    selected_mates = tuple(
        mate for mate in assembly.mates if mate.owner_definition_id in reachable
    )
    entity_ids = {entity_id for mate in selected_mates for entity_id in mate.entity_ids}
    selected_entities = tuple(
        entity
        for entity in assembly.mate_entities
        if entity.id in entity_ids and entity.owner_definition_id in reachable
    )
    selected_groups = tuple(
        group
        for group in assembly.mate_groups
        if group.owner_definition_id in reachable
    )
    document_ids = {
        definition.document_id
        for definition in selected_definitions
        if definition.id != root_definition_id and definition.document_id
    }
    selected_documents = tuple(
        component for component in assembly.documents if component.id in document_ids
    )
    selected_mesh_ids = {
        mesh_id
        for definition in selected_definitions
        for mesh_id in definition.mesh_ids
    }
    selected_payloads: list[BrepPayload] = []
    native_root_id = _native_id(root_definition_id, "sldasm:definition:")
    if native_root_id is not None:
        for payload in document.brep_payloads:
            if (
                payload.role is not PayloadRole.ASSEMBLY_STRUCTURE
                or payload.format_id.casefold() != "solidworks.mates"
                or payload.data is None
            ):
                continue
            try:
                owner_id = int(payload.attributes.get("owner_definition_id", -1))
            except (TypeError, ValueError):
                continue
            if owner_id != native_root_id:
                continue
            source_stream = payload.source_stream.rsplit("::", 1)[-1]
            selected_payloads.append(replace(payload, source_stream=source_stream))
    nested_assembly = AssemblyData(
        root_definition_id=root_definition_id,
        definitions=selected_definitions,
        instances=selected_instances,
        documents=selected_documents,
        mate_entities=selected_entities,
        mates=selected_mates,
        mate_groups=selected_groups,
        attributes=assembly.attributes,
    )
    source_path = root.source_path or f"{root.name}.SLDASM"
    nested = replace(
        document,
        source=CadSource(_ASSEMBLY_FORMAT_ID, source_path, ""),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep=None,
        brep_payloads=tuple(selected_payloads),
        meshes=tuple(mesh for mesh in document.meshes if mesh.id in selected_mesh_ids),
        assembly=nested_assembly,
        metadata=frozen_mapping(
            {
                key: value
                for key, value in document.metadata.items()
                if key not in _SOURCE_KEYS
            }
        ),
    )
    return replace(
        nested,
        capabilities=infer_capabilities(
            nested,
            roundtrip_metadata=Capability.ROUNDTRIP_METADATA in document.capabilities,
        ),
    )


def _bundle_requirements_satisfied(
    document: CadDocument, available_names: set[str]
) -> bool:
    if document.assembly is None:
        return True
    for definition in document.assembly.definitions:
        if definition.id == document.assembly.root_definition_id:
            continue
        source = str(
            definition.attributes.get("native_source_path") or definition.source_path
        )
        name = PureWindowsPath(source).name.casefold()
        if not name or name not in available_names:
            return False
    return True


def _solidworks_transfers(
    required: frozenset[Capability],
    native: frozenset[Capability],
    mixed: frozenset[Capability] = frozenset(),
) -> tuple[CapabilityTransfer, ...]:
    return tuple(
        CapabilityTransfer(
            capability,
            (
                TransferMode.NATIVE
                if capability in native
                else (
                    TransferMode.MIXED if capability in mixed else TransferMode.CARRIER
                )
            ),
            (
                None
                if capability in native
                else (
                    CarrierReason.TARGET_UNSUPPORTED
                    if capability in mixed
                    or capability in _TARGET_UNSUPPORTED_CAPABILITIES
                    else CarrierReason.WRITER_UNIMPLEMENTED
                )
            ),
        )
        for capability in sorted(required, key=lambda value: value.value)
    )


def _native_stream_sha256(streams: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name in sorted(
        (
            name
            for name in streams
            if name not in {KIT_DOCUMENT_STREAM, KIT_NATIVE_STREAM}
        ),
        key=lambda value: (value.casefold(), value),
    ):
        encoded = name.encode("utf-8")
        data = streams[name]
        digest.update(struct.pack(">I", len(encoded)))
        digest.update(encoded)
        digest.update(struct.pack(">Q", len(data)))
        digest.update(data)
    return digest.hexdigest()


def _native_attestation_bytes(
    streams: Mapping[str, bytes],
    compatibility: str,
    application_usable: bool,
    vendor_loadable: bool,
    transfers: tuple[CapabilityTransfer, ...],
    native_brep: str,
) -> bytes:
    embedded = streams[KIT_DOCUMENT_STREAM]
    document = CadDocument.from_json(embedded.decode("utf-8"))
    value = {
        "version": 2,
        "compatibility": compatibility,
        "application_usable": application_usable,
        "vendor_loadable": vendor_loadable,
        "native_brep": native_brep,
        "native_stream_sha256": _native_stream_sha256(streams),
        "embedded_sha256": hashlib.sha256(embedded).hexdigest(),
        "semantic_sha256": _semantic_sha256(document),
        "transfers": [
            {
                "capability": transfer.capability.value,
                "mode": transfer.mode.value,
                "carrier_reason": (
                    transfer.carrier_reason.value
                    if transfer.carrier_reason is not None
                    else None
                ),
            }
            for transfer in transfers
        ],
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _native_attestation(data: bytes) -> dict[str, Any] | None:
    try:
        archive = SldprtArchive.from_bytes(data)
        raw = archive.require(KIT_NATIVE_STREAM)
        embedded = archive.require(KIT_DOCUMENT_STREAM)
        value = json.loads(raw.decode("utf-8"))
        document = CadDocument.from_json(embedded.decode("utf-8"))
    except (KeyError, SldprtFormatError, TypeError, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(value, dict) or value.get("version") != 2:
        return None
    if value.get("embedded_sha256") != hashlib.sha256(embedded).hexdigest():
        return None
    if value.get("semantic_sha256") != _semantic_sha256(document):
        return None
    if value.get("native_stream_sha256") != _native_stream_sha256(archive.streams):
        return None
    if not isinstance(value.get("application_usable"), bool) or not isinstance(
        value.get("vendor_loadable"), bool
    ):
        return None
    if value["application_usable"] and not value["vendor_loadable"]:
        return None
    compatibility = value.get("compatibility")
    if (
        not isinstance(compatibility, str)
        or compatibility not in _ATTESTED_COMPATIBILITIES
    ):
        return None
    records = value.get("transfers")
    if not isinstance(records, list):
        return None
    try:
        parsed = tuple(
            CapabilityTransfer(
                Capability(record["capability"]),
                TransferMode(record["mode"]),
                (
                    CarrierReason(record["carrier_reason"])
                    if record.get("carrier_reason") is not None
                    else None
                ),
            )
            for record in records
            if isinstance(record, dict)
        )
    except (KeyError, TypeError, ValueError):
        return None
    if len(parsed) != len(records) or len({item.capability for item in parsed}) != len(
        parsed
    ):
        return None
    proof = _attested_native_proof(document, archive, compatibility)
    if proof is None:
        return None
    expected_transfers = _solidworks_transfers(
        _required_capabilities(document),
        proof.native_capabilities,
        proof.mixed_capabilities,
    )
    if (
        compatibility != proof.compatibility
        or value["application_usable"] is not proof.application_usable
        or value["vendor_loadable"] is not proof.vendor_loadable
        or value.get("native_brep") != proof.native_brep
        or parsed != expected_transfers
    ):
        return None
    value["parsed_transfers"] = parsed
    return value


def _attested_native_proof(
    document: CadDocument, archive: SldprtArchive, compatibility: str
) -> _GeneratedStreams | None:
    streams = archive.streams
    before = _native_stream_sha256(streams)
    bundle_names = _attested_generated_bundle_names(document, archive)
    try:
        if compatibility in {
            "native-brep-with-kit-neutral",
            "native-metadata-with-kit-neutral",
        }:
            proof = _generated_streams(document, bundle_names=bundle_names)
        elif KEYWORDS_STREAM in streams and RESOLVED_FEATURES_STREAM in streams:
            proof = _patch_native_template(document, streams, {})
        else:
            proof = _generated_streams(document, bundle_names=bundle_names)
    except (KeyError, SldprtFormatError, TypeError, ValueError, struct.error):
        return None
    if _native_stream_sha256(proof.streams) != before:
        return None
    return proof


def _attested_generated_bundle_names(
    document: CadDocument,
    archive: SldprtArchive,
) -> Mapping[str, str]:
    assembly = document.assembly
    if assembly is None or COMPONENT_TREE_STREAM not in archive.streams:
        return {}
    model_name = PureWindowsPath(document.source.path).stem
    try:
        encoding = encode_native_assembly(
            assembly,
            document.configurations,
            model_name or assembly.definition(assembly.root_definition_id).name,
        )
        native = decode_native_assembly(archive, include_tessellation=False)
    except (KeyError, SldprtFormatError, TypeError, ValueError, struct.error):
        return {}
    definitions = {item.object_id: item for item in native.definitions}
    result: dict[str, str] = {}
    for definition in assembly.definitions:
        if definition.id == assembly.root_definition_id:
            continue
        native_id = encoding.definition_ids.get(definition.id)
        target = definitions.get(native_id) if native_id is not None else None
        if target is None or not target.source_path:
            continue
        name = PureWindowsPath(target.source_path).name
        result[definition.id] = name
        if definition.document_id:
            result[definition.document_id] = name
    return result


def _attested_transfers(
    attestation: Mapping[str, Any], required: frozenset[Capability]
) -> tuple[CapabilityTransfer, ...]:
    parsed = attestation.get("parsed_transfers")
    if not isinstance(parsed, tuple):
        return _solidworks_transfers(required, frozenset())
    by_capability = {item.capability: item for item in parsed}
    if set(by_capability) != set(required):
        return _solidworks_transfers(required, frozenset())
    return tuple(
        by_capability[capability]
        for capability in sorted(required, key=lambda value: value.value)
    )


def _replay_compatibility(data: bytes) -> str:
    archive = SldprtArchive.from_bytes(data)
    if KIT_DOCUMENT_STREAM not in archive.streams:
        return "native-exact"
    attestation = _native_attestation(data)
    return (
        str(attestation["compatibility"])
        if attestation is not None
        else "kit-neutral-only"
    )


# this assembles independently serialized solidworks document streams
def _generated_streams(
    document: CadDocument,
    template: bytes | None = None,
    bundle_names: Mapping[str, str] | None = None,
) -> _GeneratedStreams:
    portable = _document_without_source(document)
    if isinstance(document.source.attributes.get("embedded_source_format_id"), str):
        envelope_indexes = source_payload_indexes(document)
        portable = replace(
            portable,
            brep_payloads=tuple(
                payload
                for index, payload in enumerate(portable.brep_payloads)
                if index not in envelope_indexes
            ),
        )
    embedded = portable.to_json(indent=None).encode("utf-8")
    if template is not None:
        streams = SldprtArchive.from_bytes(template).streams
        streams[KIT_DOCUMENT_STREAM] = embedded
        return _patch_native_template(document, streams, bundle_names or {})
    configuration = next(
        (item.name for item in portable.configurations if item.active),
        portable.configurations[0].name if portable.configurations else "Default",
    )
    model_name = PureWindowsPath(portable.source.path).stem
    streams = {
        **_solidworks_package_streams(),
        SOLIDWORKS_STREAM: _solidworks_xml(model_name, configuration),
        KIT_DOCUMENT_STREAM: embedded,
    }
    encoding: NativeAssemblyEncoding | None = None
    part_capabilities: frozenset[Capability] = frozenset()
    mixed_capabilities: frozenset[Capability] = frozenset()
    part_partition: bytes | None = None
    PartObjectIds: Mapping[str, int] = {}
    part_application_usable = False
    part_vendor_loadable = False
    part_donor_notes: tuple[str, ...] = ()
    assembly_envelope_complete = False
    assembly_notes: tuple[str, ...] = ()
    if portable.assembly is None:
        part = encode_native_part(portable, model_name)
        streams.update(part.envelope_streams)
        streams[KEYWORDS_STREAM] = part.keywords
        streams[FEATURES_STREAM] = part.features
        streams.update(
            {
                f"Contents/Config-{index}-ResolvedFeatures": lane
                for index, lane in part.configuration_lanes
            }
        )
        if part.kit_resolved_features is not None:
            streams[KIT_RESOLVED_STREAM] = part.kit_resolved_features
        part_capabilities = part.native_capabilities
        mixed_capabilities = part.mixed_capabilities
        part_partition = part.partition
        PartObjectIds = part.object_ids
        part_application_usable = part.application_usable
        part_vendor_loadable = part.vendor_loadable
        part_donor_notes = part.donor_notes
    else:
        RootName = portable.assembly.definition(
            portable.assembly.root_definition_id
        ).name
        AssemblyName = RootName or model_name or "Assembly"
        encoding = encode_native_assembly(
            portable.assembly,
            portable.configurations,
            AssemblyName,
            bundle_names,
        )
        preserved_mates, mates_complete = _preserved_generated_mate_streams(
            portable,
            encoding,
        )
        if mates_complete:
            encoding = replace(
                encoding,
                mate_streams=preserved_mates,
                mates_complete=True,
                unsupported_mate_ids=(),
                generated_mate_ids=(),
            )
        envelope = encode_native_assembly_envelope(
            portable,
            AssemblyName,
            _generated_occurrence_labels(portable.assembly),
            tuple(mate.name for mate in portable.assembly.mates),
        )
        streams.update(envelope.streams)
        streams[COMPONENT_TREE_STREAM] = encoding.component_tree
        streams.update(encoding.mate_streams)
        streams.update(AsmCoreStreams(portable.assembly, encoding, AssemblyName))
        assembly_envelope_complete = envelope.envelope_complete
        assembly_notes = _generated_assembly_notes(encoding, envelope, streams)
    if part_partition is not None:
        payload = part_partition
        native_brep = "generated"
    else:
        payload, native_brep = _parasolid_payload(portable, PartObjectIds)
    if payload is not None:
        streams[PARTITION_STREAM] = payload
    NativeCaps = set(
        _generated_assembly_capabilities(
            portable.assembly, encoding, streams, portable.configurations
        )
        if portable.assembly is not None and encoding is not None
        else part_capabilities
    )
    if (
        portable.assembly is not None
        and bundle_names is not None
        and all(
            DefinitionItem.id == portable.assembly.root_definition_id
            or DefinitionItem.document_id in bundle_names
            or DefinitionItem.id in bundle_names
            for DefinitionItem in portable.assembly.definitions
        )
    ):
        NativeCaps.add(Capability.COMPONENT_DOCUMENTS)
    if (
        portable.assembly is None
        and payload is not None
        and native_brep in {"generated", "preserved"}
    ):
        NativeCaps.update({Capability.BREP, Capability.NATIVE_PAYLOADS})
    native_capabilities = frozenset(NativeCaps)
    proof_transfers = _solidworks_transfers(
        _required_capabilities(portable),
        native_capabilities,
        mixed_capabilities,
    )
    native_assembly_records = (
        portable.assembly is not None
        and assembly_envelope_complete
        and encoding is not None
        and encoding.structure_complete
        and Capability.ASSEMBLIES in native_capabilities
    )
    if portable.assembly is None:
        vendor_loadable = part_vendor_loadable
        native_records_usable = part_application_usable
    else:
        vendor_loadable = native_assembly_records and not _assembly_reader_gaps(streams)
        native_records_usable = vendor_loadable and (
            not portable.assembly.mates
            or Capability.ASSEMBLY_MATES in native_capabilities
        )
    application_usable = native_records_usable and all(
        transfer.mode is TransferMode.NATIVE
        or transfer.carrier_reason is CarrierReason.TARGET_UNSUPPORTED
        for transfer in proof_transfers
    )
    return _GeneratedStreams(
        streams,
        native_brep,
        native_capabilities,
        (
            "native-brep-with-kit-neutral"
            if native_brep in {"generated", "preserved"}
            else (
                "native-metadata-with-kit-neutral"
                if portable.assembly is None
                else (
                    "native-assembly-with-kit-neutral"
                    if native_assembly_records
                    else "kit-neutral-only"
                )
            )
        ),
        application_usable,
        vendor_loadable,
        mixed_capabilities,
        assembly_notes,
        part_donor_notes,
        (_assembly_reader_gaps(streams) if portable.assembly is not None else ()),
    )


def _assembly_reader_gaps(
    streams: Mapping[str, bytes],
    donor: Mapping[str, bytes] | None = None,
    rewritable: frozenset[str] = frozenset(),
) -> tuple[str, ...]:
    gaps = [
        f"absent_vendor_stream:{name}"
        for name in _ASSEMBLY_READER_REQUIRED_STREAMS
        if name not in streams
    ]
    if donor is None:
        gaps.extend(
            f"vendor_rejected_record:{name}"
            for name in _VENDOR_REJECTED_ASSEMBLY_RECORDS
            if name in streams
        )
        return tuple(gaps)
    gaps.extend(
        f"donor_stream_absent:{name}"
        for name in _ASSEMBLY_DONOR_CARRIED_STREAMS
        if name not in donor
    )
    for name in sorted(set(streams) | set(donor)):
        if name in rewritable:
            continue
        if name not in donor:
            gaps.append(f"donor_stream_added:{name}")
        elif name not in streams:
            gaps.append(f"donor_stream_removed:{name}")
        elif streams[name] != donor[name]:
            gaps.append(f"donor_stream_rewritten:{name}")
    return tuple(gaps)


def _generated_assembly_notes(
    encoding: NativeAssemblyEncoding,
    envelope: NativeAssemblyEnvelope,
    streams: Mapping[str, bytes],
) -> tuple[str, ...]:
    counts: Counter[str] = Counter()
    for reasons in encoding.unsupported_mate_reasons.values():
        counts.update(reasons)
    for reasons in encoding.generated_mate_losses.values():
        counts.update(reasons)
    notes = [f"{reason}:{count}" for reason, count in sorted(counts.items())]
    if envelope.omitted_object_names:
        notes.append(
            f"header_object_name_unencodable:{len(envelope.omitted_object_names)}"
        )
    if not encoding.structure_complete:
        notes.append("component_structure_incomplete:1")
    if encoding.generated_mate_ids:
        notes.append(
            f"vendor_unread_synthesised_mate:{len(encoding.generated_mate_ids)}"
        )
    notes.extend(
        f"absent_vendor_stream:{name}"
        for name in _UNSYNTHESISED_ASSEMBLY_STREAMS
        if name not in streams
    )
    return tuple(notes)


def _generated_occurrence_labels(assembly: AssemblyData) -> tuple[str, ...]:
    labels: list[str] = []
    for index, instance in enumerate(assembly.instances):
        reference = _generated_reference_number(instance, index + 1)
        suffix = f"-{reference}"
        base_name = (
            instance.name[: -len(suffix)]
            if instance.name.endswith(suffix)
            else instance.name
        )
        labels.append(f"{base_name}{suffix}")
    return tuple(labels)


# native history uses the direct root occurrence and its resolved file path
def AsmCoreStreams(
    AssemblyValue: AssemblyData,
    EncodingValue: NativeAssemblyEncoding,
    ModelName: str,
) -> Mapping[str, bytes]:
    DirectItems = AssemblyValue.children(AssemblyValue.root_definition_id)
    if not 1 <= len(DirectItems) <= 2:
        raise SldprtFormatError(
            "first-principles assembly history requires one or two direct components"
        )
    XmlRoot = ET.fromstring(EncodingValue.component_tree)
    XmlSpace = {"sw": "http://www.solidworks.com/sw2003/schema"}
    OccurNames = _generated_occurrence_labels(AssemblyValue)
    CoreItems: list[AsmCoreItem] = []
    ConfigName = ""
    for InstanceItem in DirectItems:
        InstanceIndex = AssemblyValue.instances.index(InstanceItem)
        TargetId = EncodingValue.definition_ids[InstanceItem.definition_id]
        ModelNode = next(
            (
                NodeItem
                for NodeItem in XmlRoot.findall(
                    "sw:swModelList/sw:swModel", XmlSpace
                )
                if NodeItem.attrib.get("id") == str(TargetId)
            ),
            None,
        )
        if ModelNode is None:
            raise SldprtFormatError(
                "assembly component model is absent from native tree"
            )
        FileId = ModelNode.attrib.get("swFileRef", "")
        FileNode = next(
            (
                NodeItem
                for NodeItem in XmlRoot.findall("sw:swHeader/sw:swFile", XmlSpace)
                if NodeItem.attrib.get("id") == FileId
            ),
            None,
        )
        if FileNode is None or not (
            CompPath := FileNode.attrib.get("swPath", "")
        ):
            raise SldprtFormatError(
                "assembly component file is absent from native tree"
            )
        InstanceConfig = InstanceItem.configuration_name or AssemblyValue.definition(
            InstanceItem.definition_id
        ).configuration_name
        if ConfigName and (InstanceConfig or "Default") != ConfigName:
            raise SldprtFormatError(
                "direct assembly components use different configurations"
            )
        ConfigName = InstanceConfig or "Default"
        CoreItems.append(AsmCoreItem(OccurNames[InstanceIndex], CompPath))
    return EncodeAsmCore(ModelName, ConfigName, tuple(CoreItems))


def _preserved_generated_mate_streams(
    document: CadDocument,
    encoding: NativeAssemblyEncoding,
) -> tuple[dict[str, bytes], bool]:
    assembly = document.assembly
    if assembly is None or encoding.mates_complete:
        return dict(encoding.mate_streams), encoding.mates_complete
    root_id = encoding.definition_ids[assembly.root_definition_id]
    candidates: dict[str, tuple[BrepPayload, NativeMateList]] = {}
    for payload in document.brep_payloads:
        if (
            payload.role is not PayloadRole.ASSEMBLY_STRUCTURE
            or payload.format_id.casefold() != "solidworks.mates"
            or payload.data is None
            or "::" in payload.source_stream
        ):
            continue
        leaf = payload.source_stream.replace("\\", "/").rsplit("/", 1)[-1]
        if (
            leaf.casefold() != MATES_STREAM_NAME.casefold()
            and not leaf.casefold().endswith(MATES_STREAM_SUFFIX.casefold())
        ):
            continue
        try:
            owner_id = int(payload.attributes.get("owner_definition_id", -1))
            decoded = decode_mate_list(payload.data, payload.source_stream, owner_id)
        except (SldprtFormatError, TypeError, ValueError, struct.error):
            continue
        if owner_id != root_id or payload.source_stream in candidates:
            continue
        candidates[payload.source_stream] = (payload, decoded)
    if not candidates:
        return {}, False
    payload_ids = {payload.id for payload, _ in candidates.values()}
    desired_payload_ids = {
        str(value)
        for value in (
            *(mate.attributes.get("native_payload_id") for mate in assembly.mates),
            *(
                group.attributes.get("native_payload_id")
                for group in assembly.mate_groups
            ),
        )
        if isinstance(value, str) and value
    }
    if desired_payload_ids != payload_ids:
        return {}, False
    desired_mates = {
        (
            str(mate.attributes.get("native_payload_id", "")),
            _generated_integer(mate.attributes.get("native_record_offset")),
        ): mate
        for mate in assembly.mates
    }
    desired_entities = {entity.id: entity for entity in assembly.mate_entities}
    matched_mates: set[str] = set()
    matched_group_offsets: set[tuple[str, int]] = set()
    for payload, mate_list in candidates.values():
        for native_mate in mate_list.mates:
            key = (payload.id, native_mate.record_offset)
            if native_mate.kind == "group":
                matched_group_offsets.add(key)
                continue
            mate = desired_mates.get(key)
            if mate is None or not _preserved_native_mate_matches(
                mate,
                native_mate,
                desired_entities,
            ):
                return {}, False
            matched_mates.add(mate.id)
    if matched_mates != {mate.id for mate in assembly.mates}:
        return {}, False
    expected_group_offsets = {
        (
            str(group.attributes.get("native_payload_id", "")),
            _generated_integer(group.attributes.get(name)),
        )
        for group in assembly.mate_groups
        for name in ("start_record_offset", "end_record_offset")
    }
    if matched_group_offsets != expected_group_offsets:
        return {}, False
    return {
        payload.source_stream: bytes(payload.data) for payload, _ in candidates.values()
    }, True


def _preserved_native_mate_matches(
    mate: MateConstraint,
    native: NativeMate,
    entities: Mapping[str, MateEntity],
) -> bool:
    if (
        mate.name != native.name
        or mate.kind != _neutral_mate_kind(native.kind)
        or mate.alignment != _neutral_mate_alignment(native)
        or _mate_parameter_value(mate.value)
        != _mate_parameter_value(_neutral_mate_value(native))
        or mate.suppressed
        or not mate.driving
        or mate.parameter_ids
        or len(mate.entity_ids) != len(native.entities)
    ):
        return False
    for entity_id, native_entity in zip(mate.entity_ids, native.entities):
        entity = entities.get(entity_id)
        if entity is None:
            return False
        component_path = entity.attributes.get("component_path", "")
        persistent = entity.attributes.get("persistent_references", ())
        if (
            component_path != native_entity.component_path
            or persistent != native_entity.persistent_references
            or entity.source_entity_id
            != (
                native_entity.persistent_references[-1]
                if native_entity.persistent_references
                else ""
            )
        ):
            return False
    return True


def _generated_assembly_capabilities(
    assembly: AssemblyData,
    encoding: NativeAssemblyEncoding,
    streams: Mapping[str, bytes],
    configurations: Sequence[Configuration],
) -> frozenset[Capability]:
    try:
        native = decode_native_assembly(
            SldprtArchive.from_bytes(build_sldprt(dict(streams))),
            include_tessellation=False,
        )
    except (KeyError, SldprtFormatError, TypeError, ValueError, struct.error):
        return frozenset()
    result: set[Capability] = set()
    if encoding.structure_complete and _generated_assembly_structure_matches(
        assembly,
        encoding,
        native,
    ):
        result.add(Capability.ASSEMBLIES)
        if len(assembly.definitions) > 1:
            result.add(Capability.EXTERNAL_REFERENCES)
    OrderedConfigs = tuple(
        sorted(
            configurations,
            key=lambda ConfigurationItem: (
                not ConfigurationItem.active,
                configurations.index(ConfigurationItem),
            ),
        )
    )
    if tuple(
        (ConfigurationItem.name, ConfigurationItem.active)
        for ConfigurationItem in OrderedConfigs
    ) == tuple(
        (ConfigurationItem.name, ConfigurationItem.most_recent)
        for ConfigurationItem in native.configurations
    ):
        result.add(Capability.CONFIGURATIONS)
    if (
        encoding.mates_complete
        and not encoding.generated_mate_ids
        and assembly.mates
        and len(native.mate_lists) == len(encoding.mate_streams)
        and all(item.declared_count == len(item.mates) for item in native.mate_lists)
        and sum(
            1
            for item in native.mate_lists
            for mate in item.mates
            if mate.kind != "group"
        )
        == len(assembly.mates)
    ):
        result.add(Capability.ASSEMBLY_MATES)
    return frozenset(result)


def _generated_assembly_structure_matches(
    assembly: AssemblyData,
    encoding: NativeAssemblyEncoding,
    native: NativeAssembly,
) -> bool:
    definitions = {item.object_id: item for item in native.definitions}
    if native.root_definition_id != encoding.definition_ids.get(
        assembly.root_definition_id
    ):
        return False
    if set(definitions) != set(encoding.definition_ids.values()):
        return False
    for source in assembly.definitions:
        target = definitions.get(encoding.definition_ids[source.id])
        if target is None:
            return False
        expected_kind = (
            "ASSEMBLY" if str(source.kind) == ComponentKind.ASSEMBLY.value else "PART"
        )
        if (
            target.name != source.name
            or target.document_type != expected_kind
            or target.configuration_name != (source.configuration_name or "Default")
        ):
            return False
        if source.bounding_box is not None:
            expected_box = tuple(
                value / 1000.0
                for value in (
                    source.bounding_box.minimum.x,
                    source.bounding_box.minimum.y,
                    source.bounding_box.minimum.z,
                    source.bounding_box.maximum.x,
                    source.bounding_box.maximum.y,
                    source.bounding_box.maximum.z,
                )
            )
            if target.bounding_box_m != expected_box:
                return False
    occurrences = {item.object_id: item for item in native.occurrences}
    if set(occurrences) != set(encoding.occurrence_ids.values()):
        return False
    by_owner: defaultdict[str, list[tuple[int, int, ComponentInstance]]] = defaultdict(
        list
    )
    for index, source in enumerate(assembly.instances):
        by_owner[source.owner_definition_id].append((source.order, index, source))
        target = occurrences.get(encoding.occurrence_ids[source.id])
        if target is None:
            return False
        reference = _generated_reference_number(source, index + 1)
        suffix = f"-{reference}"
        base_name = (
            source.name[: -len(suffix)] if source.name.endswith(suffix) else source.name
        )
        configuration_id = _generated_integer(source.configuration_id)
        if (
            target.name != base_name
            or target.reference_number != reference
            or target.owner_definition_id
            != encoding.definition_ids[source.owner_definition_id]
            or target.definition_id != encoding.definition_ids[source.definition_id]
            or target.configuration_name
            != (
                source.configuration_name
                or assembly.definition(source.definition_id).configuration_name
                or "Default"
            )
            or target.configuration_id != configuration_id
            or target.transform != _native_assembly_matrix(source.transform)
            or target.suppressed != source.suppressed
            or target.hidden != source.hidden
            or target.flexible != source.flexible
            or target.exclude_from_bom != source.exclude_from_bom
            or (target.feature_id == 24) != source.fixed
        ):
            return False
    native_by_owner: defaultdict[int, list[NativeAssemblyOccurrence]] = defaultdict(
        list
    )
    for target in native.occurrences:
        native_by_owner[target.owner_definition_id].append(target)
    for owner_id, values in by_owner.items():
        expected = [
            encoding.occurrence_ids[item.id]
            for _, _, item in sorted(values, key=lambda value: (value[0], value[1]))
        ]
        actual = [
            item.object_id
            for item in native_by_owner[encoding.definition_ids[owner_id]]
        ]
        if actual != expected:
            return False
    return True


def _generated_reference_number(instance: ComponentInstance, fallback: int) -> int:
    for value in (
        instance.reference_number,
        instance.attributes.get("native_reference_number"),
    ):
        if isinstance(value, bool):
            continue
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number > 0:
            return number
    match = re.search(r"-(\d+)$", instance.name)
    return int(match.group(1)) if match is not None else fallback


def _generated_integer(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _patch_native_template(
    document: CadDocument,
    streams: dict[str, bytes],
    bundle_names: Mapping[str, str],
) -> _GeneratedStreams:
    native = set[Capability]()
    original_streams = dict(streams)
    if KEYWORDS_STREAM not in streams or RESOLVED_FEATURES_STREAM not in streams:
        return _GeneratedStreams(
            streams,
            "template",
            frozenset(),
            "native-source-with-kit-neutral",
            False,
            False,
        )
    resolved_stream = _resolved_features_stream(streams, RESOLVED_FEATURES_STREAM)
    original_model = decode_native_model(
        streams[KEYWORDS_STREAM],
        streams[resolved_stream],
        resolved_stream=resolved_stream,
    )
    keywords = _keywords_root(streams[KEYWORDS_STREAM])
    resolved = bytearray(streams[resolved_stream])
    keywords_changed = _patch_feature_names(
        document, original_model, keywords[1], resolved
    )
    keywords_changed = (
        _patch_parameters(document, original_model, keywords[1], resolved)
        or keywords_changed
    )
    _patch_support_planes(document, original_model, resolved)
    _patch_sketch_geometry(document, original_model, resolved)
    if keywords_changed:
        streams[KEYWORDS_STREAM] = _keywords_bytes(*keywords)
    streams[resolved_stream] = bytes(resolved)
    patched_model = decode_native_model(
        streams[KEYWORDS_STREAM],
        streams[resolved_stream],
        resolved_stream=resolved_stream,
    )
    patched_parameters = _parameters(patched_model)
    patched_planes = _planes(
        patched_model, {parameter.id for parameter in patched_parameters}
    )
    patched_sketches = _sketches(
        patched_model, {parameter.id for parameter in patched_parameters}
    )
    patched_selections = _selections(patched_model)
    patched_timeline = _timeline(patched_model, patched_selections)
    original_parameters = _parameters(original_model)
    original_planes = _planes(
        original_model, {parameter.id for parameter in original_parameters}
    )
    original_sketches = _sketches(
        original_model, {parameter.id for parameter in original_parameters}
    )
    original_selections = _selections(original_model)
    original_timeline = _timeline(original_model, original_selections)
    if _parameter_values(document.parameters) == _parameter_values(patched_parameters):
        native.add(Capability.PARAMETERS)
        if not any(
            parameter.expression is not None for parameter in document.parameters
        ):
            native.add(Capability.EXPRESSIONS)
    if _plane_values(document.support_planes) == _plane_values(patched_planes):
        native.add(Capability.SUPPORT_PLANES)
    desired_sketch_values = _sketch_values(document.sketches)
    if desired_sketch_values == _sketch_values(
        patched_sketches
    ) or desired_sketch_values == _sketch_values(original_sketches):
        native.add(Capability.EDITABLE_SKETCHES)
    if _feature_values(
        document.feature_timeline, document.parameters
    ) == _feature_values(
        patched_timeline, patched_parameters
    ) and _native_feature_definitions_unchanged(
        document.feature_timeline, original_timeline
    ):
        native.add(Capability.PARAMETRIC_HISTORY)
    if _selection_values(document.selections) == _selection_values(original_selections):
        native.add(Capability.SELECTIONS)
    original_configurations = _configurations(original_model, None)
    if _configuration_values(document.configurations) == _configuration_values(
        original_configurations
    ):
        native.add(Capability.CONFIGURATIONS)
    if document.assembly is None and _body_values(
        document.bodies
    ) == _native_body_values(original_model, original_timeline):
        native.add(Capability.BODY_STRUCTURE)
    native_brep, brep_native, payloads_native = _patch_template_brep(
        document, streams, original_streams
    )
    if brep_native:
        native.add(Capability.BREP)
    if payloads_native:
        native.add(Capability.NATIVE_PAYLOADS)
    if document.assembly is None and document.meshes == ():
        native.add(Capability.TESSELLATION)
    divergences: tuple[str, ...] = ()
    if document.assembly is not None:
        patch = _patch_native_assembly(document, streams, bundle_names)
        native.update(patch.capabilities)
        divergences = patch.divergences
        if Capability.COMPONENT_DOCUMENTS in patch.capabilities and brep_native:
            native.add(Capability.NATIVE_PAYLOADS)
    required = _required_capabilities(document)
    blockers = required - native - _TARGET_UNSUPPORTED_CAPABILITIES
    usable = not blockers
    if document.assembly is None:
        return _GeneratedStreams(
            streams,
            native_brep,
            frozenset(native),
            "native-template" if usable else "native-source-with-kit-neutral",
            usable,
            usable,
        )
    reader_gaps = (
        _assembly_reader_gaps(
            streams, original_streams, _ASSEMBLY_REWRITABLE_DONOR_STREAMS
        )
        + divergences
    )
    loadable = not reader_gaps
    return _GeneratedStreams(
        streams,
        native_brep,
        frozenset(native),
        "native-template" if usable and loadable else "native-source-with-kit-neutral",
        usable and loadable,
        loadable,
        reader_gaps=reader_gaps,
    )


def _keywords_root(data: bytes) -> tuple[bytes, ET.Element, bytes]:
    start = data.find(b"<?xml")
    if start < 0:
        start = data.find(b"<")
    if start < 0:
        raise SldprtFormatError("keyword stream contains no XML document")
    prefix = data[:start]
    raw = data[start:]
    trailing = (
        b"\r\n" if raw.endswith(b"\r\n") else b"\n" if raw.endswith(b"\n") else b""
    )
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SldprtFormatError(f"invalid keyword XML: {exc}") from exc
    return prefix, root, trailing


def _keywords_bytes(prefix: bytes, root: ET.Element, trailing: bytes) -> bytes:
    return prefix + ET.tostring(root, encoding="utf-8", xml_declaration=True) + trailing


def _xml_elements_by_id(root: ET.Element) -> dict[int, ET.Element]:
    result: dict[int, ET.Element] = {}
    for element in root.iter():
        raw = element.attrib.get("id")
        if raw is None:
            continue
        try:
            result[int(raw)] = element
        except ValueError:
            continue
    return result


def _native_id(value: str, prefix: str) -> int | None:
    if not value.startswith(prefix):
        return None
    try:
        return int(value.removeprefix(prefix).split(":", 1)[0])
    except ValueError:
        return None


def _patch_feature_names(
    document: CadDocument,
    model: NativeModel,
    root: ET.Element,
    resolved: bytearray,
) -> bool:
    desired: dict[int, str] = {}
    for feature in document.feature_timeline:
        native_id = _native_id(feature.id, "sldprt:feature:")
        if native_id is not None:
            desired[native_id] = feature.name
    for plane in document.support_planes:
        native_id = _native_id(plane.id, "sldprt:plane:")
        if native_id is not None and native_id not in desired:
            desired[native_id] = plane.name
    for sketch in document.sketches:
        native_id = _native_id(sketch.id, "sldprt:sketch:")
        if native_id is not None and native_id not in desired:
            desired[native_id] = sketch.name
    elements = _xml_elements_by_id(root)
    features = {feature.object_id: feature for feature in model.features}
    changed = False
    for object_id, name in desired.items():
        feature = features.get(object_id)
        if feature is None or name == feature.name:
            continue
        record = next(
            (
                candidate
                for candidate in model.names
                if candidate.object_id == object_id
                and candidate.offset == feature.native_offset
            ),
            None,
        )
        encoded = name.encode("utf-16le")
        if record is None or len(encoded) != len(feature.name.encode("utf-16le")):
            continue
        start = record.text_end - len(feature.name.encode("utf-16le"))
        if bytes(resolved[start : record.text_end]).decode("utf-16le") != feature.name:
            continue
        resolved[start : record.text_end] = encoded
        element = elements.get(object_id)
        if element is not None:
            element.attrib["Name"] = name
        changed = True
    return changed


def _parameter_millimeters(parameter: Parameter) -> float | None:
    value = parameter.value.value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or parameter.value.kind is not ValueKind.LENGTH:
        return None
    factor = {
        "": 1.0,
        "mm": 1.0,
        "millimeter": 1.0,
        "millimeters": 1.0,
        "cm": 10.0,
        "m": 1000.0,
        "in": 25.4,
        "inch": 25.4,
        "inches": 25.4,
    }.get(parameter.value.unit.casefold())
    return number * factor if factor is not None else None


def _dimension_text(source: str, millimeters: float) -> str:
    value = format(millimeters, ".15g")
    return _NUMBER_TEXT.sub(value, source, count=1)


def _patch_parameters(
    document: CadDocument,
    model: NativeModel,
    root: ET.Element,
    resolved: bytearray,
) -> bool:
    original = {parameter.id: parameter for parameter in _parameters(model)}
    desired = {parameter.id: parameter for parameter in document.parameters}
    if set(original) != set(desired):
        return False
    elements = _xml_elements_by_id(root)
    dimensions: dict[str, tuple[int, NativeDimension]] = {}
    for feature in model.features:
        for dimension, parameter_id in _parameter_entries(
            feature.object_id, feature.dimensions
        ):
            dimensions[parameter_id] = feature.object_id, dimension
    changed = False
    for parameter_id, target in desired.items():
        source = original[parameter_id]
        target_mm = _parameter_millimeters(target)
        source_mm = _parameter_millimeters(source)
        if (
            target_mm is None
            or source_mm is None
            or math.isclose(target_mm, source_mm, rel_tol=1e-12, abs_tol=1e-12)
        ):
            continue
        if (
            target.name != source.name
            or target.role != source.role
            or target.owner_id != source.owner_id
            or target.expression != source.expression
        ):
            continue
        record = dimensions.get(parameter_id)
        if record is None or record[1].native_offset is None:
            continue
        object_id, dimension = record
        struct.pack_into("<d", resolved, dimension.native_offset, target_mm / 1000.0)
        element = elements.get(object_id)
        if element is None:
            continue
        occurrence = (
            int(parameter_id.rsplit(":", 1)[-1]) - 1
            if parameter_id.rsplit(":", 1)[-1].isdigit() and parameter_id.count(":") > 3
            else 0
        )
        matches = tuple(
            child
            for child in element
            if child.tag.rsplit("}", 1)[-1] == "Dimension"
            and child.attrib.get("Name", "") == dimension.name
        )
        if occurrence < len(matches):
            matches[occurrence].text = _dimension_text(
                matches[occurrence].text or dimension.source_text,
                target_mm,
            )
            changed = True
    return changed


def _vector_values(vector: Vector3) -> tuple[float, float, float]:
    return vector.x, vector.y, vector.z


def _unit_vector(values: tuple[float, float, float]) -> bool:
    return all(math.isfinite(value) for value in values) and math.isclose(
        sum(value * value for value in values), 1.0, rel_tol=1e-9, abs_tol=1e-9
    )


def _orthonormal_transform(transform: Transform) -> bool:
    axes = (
        _vector_values(transform.x_axis),
        _vector_values(transform.y_axis),
        _vector_values(transform.z_axis),
    )
    return all(_unit_vector(axis) for axis in axes) and all(
        math.isclose(
            sum(left[index] * right[index] for index in range(3)),
            0.0,
            abs_tol=1e-9,
        )
        for left, right in ((axes[0], axes[1]), (axes[0], axes[2]), (axes[1], axes[2]))
    )


def _patch_support_planes(
    document: CadDocument, model: NativeModel, resolved: bytearray
) -> None:
    parameters = _parameters(model)
    original = {
        plane.id: plane
        for plane in _planes(model, {parameter.id for parameter in parameters})
    }
    desired = {plane.id: plane for plane in document.support_planes}
    if set(original) != set(desired):
        return
    for plane_id, target in desired.items():
        source = original[plane_id]
        if target.transform == source.transform:
            continue
        if (
            target.name != source.name
            or target.support_selection_id != source.support_selection_id
            or target.offset_parameter_id != source.offset_parameter_id
            or not _orthonormal_transform(target.transform)
        ):
            continue
        offset = source.attributes.get("native_frame_offset")
        length = source.attributes.get("native_frame_length")
        if not isinstance(offset, int) or length not in {81, 121}:
            continue
        origin = tuple(
            value / 1000.0 for value in _vector_values(target.transform.origin)
        )
        x_axis = _vector_values(target.transform.x_axis)
        y_axis = _vector_values(target.transform.y_axis)
        z_axis = _vector_values(target.transform.z_axis)
        if not all(math.isfinite(value) for value in origin):
            continue
        if length == 81:
            if (
                x_axis != (1.0, 0.0, 0.0)
                or y_axis != (0.0, 1.0, 0.0)
                or z_axis != (0.0, 0.0, 1.0)
            ):
                continue
            struct.pack_into("<3d", resolved, offset, *origin)
            struct.pack_into("<3d", resolved, offset + 57, 0.0, -origin[2], 1.0)
            continue
        struct.pack_into("<3d", resolved, offset, *origin)
        struct.pack_into("<3d", resolved, offset + 24, *z_axis)
        rows = tuple(zip(x_axis, y_axis, z_axis, strict=True))
        for index, row in enumerate(rows):
            struct.pack_into("<3d", resolved, offset + 49 + index * 24, *row)


def _coordinate_offset(data: bytes | bytearray, marker_offset: int) -> int | None:
    for relative in (56, 64):
        offset = marker_offset + relative
        if data[offset : offset + 2] == b"\x1e\x00" and offset + 18 <= len(data):
            return offset + 2
    return None


def _patch_coordinate(
    resolved: bytearray, marker_offset: int, point: tuple[float, float]
) -> bool:
    if not all(math.isfinite(value) for value in point):
        return False
    offset = _coordinate_offset(resolved, marker_offset)
    if offset is None:
        return False
    struct.pack_into("<2d", resolved, offset, point[0] / 1000.0, point[1] / 1000.0)
    return True


def _point_values(value: Vector2) -> tuple[float, float]:
    return value.x, value.y


def _patch_sketch_geometry(
    document: CadDocument, model: NativeModel, resolved: bytearray
) -> None:
    parameters = _parameters(model)
    original_sketches = _sketches(model, {parameter.id for parameter in parameters})
    original = {sketch.id: sketch for sketch in original_sketches}
    native = {_sketch_id(sketch.object_id): sketch for sketch in model.sketches}
    desired = {sketch.id: sketch for sketch in document.sketches}
    if set(original) != set(desired):
        return
    for sketch_id, target in desired.items():
        source = original[sketch_id]
        native_sketch = native[sketch_id]
        if (
            target.support_plane_id != source.support_plane_id
            or target.constraints != source.constraints
            or target.parameter_ids != source.parameter_ids
            or target.closed_profile_entity_ids != source.closed_profile_entity_ids
            or target.suppressed != source.suppressed
        ):
            continue
        source_entities = {entity.id: entity for entity in source.entities}
        target_entities = {entity.id: entity for entity in target.entities}
        if set(source_entities) != set(target_entities):
            continue
        for entity_id, target_entity in target_entities.items():
            source_entity = source_entities[entity_id]
            if target_entity.geometry == source_entity.geometry:
                continue
            if (
                target_entity.kind != source_entity.kind
                or target_entity.construction != source_entity.construction
                or target_entity.fixed != source_entity.fixed
            ):
                continue
            if isinstance(source_entity.geometry, PointGeometry) and isinstance(
                target_entity.geometry, PointGeometry
            ):
                marker_offset = _native_id(
                    entity_id, f"sldprt:sketch:{native_sketch.object_id}:native:"
                )
                if marker_offset is not None:
                    _patch_coordinate(
                        resolved,
                        marker_offset,
                        _point_values(target_entity.geometry.point),
                    )
        for profile_index, profile in enumerate(native_sketch.profiles):
            if profile.kind == "circle":
                entity_id = _profile_id(native_sketch.object_id, profile_index)
                source_entity = source_entities.get(entity_id)
                target_entity = target_entities.get(entity_id)
                if (
                    source_entity is None
                    or target_entity is None
                    or target_entity.geometry == source_entity.geometry
                    or not isinstance(target_entity.geometry, CircleGeometry)
                    or len(profile.marker_offsets) < 2
                ):
                    continue
                center = _point_values(target_entity.geometry.center)
                source_center = profile.coordinates[:2]
                source_edge = next(
                    (
                        marker.coordinates_mm
                        for marker in native_sketch.markers
                        if marker.offset == profile.marker_offsets[1]
                        and marker.coordinates_mm is not None
                    ),
                    None,
                )
                if source_edge is None or target_entity.geometry.radius <= 0.0:
                    continue
                dx = source_edge[0] - source_center[0]
                dy = source_edge[1] - source_center[1]
                length = math.hypot(dx, dy)
                if length <= 1e-12:
                    dx, dy, length = 1.0, 0.0, 1.0
                edge = (
                    center[0] + dx / length * target_entity.geometry.radius,
                    center[1] + dy / length * target_entity.geometry.radius,
                )
                _patch_coordinate(resolved, profile.marker_offsets[0], center)
                _patch_coordinate(resolved, profile.marker_offsets[1], edge)
            elif profile.kind == "rectangle":
                _patch_rectangle_profile(
                    resolved,
                    native_sketch,
                    profile_index,
                    profile,
                    target_entities,
                )


def _patch_rectangle_profile(
    resolved: bytearray,
    sketch: NativeSketch,
    profile_index: int,
    profile: NativeProfile,
    entities: Mapping[str, SketchEntity],
) -> None:
    lines: list[LineGeometry] = []
    for edge_index in range(4):
        entity = entities.get(
            _profile_edge_id(sketch.object_id, profile_index, edge_index)
        )
        if entity is None or not isinstance(entity.geometry, LineGeometry):
            return
        lines.append(entity.geometry)
    points = tuple(
        (
            _point_values(lines[0].start),
            _point_values(lines[0].end),
            _point_values(lines[1].end),
            _point_values(lines[2].end),
        )
    )[0]
    if (
        _point_values(lines[1].start) != points[1]
        or _point_values(lines[2].start) != points[2]
        or _point_values(lines[3].start) != points[3]
        or _point_values(lines[3].end) != points[0]
    ):
        return
    xs = sorted({point[0] for point in points})
    ys = sorted({point[1] for point in points})
    if len(xs) != 2 or len(ys) != 2:
        return
    x0, y0, x1, y1 = profile.coordinates
    source_corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    for marker in sketch.markers:
        if marker.coordinates_mm is None:
            continue
        for source, target in zip(source_corners, points, strict=True):
            if all(
                math.isclose(left, right, abs_tol=1e-9)
                for left, right in zip(marker.coordinates_mm, source, strict=True)
            ):
                _patch_coordinate(resolved, marker.offset, target)
                break


def _round_number(value: float) -> float:
    return round(value, 10)


def _parameter_values(parameters: Sequence[Parameter]) -> tuple[Any, ...]:
    return tuple(
        (
            parameter.id,
            parameter.name,
            (
                _round_number(value)
                if (value := _parameter_millimeters(parameter)) is not None
                else parameter.value
            ),
            parameter.role,
            parameter.expression,
            parameter.owner_id,
        )
        for parameter in parameters
    )


def _transform_values(transform: Transform) -> tuple[float, ...]:
    return tuple(
        _round_number(value)
        for vector in (
            transform.origin,
            transform.x_axis,
            transform.y_axis,
            transform.z_axis,
        )
        for value in _vector_values(vector)
    )


def _plane_values(planes: Sequence[SupportPlane]) -> tuple[Any, ...]:
    return tuple(
        (
            plane.id,
            plane.name,
            _transform_values(plane.transform),
            plane.support_selection_id,
            plane.offset_parameter_id,
        )
        for plane in planes
    )


def _geometry_values(geometry: Any) -> Any:
    if isinstance(geometry, PointGeometry):
        return "point", tuple(
            _round_number(value) for value in _point_values(geometry.point)
        )
    if isinstance(geometry, LineGeometry):
        return (
            "line",
            tuple(_round_number(value) for value in _point_values(geometry.start)),
            tuple(_round_number(value) for value in _point_values(geometry.end)),
        )
    if isinstance(geometry, CircleGeometry):
        return (
            "circle",
            tuple(_round_number(value) for value in _point_values(geometry.center)),
            _round_number(geometry.radius),
        )
    return geometry


def _sketch_values(sketches: Sequence[Sketch]) -> tuple[Any, ...]:
    return tuple(
        (
            sketch.id,
            sketch.name,
            sketch.support_plane_id,
            tuple(
                (
                    entity.id,
                    entity.kind,
                    _geometry_values(entity.geometry),
                    entity.construction,
                    entity.fixed,
                )
                for entity in sketch.entities
            ),
            tuple(
                (
                    constraint.id,
                    constraint.kind,
                    constraint.references,
                    constraint.parameter_id,
                    constraint.driving,
                    constraint.suppressed,
                )
                for constraint in sketch.constraints
            ),
            sketch.parameter_ids,
            sketch.closed_profile_entity_ids,
            sketch.suppressed,
        )
        for sketch in sketches
    )


def _definition_value(
    definition: Any, parameter_value: ParameterValue | None = None
) -> Any:
    if isinstance(definition, ExtrusionFeature):
        length = parameter_value or definition.length
        return (
            "extrusion",
            _round_number(float(length.value)),
            length.kind,
            length.unit,
            definition.end_condition,
            definition.reversed,
        )
    if isinstance(definition, FilletFeature):
        radius = parameter_value or definition.radius
        return (
            "fillet",
            _round_number(float(radius.value)),
            radius.kind,
            radius.unit,
        )
    if isinstance(definition, NativeFeatureDefinition):
        return "native", definition.format_id, definition.type_id
    return definition


def _feature_values(
    features: Sequence[FeatureStep], parameters: Sequence[Parameter] = ()
) -> tuple[Any, ...]:
    parameter_by_id = {parameter.id: parameter for parameter in parameters}
    return tuple(
        (
            feature.id,
            feature.name,
            feature.kind,
            feature.order,
            feature.input_feature_ids,
            feature.sketch_id,
            feature.parameter_ids,
            feature.operation,
            _definition_value(
                feature.definition,
                next(
                    (
                        parameter_by_id[parameter_id].value
                        for parameter_id in feature.parameter_ids
                        if parameter_id in parameter_by_id
                    ),
                    None,
                ),
            ),
            feature.selection_ids,
            feature.suppressed,
            feature.configuration_states,
        )
        for feature in features
    )


def _native_feature_definitions_unchanged(
    desired: Sequence[FeatureStep], original: Sequence[FeatureStep]
) -> bool:
    originals = {feature.id: feature for feature in original}
    for feature in desired:
        source = originals.get(feature.id)
        if source is None:
            return False
        if (
            isinstance(source.definition, NativeFeatureDefinition)
            and feature.definition != source.definition
        ):
            return False
    return True


def _selection_values(selections: Sequence[Selection]) -> tuple[Any, ...]:
    return tuple(
        (selection.id, selection.name, selection.path, dict(selection.query))
        for selection in selections
    )


def _configuration_values(configurations: Sequence[Configuration]) -> tuple[Any, ...]:
    return tuple(
        (
            configuration.id,
            configuration.name,
            configuration.active,
            configuration.parent_id,
            configuration.overrides,
            configuration.suppressed_feature_ids,
        )
        for configuration in configurations
    )


def _body_values(bodies: Sequence[Body]) -> tuple[Any, ...]:
    return tuple(
        (
            body.id,
            body.name,
            body.final_feature_id,
            body.topology,
            body.material_id,
        )
        for body in bodies
    )


def _native_body_values(
    model: NativeModel, timeline: tuple[FeatureStep, ...]
) -> tuple[Any, ...]:
    body_feature = _solid_body_feature(model.features)
    body = Body(
        id="sldprt:body:1",
        name=body_feature.name if body_feature is not None else "Body 1",
        final_feature_id=_final_body_feature_id(
            timeline,
            frozenset(
                _feature_id(operation.object_id) for operation in model.operations
            ),
        ),
        topology=TopologySummary(
            solid_count=1 if model.operations else 0,
            bounding_box=_bounding_box(model),
        ),
    )
    return _body_values((body,))


def _payload_values(payloads: Sequence[BrepPayload]) -> tuple[Any, ...]:
    return tuple(
        (
            payload.id,
            payload.format_id,
            payload.kind,
            payload.schema,
            payload.sha256,
            payload.data,
            payload.source_stream,
            payload.role,
            payload.file_extension,
        )
        for payload in payloads
    )


def _patch_template_brep(
    document: CadDocument,
    streams: dict[str, bytes],
    original_streams: Mapping[str, bytes],
) -> tuple[str, bool, bool]:
    archive = SldprtArchive.from_bytes(build_sldprt(original_streams))
    original_payloads, _ = _brep_payloads(archive, ReadOptions(strict=False))
    desired_indexes = source_payload_indexes(document)
    desired_payloads = tuple(
        payload
        for index, payload in enumerate(document.brep_payloads)
        if index not in desired_indexes and payload.role is PayloadRole.BREP
    )
    payloads_native = _payload_values(desired_payloads) == _payload_values(
        original_payloads
    )
    original_brep = _typed_brep(original_payloads)
    if document.brep == original_brep and payloads_native:
        return "template", True, True
    payload, state = _parasolid_payload(document)
    if payload is None:
        status = (
            state
            if state.startswith("unsupported:")
            else "unsupported:geometry has no writable Parasolid representation"
        )
        return status, False, payloads_native
    streams[PARTITION_STREAM] = payload
    return "patched", True, payloads_native


def _patch_native_assembly(
    document: CadDocument,
    streams: dict[str, bytes],
    bundle_names: Mapping[str, str],
) -> _AssemblyTemplatePatch:
    if document.assembly is None or COMPONENT_TREE_STREAM not in streams:
        return _AssemblyTemplatePatch(frozenset(), ("donor_component_tree_absent",))
    if bundle_names:
        prefix, root, trailing = _keywords_root(streams[COMPONENT_TREE_STREAM])
        path_by_file_id = {
            int(definition.attributes["native_file_id"]): (
                bundle_names.get(definition.document_id) or bundle_names[definition.id]
            )
            for definition in document.assembly.definitions
            if (definition.document_id in bundle_names or definition.id in bundle_names)
            and isinstance(definition.attributes.get("native_file_id"), int)
        }
        changed = False
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "swFile":
                continue
            try:
                file_id = int(element.attrib.get("id", ""))
            except ValueError:
                continue
            target = path_by_file_id.get(file_id)
            if target is not None and element.attrib.get("swPath") != target:
                element.attrib["swPath"] = target
                changed = True
        if changed:
            streams[COMPONENT_TREE_STREAM] = _keywords_bytes(prefix, root, trailing)
    try:
        archive = SldprtArchive.from_bytes(build_sldprt(streams))
        native = decode_native_assembly(archive, include_tessellation=True)
    except SldprtFormatError:
        return _AssemblyTemplatePatch(frozenset(), ("donor_component_tree_unreadable",))
    donor_divergences = _diverged_donor_records(document.assembly, native)
    rewritten_instances = _patch_assembly_instances(document.assembly, native, streams)
    if rewritten_instances:
        try:
            archive = SldprtArchive.from_bytes(build_sldprt(streams))
            native = decode_native_assembly(archive, include_tessellation=True)
        except SldprtFormatError:
            return _AssemblyTemplatePatch(
                frozenset(), ("donor_component_tree_unreadable",)
            )
    rewritten_mates = _patch_assembly_mates(
        document.assembly, native, streams, document.source.path
    )
    if rewritten_mates:
        try:
            archive = SldprtArchive.from_bytes(build_sldprt(streams))
            native = decode_native_assembly(archive, include_tessellation=True)
        except SldprtFormatError:
            return _AssemblyTemplatePatch(
                frozenset(), ("donor_component_tree_unreadable",)
            )
    result: set[Capability] = set()
    if _assembly_structure_values(
        document.assembly
    ) == _native_assembly_structure_values(native):
        result.add(Capability.ASSEMBLIES)
    definitions = {
        definition.id: definition for definition in document.assembly.definitions
    }
    document_ids = {component.id for component in document.assembly.documents}
    preserved_documents = all(
        isinstance(component.document, CadDocument)
        and _preserved_source(component.document, None) is not None
        for component in document.assembly.documents
    )
    bundled_documents = bool(document_ids) and document_ids <= set(bundle_names)
    if preserved_documents or bundled_documents:
        result.add(Capability.COMPONENT_DOCUMENTS)
        if all(
            not component.document.bodies
            or Capability.BODY_STRUCTURE in component.document.capabilities
            for component in document.assembly.documents
            if isinstance(component.document, CadDocument)
        ):
            result.add(Capability.BODY_STRUCTURE)
    if any(definition.source_path for definition in definitions.values()):
        result.add(Capability.EXTERNAL_REFERENCES)
    identity_definitions = {
        definition.object_id: definition.object_id for definition in native.definitions
    }
    identity_occurrences = {
        occurrence.object_id: occurrence.object_id for occurrence in native.occurrences
    }
    _, entities, mates, groups = _assembly_mates(
        native,
        (
            (
                native,
                archive,
                identity_definitions,
                identity_occurrences,
                document.source.path,
            ),
        ),
    )
    desired_entities = {entity.id: entity for entity in document.assembly.mate_entities}
    root_entity_ids = {entity_id for mate in mates for entity_id in mate.entity_ids}
    selected_entities = tuple(
        desired_entities[entity.id]
        for entity in entities
        if entity.id in root_entity_ids and entity.id in desired_entities
    )
    desired_mates = {mate.id: mate for mate in document.assembly.mates}
    selected_mates = tuple(
        desired_mates[mate.id] for mate in mates if mate.id in desired_mates
    )
    desired_groups = {group.id: group for group in document.assembly.mate_groups}
    selected_groups = tuple(
        desired_groups[group.id] for group in groups if group.id in desired_groups
    )
    root_mates_native = _mate_values(
        selected_entities,
        selected_mates,
        selected_groups,
    ) == _mate_values(entities, mates, groups)
    all_root_records_found = (
        len(selected_entities) == len(entities)
        and len(selected_mates) == len(mates)
        and len(selected_groups) == len(groups)
    )
    nested_mates_native = len(document.assembly.mates) == len(mates) or (
        Capability.COMPONENT_DOCUMENTS in result
    )
    if root_mates_native and all_root_records_found and nested_mates_native:
        result.add(Capability.ASSEMBLY_MATES)
    native_meshes, _ = _assembly_meshes(native)
    if _mesh_values(document.meshes) == _mesh_values(native_meshes):
        result.add(Capability.TESSELLATION)
    divergences = donor_divergences + tuple(
        f"donor_mate_diverged:{item}" for item in rewritten_mates
    )
    if Capability.ASSEMBLIES not in result and not divergences:
        divergences = ("donor_structure_diverged",)
    return _AssemblyTemplatePatch(frozenset(result), divergences)


def _patch_assembly_instances(
    assembly: AssemblyData,
    native: NativeAssembly,
    streams: dict[str, bytes],
) -> tuple[str, ...]:
    original = {instance.id: instance for instance in _assembly_instances(native)}
    desired = {instance.id: instance for instance in assembly.instances}
    if not set(original) <= set(desired):
        return ()
    prefix, root, trailing = _keywords_root(streams[COMPONENT_TREE_STREAM])
    elements: dict[int, ET.Element] = {}
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "swReference":
            continue
        try:
            elements[int(element.attrib.get("id", ""))] = element
        except ValueError:
            continue
    rewritten: list[str] = []
    for instance_id, target in desired.items():
        source = original[instance_id]
        native_id = _native_id(instance_id, "sldasm:instance:")
        element = elements.get(native_id or -1)
        if element is None:
            continue
        if (
            target.owner_definition_id != source.owner_definition_id
            or target.order != source.order
            or target.fixed != source.fixed
        ):
            continue
        instance_values = {
            "swModelRef": str(
                _native_id(target.definition_id, "sldasm:definition:")
                or element.attrib.get("swModelRef", "")
            ),
            "swReferenceNumber": target.reference_number,
            "swConfigurationName": target.configuration_name,
            "swConfigurationId": target.configuration_id,
            "swTransform": " ".join(
                format(value, ".17g")
                for value in _native_assembly_matrix(target.transform)
            ),
            "swSuppressed": _yes_text(target.suppressed),
            "swHidden": _yes_text(target.hidden),
            "swFlexible": _yes_text(target.flexible),
            "swExcludeFromBOM": _yes_text(target.exclude_from_bom),
        }
        reference_number = target.reference_number or source.reference_number
        suffix = f"-{reference_number}"
        target_name = (
            target.name[: -len(suffix)]
            if target.name.endswith(suffix)
            else source.name[: -len(f"-{source.reference_number}")]
        )
        instance_values["swName"] = target_name
        for key, value in instance_values.items():
            if element.attrib.get(key) != value:
                element.attrib[key] = value
                if instance_id not in rewritten:
                    rewritten.append(instance_id)
    if rewritten:
        streams[COMPONENT_TREE_STREAM] = _keywords_bytes(prefix, root, trailing)
    return tuple(rewritten)


def _native_assembly_matrix(matrix: Matrix4) -> tuple[float, ...]:
    values = matrix.values
    result = [0.0] * 16
    result[0], result[4], result[8], result[12] = (
        values[0],
        values[1],
        values[2],
        values[3] / 1000.0,
    )
    result[1], result[5], result[9], result[13] = (
        values[4],
        values[5],
        values[6],
        values[7] / 1000.0,
    )
    result[2], result[6], result[10], result[14] = (
        values[8],
        values[9],
        values[10],
        values[11] / 1000.0,
    )
    result[3], result[7], result[11], result[15] = (
        values[12],
        values[13],
        values[14],
        values[15],
    )
    if not all(math.isfinite(value) for value in result):
        raise SldprtFormatError("component transform contains a non-finite value")
    return tuple(result)


def _yes_text(value: bool) -> str:
    return "YES" if value else "NO"


def _patch_assembly_mates(
    assembly: AssemblyData,
    native: NativeAssembly,
    streams: dict[str, bytes],
    source_path: str,
) -> tuple[str, ...]:
    definition_map = {
        definition.object_id: definition.object_id for definition in native.definitions
    }
    occurrence_map = {
        occurrence.object_id: occurrence.object_id for occurrence in native.occurrences
    }
    _, _, original_mates, _ = _assembly_mates(
        native,
        (
            (
                native,
                SldprtArchive.from_bytes(build_sldprt(streams)),
                definition_map,
                occurrence_map,
                source_path,
            ),
        ),
    )
    original = {mate.id: mate for mate in original_mates}
    desired = {mate.id: mate for mate in assembly.mates}
    if set(original) != set(desired):
        return ()
    buffers: dict[str, bytearray] = {}
    rewritten: list[str] = []
    for mate_id, target in desired.items():
        source = original[mate_id]
        if (
            target.name != source.name
            or target.kind != source.kind
            or target.owner_definition_id != source.owner_definition_id
            or target.entity_ids != source.entity_ids
            or target.order != source.order
            or target.parameter_ids != source.parameter_ids
            or target.suppressed != source.suppressed
            or target.driving != source.driving
        ):
            continue
        parts = mate_id.split(":")
        if len(parts) != 5:
            continue
        try:
            list_index = int(parts[3])
            mate_order = int(parts[4])
        except ValueError:
            continue
        if not 0 <= list_index < len(native.mate_lists):
            continue
        mate_list = native.mate_lists[list_index]
        native_mate = next(
            (mate for mate in mate_list.mates if mate.order == mate_order), None
        )
        if native_mate is None:
            continue
        buffer = buffers.setdefault(
            mate_list.stream, bytearray(streams[mate_list.stream])
        )
        if target.value != source.value:
            values = _native_mate_values(target.value, native_mate)
            if values is not None:
                for index, native_value in enumerate(values):
                    struct.pack_into(
                        "<d",
                        buffer,
                        native_mate.dimensions[index].value_offset,
                        native_value,
                    )
                if mate_id not in rewritten:
                    rewritten.append(mate_id)
        if target.alignment != source.alignment:
            alignment_code = next(
                (
                    code
                    for code, alignment in NATIVE_MATE_ALIGNMENT_BY_CODE.items()
                    if alignment.kind == str(target.alignment)
                    or alignment.kind == getattr(target.alignment, "value", None)
                ),
                None,
            )
            offset = _native_mate_alignment_offset(buffer, native_mate)
            if alignment_code is not None and offset is not None:
                struct.pack_into("<H", buffer, offset, alignment_code)
                if mate_id not in rewritten:
                    rewritten.append(mate_id)
    for stream, buffer in buffers.items():
        streams[stream] = bytes(buffer)
    return tuple(rewritten)


def _native_mate_values(
    value: ParameterValue | None, mate: NativeMate
) -> tuple[float, ...] | None:
    if value is None or not mate.dimensions:
        return None
    if isinstance(value.value, bool) or not isinstance(value.value, (int, float)):
        return None
    number = float(value.value)
    if not math.isfinite(number):
        return None
    semantic = MATE_VALUE_SEMANTICS.get(mate.kind)
    if semantic == "length" and value.kind is ValueKind.LENGTH:
        factor = {
            "": 1.0,
            "mm": 1.0,
            "cm": 10.0,
            "m": 1000.0,
            "in": 25.4,
        }.get(value.unit.casefold())
        return (number * factor / 1000.0,) if factor is not None else None
    if semantic == "angle" and value.kind is ValueKind.ANGLE:
        factor = {"": 1.0, "rad": 1.0, "deg": math.pi / 180.0}.get(
            value.unit.casefold()
        )
        return (number * factor,) if factor is not None else None
    if (
        semantic == "ratio"
        and value.kind is ValueKind.NUMBER
        and len(mate.dimensions) >= 2
    ):
        denominator = mate.dimensions[1].value
        return number * denominator, denominator
    return None


def _native_mate_alignment_offset(
    data: bytes | bytearray, mate: NativeMate
) -> int | None:
    start = mate.record_offset
    end = start + mate.record_length
    encoded = mate.name.encode("utf-16le")
    text_start = bytes(data).find(encoded, start, end)
    if text_start < 0:
        return None
    offset = text_start + len(encoded) + 159
    return offset if offset + 2 <= end else None


def _definition_structure_values(definition: ComponentDefinition) -> tuple[Any, ...]:
    return (
        definition.id,
        definition.name,
        definition.kind,
        definition.configuration_name,
    )


def _instance_structure_values(instance: ComponentInstance) -> tuple[Any, ...]:
    return (
        instance.id,
        instance.name,
        instance.definition_id,
        instance.owner_definition_id,
        tuple(_round_number(value) for value in instance.transform.values),
        instance.order,
        instance.reference_number,
        instance.configuration_name,
        instance.configuration_id,
        instance.suppressed,
        instance.hidden,
        instance.fixed,
        instance.flexible,
        instance.exclude_from_bom,
    )


def _assembly_structure_values(assembly: AssemblyData) -> tuple[Any, ...]:
    return (
        assembly.root_definition_id,
        tuple(
            _definition_structure_values(definition)
            for definition in assembly.definitions
        ),
        tuple(_instance_structure_values(instance) for instance in assembly.instances),
    )


def _native_assembly_data(native: NativeAssembly) -> AssemblyData:
    return AssemblyData(
        _assembly_definition_id(native.root_definition_id),
        _assembly_definitions(native, {}, {}, {}, {}, "<memory>"),
        _assembly_instances(native),
    )


def _native_assembly_structure_values(native: NativeAssembly) -> tuple[Any, ...]:
    return _assembly_structure_values(_native_assembly_data(native))


def _diverged_keys(
    donor: Mapping[str, Any], desired: Mapping[str, Any]
) -> tuple[str, ...]:
    return tuple(sorted(set(donor) ^ set(desired))) + tuple(
        key for key in sorted(set(donor) & set(desired)) if donor[key] != desired[key]
    )


def _diverged_donor_records(
    assembly: AssemblyData, native: NativeAssembly
) -> tuple[str, ...]:
    donor = _native_assembly_data(native)
    names: list[str] = []
    if assembly.root_definition_id != donor.root_definition_id:
        names.append("donor_root_definition_diverged")
    if tuple(item.id for item in donor.definitions) != tuple(
        item.id for item in assembly.definitions
    ):
        names.append("donor_definition_order_diverged")
    if tuple(item.id for item in donor.instances) != tuple(
        item.id for item in assembly.instances
    ):
        names.append("donor_instance_order_diverged")
    names.extend(
        f"donor_definition_diverged:{key}"
        for key in _diverged_keys(
            {item.id: _definition_structure_values(item) for item in donor.definitions},
            {
                item.id: _definition_structure_values(item)
                for item in assembly.definitions
            },
        )
    )
    names.extend(
        f"donor_instance_diverged:{key}"
        for key in _diverged_keys(
            {item.id: _instance_structure_values(item) for item in donor.instances},
            {item.id: _instance_structure_values(item) for item in assembly.instances},
        )
    )
    return tuple(names)


def _mate_values(
    entities: Sequence[MateEntity],
    mates: Sequence[MateConstraint],
    groups: Sequence[MateGroup],
) -> tuple[Any, ...]:
    return (
        tuple(
            (
                entity.id,
                entity.owner_definition_id,
                entity.instance_path,
                entity.kind,
                entity.source_entity_id,
                entity.selection_id,
                entity.frame,
                entity.radius,
            )
            for entity in entities
        ),
        tuple(
            (
                mate.id,
                mate.name,
                mate.kind,
                mate.owner_definition_id,
                mate.entity_ids,
                mate.order,
                _mate_parameter_value(mate.value),
                mate.parameter_ids,
                mate.alignment,
                mate.suppressed,
                mate.driving,
            )
            for mate in mates
        ),
        tuple(
            (
                group.id,
                group.name,
                group.owner_definition_id,
                group.mate_ids,
                group.parent_group_id,
                group.order,
            )
            for group in groups
        ),
    )


def _mate_parameter_value(value: ParameterValue | None) -> Any:
    if (
        value is None
        or isinstance(value.value, bool)
        or not isinstance(value.value, (int, float))
    ):
        return value
    number = float(value.value)
    if value.kind is ValueKind.LENGTH:
        factor = {"": 1.0, "mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}.get(
            value.unit.casefold()
        )
        if factor is not None:
            return ValueKind.LENGTH, _round_number(number * factor)
    if value.kind is ValueKind.ANGLE:
        factor = {"": 1.0, "rad": 1.0, "deg": math.pi / 180.0}.get(
            value.unit.casefold()
        )
        if factor is not None:
            return ValueKind.ANGLE, _round_number(number * factor)
    if value.kind is ValueKind.NUMBER:
        return ValueKind.NUMBER, _round_number(number)
    return value


def _mesh_values(meshes: Sequence[Mesh]) -> tuple[Any, ...]:
    return tuple(
        (
            mesh.id,
            mesh.name,
            mesh.vertices,
            mesh.triangles,
            mesh.normals,
        )
        for mesh in meshes
    )


# this writes native parasolid geometry with solidworks feature ownership
def _parasolid_payload(
    document: CadDocument,
    ObjectIds: Mapping[str, int] | None = None,
) -> tuple[bytes | None, str]:
    candidates: list[bytes] = []
    for payload in document.brep_payloads:
        if (
            payload.role != PayloadRole.BREP
            or payload.format_id.casefold() != "parasolid"
            or payload.data is None
        ):
            continue
        try:
            decoded = decode_partition_stream(payload.data, payload.source_stream)
        except SldprtFormatError:
            continue
        candidates.extend(
            item.data for item in decoded if is_native_parasolid_payload(item.data)
        )
    if candidates:
        return encode_partition_stream(max(candidates, key=len)), "preserved"
    if document.assembly is not None:
        return None, "none"
    if document.brep is None:
        if (
            not document.feature_timeline
            and not document.sketches
            and not document.bodies
            and not document.meshes
        ):
            return encode_blank_partition_stream(), "generated"
        return encode_blank_partition_stream(), "none"
    FeatureIds: dict[str, int] = {}
    if ObjectIds:
        DesignBodies = {Body.id: Body for Body in document.bodies}
        SingleFeatureId = (
            document.bodies[0].final_feature_id if len(document.bodies) == 1 else ""
        )
        for BrepBody in document.brep.bodies:
            FeatureId = str(BrepBody.attributes.get("feature_id", ""))
            if not FeatureId and BrepBody.design_body_id in DesignBodies:
                FeatureId = DesignBodies[BrepBody.design_body_id].final_feature_id
            if not FeatureId and len(document.brep.bodies) == 1:
                FeatureId = SingleFeatureId
            NativeId = ObjectIds.get(f"feature:{FeatureId}")
            if NativeId is not None:
                FeatureIds[BrepBody.id] = NativeId
    try:
        return (
            encode_partition_stream(
                encode_brep_model(
                    document.brep,
                    solidworks_feature_ids=(
                        FeatureIds
                        if len(FeatureIds) == len(document.brep.bodies)
                        else None
                    ),
                )
            ),
            "generated",
        )
    except ParasolidWriteError as exc:
        return None, f"unsupported:{exc}"


def _solidworks_xml(model: str, configuration: str) -> bytes:
    model_value = _xml_attribute(model)
    configuration_value = _xml_attribute(configuration)
    return (
        '<?xml version="1.0"?><swSolidWorks><swModel swName="'
        f'{model_value}" swConfigurationName="{configuration_value}"/>'
        "</swSolidWorks>"
    ).encode("utf-8")


def _solidworks_package_streams() -> dict[str, bytes]:
    return {
        CONTENT_TYPES_STREAM: (
            b'<?xml version="1.0"?>\r\n'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'<Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
            b'<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            b'<Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/>'
            b"</Types>\r\n"
        ),
        RELATIONSHIPS_STREAM: (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            b'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            b'<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties" Target="docProps/custom.xml"/>'
            b"</Relationships>\r\n"
        ),
        "docProps/app.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            "<Template>Normal.dotm</Template><TotalTime>1526</TotalTime>"
            "<Application>SOLIDWORKS</Application><DocSecurity>0</DocSecurity>"
            "<Company>Dassault Systèmes SolidWorks Corporation</Company>"
            "<LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc>"
            "<HyperlinksChanged>false</HyperlinksChanged>"
            "<AppVersion>23.0000</AppVersion></Properties>\r\n"
        ).encode("utf-8"),
        "docProps/core.xml": (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            b'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            b"<dc:lastModifiedBy>Kit</dc:lastModifiedBy>"
            b"<dcterms:created>2026-08-02T17:13:26Z</dcterms:created>"
            b"<dcterms:modified>2026-08-02T17:13:27Z</dcterms:modified>"
            b"</cp:coreProperties>\r\n"
        ),
        "docProps/custom.xml": (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            b'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            b'<propertySection xmlns="" name="DocumentSummaryInformation" fmtid="{D5CDD502-2E9C-101B-9397-08002B2CF9AE}">'
            b'<property name="" pid="1" TypeID="0"><vt:i2>65001</vt:i2></property>'
            b'<property name="" pid="22" TypeID="0"><vt:bool>No</vt:bool></property>'
            b'<propertyNameDictionaryElement name="" pid="0"></propertyNameDictionaryElement>'
            b"</propertySection>"
            b'<propertySection xmlns="" name="UserDefinedProperties" fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}">'
            b'<property name="" pid="1" TypeID="0"><vt:i2>65001</vt:i2></property>'
            b'<propertyNameDictionaryElement name="" pid="0"></propertyNameDictionaryElement>'
            b"</propertySection></Properties>\r\n"
        ),
    }


def _xml_attribute(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _destination_format_id(document: CadDocument) -> str:
    return _ASSEMBLY_FORMAT_ID if document.assembly is not None else _FORMAT_ID


def _destination_path(destination: Destination) -> Path | None:
    if isinstance(destination, (str, Path)):
        return Path(destination).expanduser().resolve()
    return None


def _write_destination(
    destination: Destination, data: bytes, overwrite: bool
) -> Path | None:
    path = _destination_path(destination)
    if path is None:
        try:
            written = destination.write(data)
        except TypeError as exc:
            raise TypeError("SLDPRT destination stream must accept bytes") from exc
        if isinstance(written, int) and written != len(data):
            raise OSError("SLDPRT destination stream accepted a partial write")
        return None
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise
    return path


def _assembly_document(
    adapter: SldprtAdapter,
    archive: SldprtArchive,
    data: bytes,
    label: str,
    settings: ReadOptions,
) -> CadDocument:
    native = decode_native_assembly(archive, include_tessellation=True)
    resolved_stream = _resolved_features_stream(
        archive.streams, RESOLVED_FEATURES_STREAM
    )
    model = decode_native_model(
        archive.require(KEYWORDS_STREAM),
        archive.require(resolved_stream),
        resolved_stream=resolved_stream,
    )
    configurations = _configurations(model, settings.configuration)
    parameters = _parameters(model)
    parameter_ids = {parameter.id for parameter in parameters}
    planes = _planes(model, parameter_ids)
    sketches = _sketches(model, parameter_ids)
    selections = _selections(model)
    timeline = _timeline(model, selections)
    meshes, mesh_ids = _assembly_meshes(native)
    index = _component_file_index(label, settings)
    resolve_components = settings.values.get("resolve_components", True) is not False
    documents, document_ids, resolved_paths, document_diagnostics = _assembly_documents(
        adapter,
        native,
        index if resolve_components else {},
        settings,
    )
    definitions = _assembly_definitions(
        native,
        document_ids,
        resolved_paths,
        {document.id: document.document for document in documents},
        mesh_ids,
        label,
    )
    instances = _assembly_instances(native)
    mate_sources, source_diagnostics = _mate_sources(
        native, archive, label, index, settings
    )
    mate_payloads, mate_entities, mates, mate_groups = _assembly_mates(
        native, mate_sources
    )
    flattened_mates = _flattened_mates(native, mates)
    payload_settings = ReadOptions(
        configuration=settings.configuration,
        include_brep=settings.include_brep,
        include_tessellation=settings.include_tessellation,
        strict=False,
        values=settings.values,
    )
    brep_payloads, payload_diagnostics = _brep_payloads(archive, payload_settings)
    companion_payloads = (
        _companion_payloads(label)
        if settings.include_brep
        and settings.values.get("discover_companions", True) is not False
        else ()
    )
    unresolved = tuple(
        definition
        for definition in native.definitions
        if definition.document_type == "PART"
        and definition.object_id not in document_ids
        and definition.object_id not in mesh_ids
    )
    if unresolved and settings.strict and resolve_components:
        names = ", ".join(definition.name for definition in unresolved)
        raise SldprtFormatError(
            f"assembly component sources and tessellation are unavailable: {names}"
        )
    diagnostics = (
        tuple(
            Diagnostic(
                code="sldasm.native_record_unresolved",
                message=message,
                severity=Severity.INFO,
            )
            for message in model.diagnostics
        )
        + payload_diagnostics
        + document_diagnostics
        + source_diagnostics
    )
    path_records = _flattened_occurrences(native)
    linked_documents = {document.id: document.document for document in documents}
    linked_part_documents = tuple(
        document
        for document in documents
        if document.document.source.format_id == _FORMAT_ID
    )
    linked_assembly_documents = tuple(
        document
        for document in documents
        if document.document.source.format_id == _ASSEMBLY_FORMAT_ID
    )
    assembly = AssemblyData(
        root_definition_id=_assembly_definition_id(native.root_definition_id),
        definitions=definitions,
        instances=instances,
        documents=documents,
        mate_entities=mate_entities,
        mates=mates,
        mate_groups=mate_groups,
        attributes=frozen_mapping(
            {
                "application_version": native.application_version,
                "configurations": tuple(
                    {
                        "native_object_id": configuration.object_id,
                        "native_configuration_id": configuration.configuration_id,
                        "name": configuration.name,
                        "reference": configuration.reference,
                        "model_id": configuration.model_id,
                        "most_recent": configuration.most_recent,
                        "needs_update": configuration.needs_update,
                        "native_attributes": configuration.attributes,
                    }
                    for configuration in native.configurations
                ),
                "display_states": tuple(
                    {
                        "native_object_id": state.object_id,
                        "name": state.name,
                        "configuration_id": state.configuration_id,
                        "native_attributes": state.attributes,
                    }
                    for state in native.display_states
                ),
                "flattened_occurrences": path_records,
                "flattened_occurrence_count": len(path_records),
                "flattened_mate_occurrences": flattened_mates,
                "flattened_mate_occurrence_count": len(flattened_mates),
                "native_file_count": len(native.files),
                "native_definition_count": len(native.definitions),
                "native_instance_count": len(native.occurrences),
                "linked_document_count": len(documents),
                "linked_part_document_count": len(linked_part_documents),
                "linked_assembly_document_count": len(linked_assembly_documents),
                "linked_sketch_count": sum(
                    len(document.sketches) for document in linked_documents.values()
                ),
                "linked_feature_count": sum(
                    len(document.feature_timeline)
                    for document in linked_documents.values()
                ),
            }
        ),
    )
    document = CadDocument(
        source=CadSource(
            format_id=_ASSEMBLY_FORMAT_ID,
            path=label,
            sha256=hashlib.sha256(data).hexdigest(),
            container_version=str(archive.format_version),
            application_version=str(native.application_version),
            attributes=frozen_mapping(
                {
                    "file_id": archive.file_id,
                    "stream_count": len(archive.records),
                }
            ),
        ),
        configurations=configurations,
        parameters=parameters,
        support_planes=planes,
        sketches=sketches,
        selections=selections,
        feature_timeline=timeline,
        bodies=(),
        meshes=meshes,
        brep_payloads=(*brep_payloads, *mate_payloads, *companion_payloads),
        diagnostics=diagnostics,
        capabilities=adapter.info.capabilities,
        metadata=frozen_mapping(
            {
                "adapter": _ASSEMBLY_FORMAT_ID,
                "file_id": archive.file_id,
                "native_class_names": tuple(
                    dict.fromkeys(item.name for item in model.classes)
                ),
                "native_feature_count": len(model.features),
                "native_name_record_count": len(model.names),
                "native_scalar_count": len(model.scalars),
                "stream_names": tuple(record.name for record in archive.records),
                "assembly_definition_count": len(definitions),
                "assembly_instance_count": len(instances),
                "assembly_flattened_occurrence_count": len(path_records),
                "assembly_mate_count": len(mates),
                "assembly_flattened_mate_count": len(flattened_mates),
                "assembly_mesh_count": len(meshes),
            }
        ),
        units=UnitSystem.MILLIMETER,
        assembly=assembly,
    )
    document.assert_valid()
    return document


def _component_file_index(
    label: str, settings: ReadOptions
) -> dict[str, tuple[Path, ...]]:
    requested_root = settings.values.get("component_search_root")
    if requested_root:
        root = Path(str(requested_root)).expanduser().resolve()
    else:
        source = Path(label)
        if not source.is_file():
            return {}
        root = source.resolve().parent
    if not root.is_dir():
        return {}
    result: defaultdict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.casefold() in FORMAT_ID_BY_SUFFIX:
            result[path.name.casefold()].append(path.resolve())
    return {
        name: tuple(sorted(paths, key=lambda path: str(path).casefold()))
        for name, paths in result.items()
    }


def _resolved_component_path(
    source_path: str, index: dict[str, tuple[Path, ...]]
) -> Path | None:
    native = PureWindowsPath(source_path)
    candidates = index.get(native.name.casefold(), ())
    if not candidates:
        return None
    native_parts = tuple(part.casefold() for part in native.parts)

    def score(candidate: Path) -> tuple[int, str]:
        candidate_parts = tuple(part.casefold() for part in candidate.parts)
        matches = 0
        for left, right in zip(reversed(native_parts), reversed(candidate_parts)):
            if left != right:
                break
            matches += 1
        return matches, str(candidate).casefold()

    return max(candidates, key=score)


def _assembly_documents(
    adapter: SldprtAdapter,
    native: NativeAssembly,
    index: dict[str, tuple[Path, ...]],
    settings: ReadOptions,
) -> tuple[
    tuple[ComponentDocument, ...],
    dict[int, str],
    dict[int, Path],
    tuple[Diagnostic, ...],
]:
    if not index:
        return (), {}, {}, ()
    root_id = native.root_definition_id
    definitions_by_path: defaultdict[Path, list[NativeAssemblyDefinition]] = (
        defaultdict(list)
    )
    resolved_paths: dict[int, Path] = {}
    diagnostics: list[Diagnostic] = []
    for definition in native.definitions:
        if definition.object_id == root_id:
            continue
        resolved = _resolved_component_path(definition.source_path, index)
        if resolved is None:
            diagnostics.append(
                Diagnostic(
                    code="sldasm.component_source_missing",
                    message=f"component source is unavailable: {definition.source_path}",
                    severity=Severity.INFO,
                    attributes=frozen_mapping(
                        {
                            "native_definition_id": definition.object_id,
                            "configuration": definition.configuration_name,
                        }
                    ),
                )
            )
            continue
        resolved_paths[definition.object_id] = resolved
        definitions_by_path[resolved].append(definition)
    documents: list[ComponentDocument] = []
    document_ids: dict[int, str] = {}
    for resolved, definitions in sorted(
        definitions_by_path.items(), key=lambda item: str(item[0]).casefold()
    ):
        representative = definitions[0]
        values = dict(settings.values)
        values["resolve_components"] = False
        values["discover_companions"] = False
        options = ReadOptions(
            configuration=representative.configuration_name or None,
            include_brep=settings.include_brep,
            include_tessellation=representative.document_type == "ASSEMBLY",
            strict=settings.strict,
            values=frozen_mapping(values),
        )
        try:
            document = adapter.read(resolved, options)
        except (OSError, SldprtFormatError, TypeError, ValueError) as exc:
            if settings.strict:
                raise
            diagnostics.append(
                Diagnostic(
                    code="sldasm.component_decode_failed",
                    message=f"cannot decode {resolved}: {exc}",
                    severity=Severity.WARNING,
                    attributes=frozen_mapping(
                        {
                            "native_definition_ids": tuple(
                                definition.object_id for definition in definitions
                            )
                        }
                    ),
                )
            )
            continue
        document_id = f"sldasm:document:{document.source.sha256[:20]}"
        documents.append(ComponentDocument(document_id, document))
        for definition in definitions:
            document_ids[definition.object_id] = document_id
    return tuple(documents), document_ids, resolved_paths, tuple(diagnostics)


def _assembly_meshes(
    native: NativeAssembly,
) -> tuple[tuple[Mesh, ...], dict[int, str]]:
    definition_by_path = {
        occurrence.path.casefold(): occurrence.definition_id
        for occurrence in native.occurrence_paths
    }
    occurrence_by_id = {
        occurrence.object_id: occurrence for occurrence in native.occurrences
    }
    identity = {object_id: object_id for object_id in occurrence_by_id}
    definition_by_id = {
        definition.object_id: definition for definition in native.definitions
    }
    result: list[Mesh] = []
    mesh_ids: dict[int, str] = {}
    for component in native.display_components:
        definition_id = definition_by_path.get(component.occurrence_path.casefold())
        if definition_id is None:
            try:
                path = _mate_instance_path(native, identity, component.occurrence_path)
            except SldprtFormatError:
                path = ()
            if path:
                definition_id = occurrence_by_id[path[-1]].definition_id
        if definition_id is None or definition_id in mesh_ids:
            continue
        vertices: list[Vector3] = []
        normals: list[Vector3] = []
        triangles: list[tuple[int, int, int]] = []
        faces: list[dict[str, Any]] = []
        for face in component.faces:
            vertex_start = len(vertices)
            triangle_start = len(triangles)
            vertices.extend(Vector3(*point) for point in face.positions_mm)
            normals.extend(Vector3(*normal) for normal in face.normals)
            triangles.extend(
                tuple(index + vertex_start for index in triangle)
                for triangle in face.triangle_indices
            )
            faces.append(
                {
                    "face_id": face.face_id,
                    "vertex_start": vertex_start,
                    "vertex_count": len(face.positions_mm),
                    "triangle_start": triangle_start,
                    "triangle_count": len(face.triangle_indices),
                    "strip_lengths": face.strip_lengths,
                    "source_offset": face.offset,
                    "source_length": face.record_length,
                }
            )
        definition = definition_by_id[definition_id]
        mesh_id = f"sldasm:mesh:{definition_id}"
        result.append(
            Mesh(
                id=mesh_id,
                name=f"{definition.name} tessellation",
                vertices=tuple(vertices),
                triangles=tuple(triangles),
                normals=tuple(normals),
                provenance=Provenance(
                    adapter=_ASSEMBLY_FORMAT_ID,
                    native_id=str(definition_id),
                    spans=(
                        ProvenanceSpan(
                            DISPLAY_LISTS_STREAM,
                            component.record_offset,
                            component.record_length,
                            "component-tessellation",
                        ),
                    ),
                ),
                attributes=frozen_mapping(
                    {
                        "occurrence_path": component.occurrence_path,
                        "source_path": component.source_path,
                        "faces": tuple(faces),
                    }
                ),
            )
        )
        mesh_ids[definition_id] = mesh_id
    return tuple(result), mesh_ids


def _assembly_definitions(
    native: NativeAssembly,
    document_ids: dict[int, str],
    resolved_paths: dict[int, Path],
    documents: dict[str, CadDocument],
    mesh_ids: dict[int, str],
    label: str,
) -> tuple[ComponentDefinition, ...]:
    result: list[ComponentDefinition] = []
    for definition in native.definitions:
        document_id = document_ids.get(definition.object_id, "")
        document = documents.get(document_id)
        source_path = resolved_paths.get(definition.object_id)
        if definition.object_id == native.root_definition_id and Path(label).is_file():
            source_path = Path(label).resolve()
        kind = (
            ComponentKind.ASSEMBLY
            if definition.document_type == "ASSEMBLY"
            else (
                ComponentKind.PART
                if definition.document_type == "PART"
                else ComponentKind.NATIVE
            )
        )
        result.append(
            ComponentDefinition(
                id=_assembly_definition_id(definition.object_id),
                name=definition.name,
                kind=kind,
                document_id=document_id,
                configuration_name=definition.configuration_name,
                configuration_id=str(definition.configuration_id),
                bounding_box=_assembly_bounding_box(definition.bounding_box_m),
                body_ids=(
                    tuple(body.id for body in document.bodies)
                    if document is not None and kind == ComponentKind.PART
                    else ()
                ),
                mesh_ids=(
                    (mesh_ids[definition.object_id],)
                    if definition.object_id in mesh_ids
                    else ()
                ),
                source_path=(
                    str(source_path)
                    if source_path is not None
                    else definition.source_path
                ),
                source_format_id=(
                    _ASSEMBLY_FORMAT_ID
                    if kind == ComponentKind.ASSEMBLY
                    else _FORMAT_ID
                ),
                source_sha256=document.source.sha256 if document is not None else "",
                provenance=Provenance(
                    adapter=_ASSEMBLY_FORMAT_ID,
                    native_id=str(definition.object_id),
                    spans=(
                        ProvenanceSpan(
                            COMPONENT_TREE_STREAM,
                            0,
                            0,
                            "component-definition",
                        ),
                    ),
                ),
                attributes=frozen_mapping(
                    {
                        "native_object_id": definition.object_id,
                        "native_file_id": definition.file_id,
                        "native_source_path": definition.source_path,
                        "alternate_configuration_name": definition.alternate_configuration_name,
                        "last_modified_stamp": definition.last_modified_stamp,
                        "configuration_flags": definition.configuration_flags,
                        "child_occurrence_ids": definition.child_occurrence_ids,
                        "native_attributes": definition.attributes,
                    }
                ),
            )
        )
    return tuple(result)


def _assembly_instances(
    native: NativeAssembly,
) -> tuple[ComponentInstance, ...]:
    return tuple(
        ComponentInstance(
            id=_assembly_instance_id(occurrence.object_id),
            name=f"{occurrence.name}-{occurrence.reference_number}",
            definition_id=_assembly_definition_id(occurrence.definition_id),
            owner_definition_id=_assembly_definition_id(occurrence.owner_definition_id),
            transform=_assembly_matrix(occurrence.transform),
            order=occurrence.order,
            reference_number=str(occurrence.reference_number),
            configuration_name=occurrence.configuration_name,
            configuration_id=str(occurrence.configuration_id),
            suppressed=occurrence.suppressed,
            hidden=occurrence.hidden,
            fixed=occurrence.feature_id == 24,
            flexible=occurrence.flexible,
            exclude_from_bom=occurrence.exclude_from_bom,
            provenance=Provenance(
                adapter=_ASSEMBLY_FORMAT_ID,
                native_id=str(occurrence.object_id),
                spans=(
                    ProvenanceSpan(
                        COMPONENT_TREE_STREAM,
                        0,
                        0,
                        "component-instance",
                    ),
                ),
            ),
            attributes=frozen_mapping(
                {
                    "native_feature_id": occurrence.feature_id,
                    "native_reference_number": occurrence.reference_number,
                    "component_reference": occurrence.component_reference,
                    "native_transform": occurrence.transform,
                    "transform_stamp": occurrence.transform_stamp,
                    "virtual": occurrence.virtual,
                    "zone": occurrence.zone,
                    "display_mode": occurrence.display_mode,
                    "display_quality": occurrence.display_quality,
                    "edges_in_shaded_mode": occurrence.edges_in_shaded_mode,
                    "native_attributes": occurrence.attributes,
                }
            ),
        )
        for occurrence in native.occurrences
    )


def _mate_sources(
    root: NativeAssembly,
    archive: SldprtArchive,
    label: str,
    index: dict[str, tuple[Path, ...]],
    settings: ReadOptions,
) -> tuple[
    tuple[
        tuple[
            NativeAssembly,
            SldprtArchive,
            dict[int, int],
            dict[int, int],
            str,
        ],
        ...,
    ],
    tuple[Diagnostic, ...],
]:
    sources = [
        (
            root,
            archive,
            {
                definition.object_id: definition.object_id
                for definition in root.definitions
            },
            {
                occurrence.object_id: occurrence.object_id
                for occurrence in root.occurrences
            },
            label,
        )
    ]
    diagnostics: list[Diagnostic] = []
    for target in root.definitions:
        if (
            target.document_type != "ASSEMBLY"
            or target.object_id == root.root_definition_id
        ):
            continue
        resolved = _resolved_component_path(target.source_path, index)
        if resolved is None:
            message = (
                f"nested assembly mate source is unavailable: {target.source_path}"
            )
            if settings.strict:
                raise SldprtFormatError(message)
            diagnostics.append(
                Diagnostic(
                    code="sldasm.nested_mates_missing",
                    message=message,
                    severity=Severity.WARNING,
                )
            )
            continue
        nested_archive = SldprtArchive.open(resolved)
        nested = decode_native_assembly(nested_archive, include_tessellation=False)
        try:
            definition_map = _nested_definition_map(root, nested, target.object_id)
            occurrence_map = _nested_occurrence_map(root, nested, definition_map)
        except SldprtFormatError as exc:
            if settings.strict:
                raise
            diagnostics.append(
                Diagnostic(
                    code="sldasm.nested_mates_unmapped",
                    message=f"cannot map nested mates from {resolved}: {exc}",
                    severity=Severity.WARNING,
                )
            )
            continue
        sources.append(
            (
                nested,
                nested_archive,
                definition_map,
                occurrence_map,
                str(resolved),
            )
        )
    return tuple(sources), tuple(diagnostics)


def _native_definition_key(
    definition: NativeAssemblyDefinition,
) -> tuple[str, str, str]:
    return (
        PureWindowsPath(definition.source_path).name.casefold(),
        definition.configuration_name.casefold(),
        definition.document_type.casefold(),
    )


def _nested_definition_map(
    root: NativeAssembly, nested: NativeAssembly, target_root_id: int
) -> dict[int, int]:
    result = {nested.root_definition_id: target_root_id}
    targets: defaultdict[tuple[str, str, str], list[NativeAssemblyDefinition]] = (
        defaultdict(list)
    )
    for definition in root.definitions:
        targets[_native_definition_key(definition)].append(definition)
    for definition in nested.definitions:
        if definition.object_id == nested.root_definition_id:
            continue
        candidates = targets.get(_native_definition_key(definition), [])
        if len(candidates) != 1:
            raise SldprtFormatError(
                f"nested definition {definition.name!r} has {len(candidates)} root mappings"
            )
        result[definition.object_id] = candidates[0].object_id
    return result


def _nested_occurrence_map(
    root: NativeAssembly,
    nested: NativeAssembly,
    definition_map: dict[int, int],
) -> dict[int, int]:
    result: dict[int, int] = {}
    for occurrence in nested.occurrences:
        owner_id = definition_map[occurrence.owner_definition_id]
        definition_id = definition_map[occurrence.definition_id]
        candidates = tuple(
            target
            for target in root.occurrences
            if target.owner_definition_id == owner_id
            and target.definition_id == definition_id
            and target.name.casefold() == occurrence.name.casefold()
            and target.reference_number == occurrence.reference_number
            and target.feature_id == occurrence.feature_id
        )
        if len(candidates) != 1:
            raise SldprtFormatError(
                f"nested occurrence {occurrence.name}-{occurrence.reference_number} has {len(candidates)} root mappings"
            )
        result[occurrence.object_id] = candidates[0].object_id
    return result


def _assembly_mates(
    root: NativeAssembly,
    sources: tuple[
        tuple[
            NativeAssembly,
            SldprtArchive,
            dict[int, int],
            dict[int, int],
            str,
        ],
        ...,
    ],
) -> tuple[
    tuple[BrepPayload, ...],
    tuple[MateEntity, ...],
    tuple[MateConstraint, ...],
    tuple[MateGroup, ...],
]:
    payloads: list[BrepPayload] = []
    entities: list[MateEntity] = []
    mates: list[MateConstraint] = []
    groups: list[MateGroup] = []
    for source_index, (
        source,
        archive,
        definition_map,
        occurrence_map,
        source_label,
    ) in enumerate(sources):
        for list_index, mate_list in enumerate(source.mate_lists):
            owner_id = definition_map[mate_list.owner_definition_id]
            stream_data = archive.require(mate_list.stream)
            stream_name = (
                mate_list.stream
                if source_index == 0
                else f"{source_label}::{mate_list.stream}"
            )
            payload_id = f"sldasm:mates:{owner_id}:{list_index}"
            payloads.append(
                _mate_payload(
                    payload_id,
                    stream_name,
                    stream_data,
                    mate_list,
                    owner_id,
                    source_label,
                )
            )
            mate_ids_by_order: dict[int, str] = {}
            for mate in mate_list.mates:
                if mate.kind == "group":
                    continue
                mate_id = f"sldasm:mate:{owner_id}:{list_index}:{mate.order}"
                entity_ids: list[str] = []
                for entity_index, native_entity in enumerate(mate.entities):
                    entity_id = f"{mate_id}:entity:{entity_index}"
                    entity_ids.append(entity_id)
                    entities.append(
                        _assembly_mate_entity(
                            entity_id,
                            owner_id,
                            source,
                            occurrence_map,
                            native_entity,
                            mate,
                            stream_name,
                            source_label,
                        )
                    )
                mates.append(
                    MateConstraint(
                        id=mate_id,
                        name=mate.name,
                        kind=_neutral_mate_kind(mate.kind),
                        owner_definition_id=_assembly_definition_id(owner_id),
                        entity_ids=tuple(entity_ids),
                        order=mate.order,
                        value=_neutral_mate_value(mate),
                        alignment=_neutral_mate_alignment(mate),
                        suppressed=False,
                        driving=True,
                        provenance=_mate_provenance(mate, stream_name),
                        attributes=frozen_mapping(
                            {
                                "native_kind": mate.kind,
                                "native_class_name": mate.class_name,
                                "native_class_token": mate.class_token,
                                "native_owner_definition_id": mate.owner_definition_id,
                                "native_record_offset": mate.record_offset,
                                "native_record_length": mate.record_length,
                                "native_payload_id": payload_id,
                                "serialized_strings": mate.serialized_strings,
                                "source_document": source_label,
                                "native_alignment_code": mate.alignment_code,
                                "native_dimensions": tuple(
                                    {
                                        "name": dimension.name,
                                        "value": dimension.value,
                                        "value_offset": dimension.value_offset,
                                    }
                                    for dimension in mate.dimensions
                                ),
                                "native_value_m": mate.value_m,
                                "native_value_offset": mate.value_offset,
                            }
                        ),
                    )
                )
                mate_ids_by_order[mate.order] = mate_id
            groups.extend(
                _mate_groups(
                    mate_list,
                    owner_id,
                    mate_ids_by_order,
                    stream_name,
                    payload_id,
                )
            )
    return tuple(payloads), tuple(entities), tuple(mates), tuple(groups)


def _mate_payload(
    payload_id: str,
    stream_name: str,
    data: bytes,
    mate_list: NativeMateList,
    owner_id: int,
    source_label: str,
) -> BrepPayload:
    return BrepPayload(
        id=payload_id,
        format_id="solidworks.mates",
        kind="mate-list",
        schema="solidworks.serialized-object-stream",
        sha256=hashlib.sha256(data).hexdigest(),
        data=data,
        source_stream=stream_name,
        provenance=Provenance(
            adapter=_ASSEMBLY_FORMAT_ID,
            native_id=str(mate_list.native_id),
            spans=(ProvenanceSpan(stream_name, 0, len(data), "mate-list"),),
        ),
        attributes=frozen_mapping(
            {
                "native_id": mate_list.native_id,
                "declared_count": mate_list.declared_count,
                "owner_definition_id": owner_id,
                "source_document": source_label,
                "records": tuple(
                    {
                        "name": mate.name,
                        "kind": mate.kind,
                        "class_name": mate.class_name,
                        "class_token": mate.class_token,
                        "offset": mate.record_offset,
                        "length": mate.record_length,
                    }
                    for mate in mate_list.mates
                ),
            }
        ),
        role=PayloadRole.ASSEMBLY_STRUCTURE,
        file_extension=".bin",
    )


def _assembly_mate_entity(
    entity_id: str,
    owner_id: int,
    source: NativeAssembly,
    occurrence_map: dict[int, int],
    entity: NativeMateEntity,
    mate: NativeMate,
    stream_name: str,
    source_label: str,
) -> MateEntity:
    path = _mate_instance_path(source, occurrence_map, entity.component_path)
    source_entity_id = (
        entity.persistent_references[-1] if entity.persistent_references else ""
    )
    return MateEntity(
        id=entity_id,
        owner_definition_id=_assembly_definition_id(owner_id),
        instance_path=tuple(_assembly_instance_id(value) for value in path),
        kind=_neutral_mate_entity_kind(source_entity_id),
        source_entity_id=source_entity_id,
        provenance=_mate_provenance(mate, stream_name),
        attributes=frozen_mapping(
            {
                "component_path": entity.component_path,
                "persistent_references": entity.persistent_references,
                "source_path": entity.source_path,
                "configuration_name": entity.configuration_name,
                "source_document": source_label,
            }
        ),
    )


def _mate_instance_path(
    source: NativeAssembly,
    occurrence_map: dict[int, int],
    component_path: str,
) -> tuple[int, ...]:
    if not component_path:
        return ()
    children: defaultdict[int, list[NativeAssemblyOccurrence]] = defaultdict(list)
    for occurrence in source.occurrences:
        children[occurrence.owner_definition_id].append(occurrence)
    owner_id = source.root_definition_id
    result: list[int] = []
    for raw_segment in component_path.split("/"):
        segment = raw_segment.split("@", 1)[0].strip().casefold()
        candidates = tuple(
            occurrence
            for occurrence in children.get(owner_id, [])
            if segment
            in {
                occurrence.name.strip().casefold(),
                f"{occurrence.name}-{occurrence.reference_number}".strip().casefold(),
            }
        )
        if not candidates:
            return ()
        if len(candidates) != 1:
            raise SldprtFormatError(
                f"mate component path segment {raw_segment!r} has {len(candidates)} hierarchy mappings"
            )
        occurrence = candidates[0]
        mapped = occurrence_map.get(occurrence.object_id)
        if mapped is None:
            raise SldprtFormatError(
                f"mate component path references unmapped occurrence {occurrence.object_id}"
            )
        result.append(mapped)
        owner_id = occurrence.definition_id
    return tuple(result)


def _neutral_mate_kind(value: str) -> MateKind:
    alias = NATIVE_MATE_NEUTRAL_KIND_ALIASES.get(value)
    if alias is not None:
        return MateKind(alias)
    try:
        return MateKind(value)
    except ValueError:
        return MateKind.NATIVE


def _neutral_mate_alignment(mate: NativeMate) -> MateAlignment:
    alignment = NATIVE_MATE_ALIGNMENT_BY_CODE.get(mate.alignment_code)
    if alignment is None:
        return MateAlignment.UNKNOWN
    return MateAlignment(alignment.kind)


def _neutral_mate_value(mate: NativeMate) -> ParameterValue | None:
    dimensions = mate.dimensions
    if not dimensions:
        return None
    semantic = MATE_VALUE_SEMANTICS.get(mate.kind)
    if semantic == "angle":
        return ParameterValue(dimensions[0].value, ValueKind.ANGLE, "rad")
    if semantic == "length":
        return ParameterValue(dimensions[0].value * 1000.0, ValueKind.LENGTH, "mm")
    if semantic == "ratio" and len(dimensions) >= 2:
        denominator = dimensions[1].value
        if denominator != 0.0:
            return ParameterValue(
                dimensions[0].value / denominator, ValueKind.NUMBER, ""
            )
    return None


def _neutral_mate_entity_kind(value: str) -> MateEntityKind:
    lowered = value.casefold()
    for marker, kind in NATIVE_MATE_ENTITY_MARKERS:
        if marker in lowered:
            return MateEntityKind(kind)
    return MateEntityKind.NATIVE


def _mate_provenance(mate: NativeMate, stream_name: str) -> Provenance:
    return Provenance(
        adapter=_ASSEMBLY_FORMAT_ID,
        native_id=mate.name,
        spans=(
            ProvenanceSpan(
                stream_name,
                mate.record_offset,
                mate.record_length,
                "mate-record",
            ),
        ),
    )


def _mate_groups(
    mate_list: NativeMateList,
    owner_id: int,
    mate_ids_by_order: dict[int, str],
    stream_name: str,
    payload_id: str,
) -> tuple[MateGroup, ...]:
    result: list[MateGroup] = []
    records = mate_list.mates
    markers = tuple(record for record in records if record.kind == "group")
    for pair_index in range(0, len(markers) - 1, 2):
        marker = markers[pair_index]
        end = markers[pair_index + 1]
        next_start = (
            markers[pair_index + 2].order
            if pair_index + 2 < len(markers)
            else len(records)
        )
        members: list[str] = []
        for candidate in records:
            if (
                candidate.order <= end.order
                or candidate.order >= next_start
                or candidate.kind == "group"
            ):
                continue
            mate_id = mate_ids_by_order.get(candidate.order)
            if mate_id is not None:
                members.append(mate_id)
            if candidate.kind == "lock_to_sketch":
                break
        result.append(
            MateGroup(
                id=f"sldasm:mate-group:{owner_id}:{marker.order}",
                name=marker.name,
                owner_definition_id=_assembly_definition_id(owner_id),
                mate_ids=tuple(members),
                order=marker.order,
                provenance=Provenance(
                    adapter=_ASSEMBLY_FORMAT_ID,
                    native_id=marker.name,
                    spans=(
                        ProvenanceSpan(
                            stream_name,
                            marker.record_offset,
                            marker.record_length,
                            "mate-group-start",
                        ),
                        ProvenanceSpan(
                            stream_name,
                            end.record_offset,
                            end.record_length,
                            "mate-group-end",
                        ),
                    ),
                ),
                attributes=frozen_mapping(
                    {
                        "native_payload_id": payload_id,
                        "start_record_offset": marker.record_offset,
                        "start_record_length": marker.record_length,
                        "end_record_offset": end.record_offset,
                        "end_record_length": end.record_length,
                    }
                ),
            )
        )
    return tuple(result)


def _flattened_occurrences(native: NativeAssembly) -> tuple[dict[str, Any], ...]:
    identity = {item.object_id: item.object_id for item in native.occurrences}
    return tuple(
        {
            "occurrence_id": _assembly_instance_id(occurrence.occurrence_id),
            "definition_id": _assembly_definition_id(occurrence.definition_id),
            "path": occurrence.path,
            "instance_path": tuple(
                _assembly_instance_id(value)
                for value in _mate_instance_path(
                    native,
                    identity,
                    occurrence.path,
                )
            ),
            "depth": occurrence.depth,
        }
        for occurrence in native.occurrence_paths
    )


def _flattened_mates(
    native: NativeAssembly, mates: tuple[MateConstraint, ...]
) -> tuple[dict[str, Any], ...]:
    identity = {item.object_id: item.object_id for item in native.occurrences}
    owner_paths: defaultdict[int, list[tuple[str, tuple[str, ...]]]] = defaultdict(list)
    owner_paths[native.root_definition_id].append(("", ()))
    for occurrence in native.occurrence_paths:
        path = tuple(
            _assembly_instance_id(value)
            for value in _mate_instance_path(native, identity, occurrence.path)
        )
        owner_paths[occurrence.definition_id].append((occurrence.path, path))
    result: list[dict[str, Any]] = []
    for mate in mates:
        owner_id = int(mate.owner_definition_id.rsplit(":", 1)[-1])
        for index, (path, instance_path) in enumerate(owner_paths.get(owner_id, [])):
            result.append(
                {
                    "id": f"{mate.id}:occurrence:{index}",
                    "mate_id": mate.id,
                    "owner_definition_id": mate.owner_definition_id,
                    "owner_occurrence_path": path,
                    "owner_instance_path": instance_path,
                }
            )
    return tuple(result)


def _companion_payloads(label: str) -> tuple[BrepPayload, ...]:
    source = Path(label)
    if not source.is_file():
        return ()
    source = source.resolve()
    specifications = (
        ("ACIS", ".sat", "acis.sat"),
        ("Parasolid", ".x_t", "parasolid.x_t"),
    )
    result: list[BrepPayload] = []
    for directory_name, suffix, format_id in specifications:
        directory = source.parent / directory_name
        if not directory.is_dir():
            continue
        candidate = next(
            (
                path
                for path in directory.iterdir()
                if path.is_file()
                and path.stem.casefold() == source.stem.casefold()
                and path.suffix.casefold() == suffix
            ),
            None,
        )
        if candidate is None:
            continue
        data = candidate.read_bytes()
        attributes: dict[str, Any] = {
            "companion_path": str(candidate.resolve()),
            "source_assembly": str(source),
        }
        if format_id == "acis.sat":
            header = data.splitlines()[0].decode("ascii", errors="replace").split()
            if len(header) >= 3 and header[2].isdigit():
                attributes["body_count"] = int(header[2])
        result.append(
            BrepPayload(
                id=f"sldasm:resolved:{format_id}",
                format_id=format_id,
                kind="resolved-assembly",
                schema=format_id,
                sha256=hashlib.sha256(data).hexdigest(),
                data=data,
                source_stream=str(candidate.resolve()),
                provenance=Provenance(
                    adapter=_ASSEMBLY_FORMAT_ID,
                    native_id=candidate.name,
                    spans=(
                        ProvenanceSpan(
                            str(candidate.resolve()),
                            0,
                            len(data),
                            "resolved-assembly-brep",
                        ),
                    ),
                ),
                attributes=frozen_mapping(attributes),
                role=PayloadRole.BREP,
                file_extension=suffix,
            )
        )
    return tuple(result)


def _assembly_matrix(values: tuple[float, ...]) -> Matrix4:
    return Matrix4(
        (
            values[0],
            values[4],
            values[8],
            values[12] * 1000.0,
            values[1],
            values[5],
            values[9],
            values[13] * 1000.0,
            values[2],
            values[6],
            values[10],
            values[14] * 1000.0,
            values[3],
            values[7],
            values[11],
            values[15],
        )
    )


def _assembly_bounding_box(
    values: tuple[float, float, float, float, float, float] | None,
) -> BoundingBox | None:
    if values is None:
        return None
    return BoundingBox(
        Vector3(*(value * 1000.0 for value in values[:3])),
        Vector3(*(value * 1000.0 for value in values[3:])),
    )


def _assembly_definition_id(native_id: int) -> str:
    return f"sldasm:definition:{native_id}"


def _assembly_instance_id(native_id: int) -> str:
    return f"sldasm:instance:{native_id}"


def _validate_source_suffix(label: str, is_assembly: bool) -> None:
    suffix = Path(label).suffix.casefold()
    expected_format = _ASSEMBLY_FORMAT_ID if is_assembly else _FORMAT_ID
    expected = SUFFIX_BY_FORMAT_ID[expected_format]
    if suffix in FORMAT_ID_BY_SUFFIX and suffix != expected:
        kind = "assembly" if is_assembly else "part"
        raise SldprtFormatError(
            f"SOLIDWORKS {kind} content requires a {expected.upper()} source"
        )


def _source_bytes(source: Source) -> tuple[bytes, str]:
    if isinstance(source, (str, Path)):
        path = Path(source).expanduser().resolve()
        return path.read_bytes(), str(path)
    if isinstance(source, (bytes, bytearray)):
        return bytes(source), "<memory>"
    position = None
    tell = getattr(source, "tell", None)
    seek = getattr(source, "seek", None)
    if callable(tell):
        try:
            position = tell()
        except (OSError, ValueError):
            position = None
    value = source.read()
    if position is not None and callable(seek):
        try:
            seek(position)
        except (OSError, ValueError):
            position = None
    if not isinstance(value, (bytes, bytearray)):
        raise TypeError("SLDPRT source stream must yield bytes")
    name = getattr(source, "name", "<stream>")
    return bytes(value), str(name)


def _resolved_features_stream(streams: Mapping[str, bytes], lane: str) -> str:
    return KIT_RESOLVED_STREAM if KIT_RESOLVED_STREAM in streams else lane


def _native_part_model(archive: SldprtArchive, requested: str | None) -> NativeModel:
    keywords = archive.require(KEYWORDS_STREAM)
    lanes = {
        int(match.group(1)): name
        for name in archive.streams
        if (match := _RESOLVED_CONFIGURATION_STREAM.fullmatch(name)) is not None
    }
    if not lanes:
        raise SldprtFormatError("required native resolved-feature stream is missing")
    initial_id = 0 if 0 in lanes else min(lanes)
    initial_stream = _resolved_features_stream(archive.streams, lanes[initial_id])
    initial = decode_native_model(
        keywords,
        archive.require(initial_stream),
        configuration_id=initial_id,
        resolved_stream=initial_stream,
    )
    selected_id = initial_id
    if requested is not None:
        selected = next(
            (
                item.configuration_id
                for item in initial.configurations
                if item.name == requested
            ),
            None,
        )
        if selected is None:
            raise SldprtFormatError(
                f"configuration {requested!r} is unavailable; choices are "
                f"{sorted(item.name for item in initial.configurations)}"
            )
        selected_id = selected
    if selected_id not in lanes:
        raise SldprtFormatError(
            f"native data for configuration {selected_id} is unavailable; "
            f"available lanes are {sorted(lanes)}"
        )
    resolved_stream = _resolved_features_stream(archive.streams, lanes[selected_id])
    configuration_stream = f"Contents/Config-{selected_id}"
    return decode_native_model(
        keywords,
        archive.require(resolved_stream),
        archive.get(configuration_stream) or b"",
        configuration_id=selected_id,
        resolved_stream=resolved_stream,
        configuration_stream=configuration_stream,
    )


def _configurations(
    model: NativeModel, requested: str | None
) -> tuple[Configuration, ...]:
    available = {item.name for item in model.configurations}
    if requested is not None and requested not in available:
        raise SldprtFormatError(
            f"configuration {requested!r} is unavailable; choices are {sorted(available)}"
        )
    active = requested or next(
        (
            item.name
            for item in model.configurations
            if item.configuration_id == model.active_configuration_id
        ),
        model.configurations[0].name,
    )
    return tuple(
        Configuration(
            id=_configuration_id(item.configuration_id),
            name=item.name,
            active=item.name == active,
            attributes=frozen_mapping(
                {
                    "native_object_id": item.object_id,
                    "native_configuration_id": item.configuration_id,
                    "native_properties": item.properties,
                }
            ),
        )
        for item in model.configurations
    )


def _parameters(model: NativeModel) -> tuple[Parameter, ...]:
    parameters: list[Parameter] = []
    dimension_ids: dict[tuple[str, str], str] = {}
    for feature in model.features:
        for dimension, parameter_id in _parameter_entries(
            feature.object_id, feature.dimensions
        ):
            native_value = (
                dimension.native_value
                if dimension.native_value is not None
                else dimension.value_mm / 1000.0
            )
            parameters.append(
                Parameter(
                    id=parameter_id,
                    name=dimension.name,
                    value=_dimension_parameter_value(dimension),
                    role=(
                        ParameterRole.DRIVEN
                        if dimension.native_role == "display"
                        else ParameterRole.DRIVING
                    ),
                    owner_id=_feature_id(feature.object_id),
                    provenance=(
                        _provenance(
                            f"{feature.object_id}:{dimension.name}",
                            dimension.native_offset,
                            8,
                            "dimension-scalar",
                            stream=feature.native_stream,
                        )
                        if dimension.native_offset is not None
                        else _feature_provenance(feature)
                    ),
                    attributes=frozen_mapping(
                        {
                            "source_text": dimension.source_text,
                            "dimension_kind": dimension.kind,
                            "native_value": native_value,
                            "native_unit": (
                                "rad" if dimension.kind == "angle" else "m"
                            ),
                            "native_role": dimension.native_role or "unresolved",
                            "native_operands": tuple(
                                {
                                    "offset": operand.offset,
                                    "kind_code": operand.kind_code,
                                    "entity_index": operand.entity_index,
                                }
                                for operand in dimension.operands
                            ),
                        }
                    ),
                )
            )
            dimension_ids.setdefault((feature.name, dimension.name), parameter_id)
    return _apply_native_equations(parameters, model, dimension_ids)


def _dimension_parameter_value(dimension: NativeDimension) -> ParameterValue:
    if dimension.kind == "angle":
        return ParameterValue(dimension.value_mm, ValueKind.ANGLE, "deg")
    return ParameterValue(dimension.value_mm, ValueKind.LENGTH, "mm")


def _apply_native_equations(
    parameters: list[Parameter],
    model: NativeModel,
    dimension_ids: dict[tuple[str, str], str],
) -> tuple[Parameter, ...]:
    if not model.equations:
        return tuple(parameters)
    global_ids = {
        equation.lhs: f"sldprt:parameter:equation:{equation.lhs}"
        for equation in model.equations
        if "@" not in equation.lhs
    }
    values: dict[str, ParameterValue] = {}
    parameter_indexes = {
        parameter.id: index for index, parameter in enumerate(parameters)
    }
    for equation in model.equations:
        reference_ids = tuple(
            global_ids[reference]
            for reference in equation.references
            if reference in global_ids
        )
        expression = Expression(
            equation.rhs,
            reference_ids,
            "solidworks",
        )
        provenance = Provenance(
            adapter=_FORMAT_ID,
            native_id=f"equation:{equation.native_offset}",
            spans=(
                ProvenanceSpan(
                    equation.native_stream,
                    equation.native_offset,
                    equation.native_length,
                    "equation",
                ),
            ),
        )
        if "@" in equation.lhs:
            dimension_name, feature_name = equation.lhs.split("@", 1)
            parameter_id = dimension_ids.get((feature_name, dimension_name))
            if parameter_id is None or parameter_id not in parameter_indexes:
                continue
            index = parameter_indexes[parameter_id]
            parameters[index] = replace(
                parameters[index],
                role=ParameterRole.DERIVED,
                expression=expression,
                provenance=provenance,
                attributes=frozen_mapping(
                    {
                        **dict(parameters[index].attributes),
                        "equation_source": equation.source,
                        "equation_configuration_id": equation.configuration_id,
                    }
                ),
            )
            continue
        value = _native_equation_value(equation.rhs, values)
        if value is None:
            value = ParameterValue(equation.rhs, ValueKind.STRING)
        values[equation.lhs] = value
        parameter = Parameter(
            id=global_ids[equation.lhs],
            name=equation.lhs,
            value=value,
            role=(
                ParameterRole.DERIVED if equation.references else ParameterRole.DRIVING
            ),
            expression=expression,
            owner_id=_feature_id(16),
            provenance=provenance,
            attributes=frozen_mapping(
                {
                    "equation_source": equation.source,
                    "equation_configuration_id": equation.configuration_id,
                }
            ),
        )
        if parameter.id in parameter_indexes:
            parameters[parameter_indexes[parameter.id]] = parameter
        else:
            parameter_indexes[parameter.id] = len(parameters)
            parameters.append(parameter)
    return tuple(parameters)


def _native_equation_value(
    rhs: str, values: Mapping[str, ParameterValue]
) -> ParameterValue | None:
    literal = re.fullmatch(
        r"\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*mm\s*",
        rhs,
        re.IGNORECASE,
    )
    if literal is not None:
        return ParameterValue(float(literal.group(1)), ValueKind.LENGTH, "mm")
    number = re.fullmatch(r"\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*", rhs)
    if number is not None:
        return ParameterValue(float(number.group(1)), ValueKind.NUMBER, "")
    quotient = re.fullmatch(
        r'\s*"([^"\r\n]+)"\s*/\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*',
        rhs,
    )
    if quotient is None:
        return None
    source = values.get(quotient.group(1))
    if (
        source is None
        or source.kind not in {ValueKind.LENGTH, ValueKind.NUMBER}
        or not isinstance(source.value, (int, float))
    ):
        return None
    divisor = float(quotient.group(2))
    if not math.isfinite(divisor) or divisor == 0.0:
        return None
    return ParameterValue(float(source.value) / divisor, source.kind, source.unit)


def _planes(model: NativeModel, parameter_ids: set[str]) -> tuple[SupportPlane, ...]:
    result: list[SupportPlane] = []
    for plane in sorted(
        model.planes,
        key=lambda item: (
            next(
                (
                    feature.native_offset
                    for feature in model.features
                    if feature.object_id == item.object_id
                ),
                None,
            )
            is None,
            next(
                (
                    feature.native_offset
                    for feature in model.features
                    if feature.object_id == item.object_id
                ),
                1 << 62,
            ),
        ),
    ):
        offset_id = _parameter_id(plane.object_id, "D1")
        result.append(
            SupportPlane(
                id=_plane_id(plane.object_id),
                name=plane.name,
                transform=Transform(
                    origin=Vector3(*plane.origin_mm),
                    x_axis=Vector3(*plane.u_axis),
                    y_axis=Vector3(*plane.v_axis),
                    z_axis=Vector3(*plane.normal),
                ),
                offset_parameter_id=(offset_id if offset_id in parameter_ids else None),
                provenance=(
                    _provenance(
                        str(plane.object_id),
                        plane.native_offset,
                        plane.native_length or 1,
                        "support-plane-frame",
                        stream=plane.native_stream,
                    )
                    if plane.native_offset is not None
                    else _provenance(
                        str(plane.object_id), None, None, "principal-plane"
                    )
                ),
                attributes=frozen_mapping(
                    {
                        "native_object_id": plane.object_id,
                        "native_frame_offset": plane.native_offset,
                        "native_frame_length": plane.native_length,
                        "principal": plane.principal,
                        "native_reference_ids": plane.reference_ids,
                    }
                ),
            )
        )
    return tuple(result)


def _sketches(model: NativeModel, parameter_ids: set[str]) -> tuple[Sketch, ...]:
    return tuple(
        _sketch(sketch, parameter_ids)
        for sketch in sorted(model.sketches, key=lambda item: item.native_offset)
    )


def _sketch(sketch: NativeSketch, parameter_ids: set[str]) -> Sketch:
    entities: list[SketchEntity] = []
    reference_map: dict[str, str] = {}
    profile_entities: dict[int, str] = {}
    profile_offsets = {
        offset for profile in sketch.profiles for offset in profile.marker_offsets
    }
    for profile_index, profile in enumerate(sketch.profiles):
        if profile.kind == "rectangle":
            x0, y0, x1, y1 = profile.coordinates
            endpoints = (
                ((x0, y0), (x1, y0)),
                ((x1, y0), (x1, y1)),
                ((x1, y1), (x0, y1)),
                ((x0, y1), (x0, y0)),
            )
            for edge_index, (start, end) in enumerate(endpoints):
                entity_id = _profile_edge_id(
                    sketch.object_id, profile_index, edge_index
                )
                marker_offset = (
                    profile.marker_offsets[edge_index]
                    if edge_index < len(profile.marker_offsets)
                    else None
                )
                entities.append(
                    SketchEntity(
                        id=entity_id,
                        kind=GeometryKind.LINE,
                        geometry=LineGeometry(Vector2(*start), Vector2(*end)),
                        provenance=(
                            _provenance(
                                f"{sketch.object_id}:{marker_offset}",
                                marker_offset,
                                92,
                                "sketch-profile-line",
                                stream=sketch.native_stream,
                            )
                            if marker_offset is not None
                            else _feature_span_provenance(sketch)
                        ),
                        attributes=frozen_mapping(
                            {
                                "profile_index": profile_index,
                                "edge_index": edge_index,
                            }
                        ),
                    )
                )
                reference_map[
                    f"{sketch.object_id}:profile:{profile_index}:edge:{edge_index}"
                ] = entity_id
                if marker_offset is not None:
                    profile_entities[marker_offset] = entity_id
        elif profile.kind == "circle":
            x, y, radius = profile.coordinates
            entity_id = _profile_id(sketch.object_id, profile_index)
            entities.append(
                SketchEntity(
                    id=entity_id,
                    kind=GeometryKind.CIRCLE,
                    geometry=CircleGeometry(Vector2(x, y), radius),
                    provenance=Provenance(
                        adapter=_FORMAT_ID,
                        native_id=f"{sketch.object_id}:profile:{profile_index}",
                        spans=tuple(
                            ProvenanceSpan(
                                sketch.native_stream,
                                offset,
                                142,
                                "sketch-circle-marker",
                            )
                            for offset in profile.marker_offsets
                        ),
                    ),
                    attributes=frozen_mapping({"profile_index": profile_index}),
                )
            )
            reference_map[f"{sketch.object_id}:profile:{profile_index}"] = entity_id
            profile_entities.update(
                {offset: entity_id for offset in profile.marker_offsets}
            )
    coordinates_by_prefix = {
        prefix: tuple(
            marker.coordinates_mm
            for marker in sketch.markers
            if marker.prefix == prefix
        )
        for prefix in {marker.prefix for marker in sketch.markers}
    }
    coordinates_by_index = tuple(marker.coordinates_mm for marker in sketch.markers)
    marker_semantics = tuple(
        _marker_curve_semantic(marker) for marker in sketch.markers
    )
    curve_reference_indices = {
        reference
        for marker, semantic in zip(sketch.markers, marker_semantics, strict=True)
        for reference in _marker_curve_reference_indices(marker, semantic)
    } | {
        reference
        for marker in sketch.markers
        for reference in _marker_object_reference_indices(marker.data)
    }
    marker_entities: dict[int, str] = {}
    for marker_index, (marker, semantic) in enumerate(
        zip(sketch.markers, marker_semantics, strict=True)
    ):
        if marker.offset in profile_offsets:
            entity_id = profile_entities.get(marker.offset)
            if entity_id is not None:
                marker_entities[marker_index] = entity_id
            continue
        if (
            marker_index in curve_reference_indices
            and marker.coordinates_mm is not None
            and marker.locus == "05000100"
        ):
            continue
        if (
            marker.coordinates_mm is not None
            and marker.object_index is None
            and marker.locus == "05000100"
        ):
            continue
        if marker.endpoint_indices is None and b"sgSlot_c" in marker.data:
            continue
        entity = _marker_entity(
            sketch,
            marker,
            coordinates_by_prefix,
            coordinates_by_index,
            semantic,
        )
        entities.append(entity)
        marker_entities[marker_index] = entity.id
    reference_map.update(
        {
            f"native-index:{index}": entity_id
            for index, entity_id in marker_entities.items()
        }
    )
    for dimension in sketch.dimensions:
        if dimension.kind != "length":
            continue
        for operand in dimension.operands:
            entity_id = marker_entities.get(operand.entity_index)
            if entity_id is not None:
                reference_map[
                    f"native:{operand.kind_code:04x}:{operand.entity_index}"
                ] = entity_id
    constraints = _sketch_constraints(sketch, reference_map, parameter_ids)
    closed_profiles: list[tuple[str, ...]] = []
    for profile_index, profile in enumerate(sketch.profiles):
        if profile.kind == "rectangle":
            closed_profiles.append(
                tuple(
                    _profile_edge_id(sketch.object_id, profile_index, edge_index)
                    for edge_index in range(4)
                )
            )
        elif profile.kind == "circle":
            closed_profiles.append((_profile_id(sketch.object_id, profile_index),))
    sketch_parameter_ids = tuple(
        parameter_id
        for dimension, parameter_id in _parameter_entries(
            sketch.object_id, sketch.dimensions
        )
        if parameter_id in parameter_ids
    )
    return Sketch(
        id=_sketch_id(sketch.object_id),
        name=sketch.name,
        support_plane_id=_plane_id(sketch.support_plane_id),
        entities=tuple(entities),
        constraints=constraints,
        parameter_ids=sketch_parameter_ids,
        closed_profile_entity_ids=tuple(closed_profiles),
        provenance=_feature_span_provenance(sketch),
        attributes=frozen_mapping(
            {
                "native_object_id": sketch.object_id,
                "native_marker_count": len(sketch.markers),
                "native_profile_count": len(sketch.profiles),
                "support_plane_native_id": sketch.support_plane_id,
                "support_plane_source": sketch.support_source,
                "unframed_support_plane_native_id": sketch.unframed_support_plane_id,
            }
        ),
    )


def _marker_entity(
    sketch: NativeSketch,
    marker: NativeMarker,
    coordinates_by_prefix: dict[str, tuple[tuple[float, float] | None, ...]],
    coordinates_by_index: tuple[tuple[float, float] | None, ...],
    semantic: str | None = None,
) -> SketchEntity:
    entity_id = _marker_id(sketch.object_id, marker.offset)
    resolved_semantic = semantic or marker.semantic
    if resolved_semantic == "point" and marker.coordinates_mm is not None:
        kind = GeometryKind.POINT
        geometry: Any = PointGeometry(Vector2(*marker.coordinates_mm))
    elif resolved_semantic == "line" and marker.endpoint_indices is not None:
        coordinates = (
            coordinates_by_index
            if resolved_semantic != marker.semantic
            or marker.profile_role == 2
            and marker.native_kind == 2
            else coordinates_by_prefix[marker.prefix]
        )
        start = _coordinate_reference(coordinates, marker.endpoint_indices[0])
        end = _coordinate_reference(coordinates, marker.endpoint_indices[1])
        if start is not None and end is not None and start != end:
            kind = GeometryKind.LINE
            geometry = LineGeometry(Vector2(*start), Vector2(*end))
        else:
            kind = GeometryKind.NATIVE
            geometry = _native_marker_geometry(marker)
    elif resolved_semantic in {"circle", "arc"}:
        circular = _marker_circular_geometry(
            marker, coordinates_by_index, resolved_semantic
        )
        if circular is None:
            kind = GeometryKind.NATIVE
            geometry = _native_marker_geometry(marker, resolved_semantic)
        else:
            kind, geometry = circular
    elif resolved_semantic == "ellipse":
        ellipse = _marker_ellipse_geometry(marker, coordinates_by_index)
        if ellipse is None:
            kind = GeometryKind.NATIVE
            geometry = _native_marker_geometry(marker, resolved_semantic)
        else:
            kind = GeometryKind.ELLIPSE
            geometry = ellipse
    elif resolved_semantic == "arc_ellipse":
        ellipse = _marker_arc_ellipse_geometry(marker, coordinates_by_index)
        if ellipse is None:
            kind = GeometryKind.NATIVE
            geometry = _native_marker_geometry(marker, resolved_semantic)
        else:
            kind = GeometryKind.ARC_ELLIPSE
            geometry = ellipse
    elif resolved_semantic == "parabola":
        parabola = _marker_parabola_geometry(marker, coordinates_by_index)
        if parabola is None:
            kind = GeometryKind.NATIVE
            geometry = _native_marker_geometry(marker, resolved_semantic)
        else:
            kind = GeometryKind.ARC_PARABOLA
            geometry = parabola
    elif resolved_semantic == "spline":
        spline = _marker_spline_geometry(marker, coordinates_by_index)
        if spline is None:
            kind = GeometryKind.NATIVE
            geometry = _native_marker_geometry(marker, resolved_semantic)
        else:
            kind = GeometryKind.SPLINE
            geometry = spline
    else:
        kind = GeometryKind.NATIVE
        geometry = _native_marker_geometry(marker, resolved_semantic)
    return SketchEntity(
        id=entity_id,
        kind=kind,
        geometry=geometry,
        construction=marker.construction,
        provenance=_provenance(
            f"{sketch.object_id}:{marker.offset}",
            marker.offset,
            marker.length,
            "sketch-native-marker",
            stream=sketch.native_stream,
        ),
        attributes=frozen_mapping(
            {
                "native_kind": marker.native_kind,
                "native_locus": marker.locus,
                "profile_role": marker.profile_role,
                "state": marker.state,
                "object_index": marker.object_index,
                "local_id": marker.local_id,
                "endpoint_indices": marker.endpoint_indices,
                "semantic": resolved_semantic,
                "marker_prefix": marker.prefix,
            }
        ),
    )


def _marker_curve_semantic(marker: NativeMarker) -> str:
    endpoints = marker.endpoint_indices
    if endpoints is None:
        return marker.semantic
    if marker.semantic == "line" and b"cptsSplineList_c" not in marker.data[:192]:
        return "line"
    if len(marker.data) >= 102 and marker.data[86:102] == b"\xfe\xff\xff\xff" * 4:
        return "circle" if endpoints[0] == endpoints[1] else "arc"
    if (
        marker.length == 92 or marker.length == 104 and endpoints[0] != endpoints[1]
    ) and (marker.locus == "05000100" or marker.profile_role == 1):
        return "line"
    if marker.length in {112, 116}:
        return "circle" if endpoints[0] == endpoints[1] else "arc"
    if marker.length == 104:
        return "ellipse"
    if marker.length == 108:
        return "arc_ellipse"
    if marker.length == 124:
        return "parabola"
    if marker.length == 128:
        return "conic"
    if marker.length > 128:
        return "spline"
    return marker.semantic


def _marker_curve_reference_indices(
    marker: NativeMarker, semantic: str
) -> tuple[int, ...]:
    result = list(marker.endpoint_indices or ())
    if semantic in {"circle", "arc"} and len(marker.data) >= 86:
        result.append(struct.unpack_from("<H", marker.data, 84)[0])
    elif semantic in {"ellipse", "arc_ellipse"} and len(marker.data) >= 94:
        result.extend(struct.unpack_from("<5H", marker.data, 84))
    elif semantic == "parabola" and len(marker.data) >= 88:
        result.extend(struct.unpack_from("<2I", marker.data, 80))
    elif semantic == "conic" and len(marker.data) >= 96:
        result.extend(struct.unpack_from("<2I", marker.data, 88))
    elif semantic == "spline":
        result.extend(_marker_spline_reference_indices(marker.data))
    return tuple(dict.fromkeys(result))


def _marker_spline_reference_indices(data: bytes) -> tuple[int, ...]:
    result: list[int] = []
    for offset in range(max(0, len(data) - 11)):
        if data[offset : offset + 2] != b"\xa7\x80":
            continue
        if data[offset + 4 : offset + 12] != b"\xff\xff\xff\xff\0\0\0\0":
            continue
        result.append(struct.unpack_from("<H", data, offset + 2)[0])
    return tuple(dict.fromkeys(result))


def _marker_object_reference_indices(data: bytes) -> tuple[int, ...]:
    result: list[int] = []
    for offset in range(max(0, len(data) - 11)):
        if data[offset] not in {0xA7, 0xB2, 0xB7, 0xC7} or data[offset + 1] != 0x80:
            continue
        if data[offset + 4 : offset + 12] != b"\xff\xff\xff\xff\0\0\0\0":
            continue
        result.append(struct.unpack_from("<H", data, offset + 2)[0])
    return tuple(dict.fromkeys(result))


def _marker_circular_geometry(
    marker: NativeMarker,
    coordinates: tuple[tuple[float, float] | None, ...],
    semantic: str,
) -> tuple[GeometryKind, CircleGeometry | ArcGeometry] | None:
    if marker.endpoint_indices is None or len(marker.data) < 86:
        return None
    center = _coordinate_reference(
        coordinates, struct.unpack_from("<H", marker.data, 84)[0]
    )
    start = _coordinate_reference(coordinates, marker.endpoint_indices[0])
    end = _coordinate_reference(coordinates, marker.endpoint_indices[1])
    if center is None or start is None:
        return None
    radius = math.dist(center, start)
    if not math.isfinite(radius) or radius <= 1e-12:
        return None
    if semantic == "circle":
        return GeometryKind.CIRCLE, CircleGeometry(Vector2(*center), radius)
    if end is None:
        return None
    start_angle = math.atan2(start[1] - center[1], start[0] - center[0])
    end_angle = math.atan2(end[1] - center[1], end[0] - center[0])
    if struct.unpack_from("<I", marker.data, 80)[0] == 0xFFFFFFFF:
        start_angle, end_angle = end_angle, start_angle
    return (
        GeometryKind.ARC,
        ArcGeometry(Vector2(*center), radius, start_angle, end_angle),
    )


def _marker_ellipse_geometry(
    marker: NativeMarker,
    coordinates: tuple[tuple[float, float] | None, ...],
) -> EllipseGeometry | None:
    if len(marker.data) < 90:
        return None
    center_index, major_index, minor_index = struct.unpack_from("<3H", marker.data, 84)
    center = _coordinate_reference(coordinates, center_index)
    major = _coordinate_reference(coordinates, major_index)
    minor = _coordinate_reference(coordinates, minor_index)
    if center is None or major is None or minor is None:
        return None
    major_radius = math.dist(center, major)
    minor_radius = math.dist(center, minor)
    if major_radius <= 1e-12 or minor_radius <= 1e-12:
        return None
    return EllipseGeometry(
        Vector2(*center),
        Vector2(
            (major[0] - center[0]) / major_radius,
            (major[1] - center[1]) / major_radius,
        ),
        major_radius,
        minor_radius,
    )


def _marker_arc_ellipse_geometry(
    marker: NativeMarker,
    coordinates: tuple[tuple[float, float] | None, ...],
) -> ArcEllipseGeometry | None:
    ellipse = _marker_ellipse_geometry(marker, coordinates)
    if ellipse is None or marker.endpoint_indices is None:
        return None
    start = _coordinate_reference(coordinates, marker.endpoint_indices[0])
    end = _coordinate_reference(coordinates, marker.endpoint_indices[1])
    if start is None or end is None:
        return None
    u = ellipse.major_axis
    v = Vector2(-u.y, u.x)

    def parameter(point: tuple[float, float]) -> float:
        delta = Vector2(point[0] - ellipse.center.x, point[1] - ellipse.center.y)
        return math.atan2(
            (delta.x * v.x + delta.y * v.y) / ellipse.minor_radius,
            (delta.x * u.x + delta.y * u.y) / ellipse.major_radius,
        )

    return ArcEllipseGeometry(
        ellipse.center,
        ellipse.major_axis,
        ellipse.major_radius,
        ellipse.minor_radius,
        parameter(start),
        parameter(end),
    )


def _marker_spline_geometry(
    marker: NativeMarker,
    coordinates: tuple[tuple[float, float] | None, ...],
) -> SplineGeometry | None:
    references = _marker_spline_reference_indices(marker.data)
    points = tuple(
        point
        for index in references
        if (point := _coordinate_reference(coordinates, index)) is not None
    )
    if len(points) < 2:
        return None
    degree = min(3, len(points) - 1)
    return SplineGeometry(tuple(Vector2(*point) for point in points), degree)


def _marker_parabola_geometry(
    marker: NativeMarker,
    coordinates: tuple[tuple[float, float] | None, ...],
) -> ArcParabolaGeometry | None:
    if marker.endpoint_indices is None or len(marker.data) < 88:
        return None
    focus_index, apex_index = struct.unpack_from("<2I", marker.data, 80)
    focus = _coordinate_reference(coordinates, focus_index)
    apex = _coordinate_reference(coordinates, apex_index)
    start = _coordinate_reference(coordinates, marker.endpoint_indices[0])
    end = _coordinate_reference(coordinates, marker.endpoint_indices[1])
    if focus is None or apex is None or start is None or end is None:
        return None
    focal_length = math.dist(focus, apex)
    if not math.isfinite(focal_length) or focal_length <= 1e-12:
        return None
    axis = Vector2(
        (focus[0] - apex[0]) / focal_length,
        (focus[1] - apex[1]) / focal_length,
    )
    perpendicular = Vector2(-axis.y, axis.x)

    def parameter(point: tuple[float, float]) -> float:
        delta = Vector2(point[0] - apex[0], point[1] - apex[1])
        return (delta.x * perpendicular.x + delta.y * perpendicular.y) / (
            2.0 * focal_length
        )

    limits = sorted((parameter(start), parameter(end)))
    return ArcParabolaGeometry(
        Vector2(*apex),
        axis,
        focal_length,
        limits[0],
        limits[1],
    )


def _coordinate_reference(
    coordinates: tuple[tuple[float, float] | None, ...], index: int
) -> tuple[float, float] | None:
    return coordinates[index] if 0 <= index < len(coordinates) else None


def _native_marker_geometry(
    marker: NativeMarker, entity_type: str | None = None
) -> NativeGeometry:
    return NativeGeometry(
        format_id=_FORMAT_ID,
        entity_type=entity_type or marker.semantic,
        data=frozen_mapping(
            {
                "native_kind": marker.native_kind,
                "locus": marker.locus,
                "coordinates_mm": marker.coordinates_mm,
                "endpoint_indices": marker.endpoint_indices,
                "record_data": marker.data,
            }
        ),
    )


def _sketch_constraints(
    sketch: NativeSketch,
    reference_map: dict[str, str],
    parameter_ids: set[str],
) -> tuple[SketchConstraint, ...]:
    result: list[SketchConstraint] = []
    dimension_usage: defaultdict[float, int] = defaultdict(int)
    candidates: defaultdict[float, list[tuple[str, str]]] = defaultdict(list)
    for profile_index, profile in enumerate(sketch.profiles):
        if profile.kind != "rectangle":
            continue
        width = round(profile.coordinates[2] - profile.coordinates[0], 9)
        height = round(profile.coordinates[3] - profile.coordinates[1], 9)
        candidates[width].append(
            (_profile_edge_id(sketch.object_id, profile_index, 0), "distance_x")
        )
        candidates[height].append(
            (_profile_edge_id(sketch.object_id, profile_index, 1), "distance_y")
        )
    dimensions_by_name: defaultdict[str, list[NativeDimension]] = defaultdict(list)
    parameter_ids_by_name: defaultdict[str, list[str]] = defaultdict(list)
    for dimension, parameter_id in _parameter_entries(
        sketch.object_id, sketch.dimensions
    ):
        dimensions_by_name[dimension.name].append(dimension)
        parameter_ids_by_name[dimension.name].append(parameter_id)
    parameter_usage: defaultdict[str, int] = defaultdict(int)
    constraint_id_usage: defaultdict[str, int] = defaultdict(int)
    for constraint in sketch.constraints:
        resolved_references = [
            reference_map.get(reference) for reference in constraint.references
        ]
        references = (
            [ConstraintReference(reference) for reference in resolved_references]
            if resolved_references and all(resolved_references)
            else []
        )
        kind = constraint.kind
        native_name = (
            constraint.parameter.rsplit(":", 1)[-1]
            if constraint.parameter is not None
            else ""
        )
        occurrence = parameter_usage[native_name] if native_name else 0
        dimensions = dimensions_by_name.get(native_name, [])
        dimension = (
            dimensions[min(occurrence, len(dimensions) - 1)] if dimensions else None
        )
        if not references and constraint.parameter is not None:
            if dimension is not None:
                key = round(dimension.value_mm, 9)
                available = candidates.get(key, [])
                if available:
                    index = dimension_usage[key] % len(available)
                    entity_id, inferred_kind = available[index]
                    dimension_usage[key] += 1
                    references = [ConstraintReference(entity_id)]
                    kind = inferred_kind
        parameter_id = None
        if constraint.parameter is not None:
            available_parameter_ids = parameter_ids_by_name.get(native_name, [])
            if available_parameter_ids:
                candidate = available_parameter_ids[
                    min(occurrence, len(available_parameter_ids) - 1)
                ]
                if candidate in parameter_ids:
                    parameter_id = candidate
            parameter_usage[native_name] += 1
        constraint_id_usage[constraint.id] += 1
        constraint_occurrence = constraint_id_usage[constraint.id]
        constraint_id = f"sldprt:constraint:{constraint.id}"
        if constraint_occurrence > 1:
            constraint_id += f":{constraint_occurrence}"
        result.append(
            SketchConstraint(
                id=constraint_id,
                kind=kind,
                references=tuple(references),
                parameter_id=parameter_id,
                driving=dimension.native_role != "display" if dimension else True,
                provenance=(
                    _provenance(
                        constraint.id,
                        constraint.native_offset,
                        8,
                        "sketch-constraint",
                        stream=sketch.native_stream,
                    )
                    if constraint.native_offset is not None
                    else None
                ),
                attributes=frozen_mapping(
                    {
                        "native_code": constraint.native_code,
                        "native_references": constraint.references,
                        "native_value": constraint.value,
                        "parameter_occurrence": occurrence + 1 if native_name else None,
                    }
                ),
            )
        )
    for profile_index, profile in enumerate(sketch.profiles):
        if profile.kind != "rectangle":
            continue
        for edge_index in range(4):
            current = _profile_edge_id(sketch.object_id, profile_index, edge_index)
            following = _profile_edge_id(
                sketch.object_id, profile_index, (edge_index + 1) % 4
            )
            result.append(
                SketchConstraint(
                    id=(
                        f"sldprt:constraint:{sketch.object_id}:profile:"
                        f"{profile_index}:coincident:{edge_index}"
                    ),
                    kind="coincident",
                    references=(
                        ConstraintReference(current, "end"),
                        ConstraintReference(following, "start"),
                    ),
                    attributes=frozen_mapping({"inferred": True}),
                )
            )
    return tuple(result)


def _selections(model: NativeModel) -> tuple[Selection, ...]:
    result: list[Selection] = []
    for operation in model.operations:
        if not operation.selection_offsets:
            continue
        for producer, local_id, offsets in _operation_selection_entries(operation):
            selection_id = _operation_selection_id(operation, producer, local_id)
            kind = operation.selection_kind
            result.append(
                Selection(
                    id=selection_id,
                    name=f"{operation.name} {kind} {local_id}",
                    path=(
                        SelectionPathElement(
                            entity_kind="feature",
                            entity_id=_feature_id(producer),
                            subelement=f"{kind}:{local_id}",
                        ),
                    ),
                    query=frozen_mapping(
                        {
                            "native_producer_id": producer,
                            "native_local_id": local_id,
                            "native_identity": "7dc39425ad49b2547dc39425ad49b254",
                            "topology_role": (
                                "extrusion_terminal_profile_boundary"
                                if operation.kind == "fillet"
                                else f"native_{kind}"
                            ),
                        }
                    ),
                    provenance=Provenance(
                        adapter=_FORMAT_ID,
                        native_id=f"{operation.object_id}:{kind}:{local_id}",
                        spans=tuple(
                            ProvenanceSpan(
                                operation.native_stream,
                                offset,
                                38,
                                f"{kind}-selection",
                            )
                            for offset in offsets
                        ),
                    ),
                )
            )
    return (*result, *_direction_axis_selections(model))


def _direction_axis_selections(model: NativeModel) -> tuple[Selection, ...]:
    sketch_by_id = {sketch.object_id: sketch for sketch in model.sketches}
    result: list[Selection] = []
    for operation in model.operations:
        if operation.profile_id is None:
            continue
        sketch = sketch_by_id.get(operation.profile_id)
        subelement = operation_axis_subelement(operation, sketch)
        if sketch is None or subelement is None:
            continue
        result.append(
            Selection(
                id=(
                    f"sldprt:selection:{operation.object_id}:axis:"
                    f"{sketch.object_id}:{subelement}"
                ),
                name=f"{operation.name} direction {subelement}",
                path=(
                    SelectionPathElement(
                        entity_kind="native",
                        entity_id=sketch.name,
                        subelement=subelement,
                    ),
                ),
                query=frozen_mapping(
                    {
                        "native_owner_id": operation.object_id,
                        "native_target_id": sketch.object_id,
                        "topology_role": DIRECTION_AXIS_ROLE,
                    }
                ),
                provenance=Provenance(
                    adapter=_FORMAT_ID,
                    native_id=f"{operation.object_id}:axis:{subelement}",
                    spans=(
                        ProvenanceSpan(
                            operation.native_stream,
                            operation.native_offset,
                            operation.native_end - operation.native_offset,
                            "direction-axis",
                        ),
                    ),
                ),
            )
        )
    return tuple(result)


def _operation_selection_entries(
    operation: NativeOperation,
) -> tuple[tuple[int, int, tuple[int, ...]], ...]:
    references = operation.selection_references
    if not references:
        producer = operation.dependencies[-1] if operation.dependencies else 0
        references = tuple(
            (producer, local_id) for local_id in operation.selected_local_ids
        )
    aligned = len(operation.selection_offsets) == len(references)
    return tuple(
        (
            producer,
            local_id,
            (
                (operation.selection_offsets[index],)
                if aligned
                else operation.selection_offsets
            ),
        )
        for index, (producer, local_id) in enumerate(references)
    )


def _operation_selection_id(
    operation: NativeOperation, producer: int, local_id: int
) -> str:
    duplicate = (
        sum(
            reference_local == local_id
            for _, reference_local in operation.selection_references
        )
        > 1
    )
    return _selection_id(
        operation.object_id,
        local_id,
        operation.selection_kind,
        producer if duplicate else None,
    )


def _timeline(
    model: NativeModel, selections: tuple[Selection, ...]
) -> tuple[FeatureStep, ...]:
    operation_by_id = {operation.object_id: operation for operation in model.operations}
    sketch_by_id = {sketch.object_id: sketch for sketch in model.sketches}
    plane_by_id = {plane.object_id: plane for plane in model.planes}
    feature_ids = {feature.object_id for feature in model.features}
    order_by_id = {
        feature.object_id: order for order, feature in enumerate(model.features)
    }
    selection_ids = {selection.id for selection in selections}
    principal_plane_ids = {plane.object_id for plane in model.planes if plane.principal}
    previous_operation: int | None = None
    result: list[FeatureStep] = []
    for order, feature in enumerate(model.features):
        operation = operation_by_id.get(feature.object_id)
        sketch = sketch_by_id.get(feature.object_id)
        inputs: list[int] = []
        if operation is not None:
            inputs.extend(operation.dependencies)
        elif sketch is not None:
            inputs.append(sketch.support_plane_id)
        elif feature.object_id in plane_by_id:
            reference_ids = plane_by_id[feature.object_id].reference_ids
            inputs.extend(reference_ids)
            if (
                not reference_ids
                and feature.object_id not in principal_plane_ids
                and previous_operation is not None
            ):
                inputs.append(previous_operation)
        dependencies = tuple(
            _feature_id(native_id)
            for native_id in dict.fromkeys(inputs)
            if native_id in feature_ids and order_by_id[native_id] < order
        )
        parameter_ids = tuple(
            parameter_id
            for dimension, parameter_id in _parameter_entries(
                feature.object_id, feature.dimensions
            )
        )
        attributes: dict[str, Any] = {
            "native_object_id": feature.object_id,
            "native_type": feature.kind,
            "xml_tag": feature.xml_tag,
            "native_properties": feature.properties,
        }
        operation_value: BooleanOperation | str | None = None
        selected: tuple[str, ...] = ()
        if operation is not None:
            attributes.update(_operation_attributes(operation))
            if operation.kind == "join":
                operation_value = BooleanOperation.JOIN
            elif operation.kind == "cut":
                operation_value = BooleanOperation.CUT
            elif operation.kind in {
                "fillet",
                "chamfer",
                "shell",
                "dome",
                "scale",
                "move_body",
            }:
                operation_value = None
            elif operation.kind == "revolve_join":
                operation_value = BooleanOperation.JOIN
            elif operation.kind == "revolve_cut":
                operation_value = BooleanOperation.CUT
            elif operation.kind == "hole":
                operation_value = BooleanOperation.CUT
            elif operation.kind == "combine_join":
                operation_value = BooleanOperation.JOIN
            elif operation.kind == "surface":
                operation_value = BooleanOperation.CREATE
            else:
                operation_value = operation.kind
            selected = tuple(
                selection_id
                for producer, local_id, _ in _operation_selection_entries(operation)
                for selection_id in (
                    _operation_selection_id(operation, producer, local_id),
                )
                if selection_id in selection_ids
            )
            if operation.kind != "surface":
                previous_operation = operation.object_id
        result.append(
            FeatureStep(
                id=_feature_id(feature.object_id),
                name=feature.name,
                kind=_feature_kind(feature),
                order=order,
                input_feature_ids=dependencies,
                sketch_id=(
                    _sketch_id(operation.profile_id)
                    if operation is not None and operation.profile_id in sketch_by_id
                    else _sketch_id(feature.object_id) if sketch is not None else None
                ),
                parameter_ids=parameter_ids,
                operation=operation_value,
                definition=_feature_definition(
                    feature,
                    operation,
                    sketch_by_id,
                    plane_by_id,
                ),
                selection_ids=selected,
                provenance=_feature_provenance(feature),
                attributes=frozen_mapping(attributes),
            )
        )
    return tuple(result)


def _solid_body_feature(
    features: tuple[NativeFeature, ...],
) -> NativeFeature | None:
    return next(
        (
            feature
            for feature in features
            if feature.kind.casefold().strip() in SOLID_BODY_FEATURE_TYPES
        ),
        None,
    )


def _final_body_feature_id(
    timeline: tuple[FeatureStep, ...], operation_feature_ids: frozenset[str]
) -> str:
    candidate = next(
        (
            feature
            for feature in reversed(timeline)
            if feature.id in operation_feature_ids
            or (
                isinstance(feature.kind, FeatureKind)
                and feature.kind != FeatureKind.REFERENCE
                and feature.kind != FeatureKind.SURFACE
                and feature.kind != FeatureKind.NATIVE
            )
        ),
        None,
    )
    if candidate is not None:
        return candidate.id
    return timeline[-1].id if timeline else ""


def _operation_attributes(operation: NativeOperation) -> dict[str, Any]:
    result: dict[str, Any] = {
        "profile_native_id": operation.profile_id,
        "native_dependencies": operation.dependencies,
        "family_code": operation.family_code,
        "operation_code": operation.operation_code,
        "schema_code": operation.schema_code,
        "direction_code": operation.direction_code,
        "termination_code": operation.termination_code,
        "native_selection_offsets": operation.selection_offsets,
        "selected_local_ids": operation.selected_local_ids,
        "native_selection_references": operation.selection_references,
        "selection_kind": operation.selection_kind,
        "mode": operation.mode,
    }
    if operation.length_mm is not None:
        result.update(
            {
                "length_mm": operation.length_mm,
                "direction_multiplier": (
                    -1 if operation.kind in {"cut", "revolve_cut", "hole"} else 1
                ),
                "end_condition": (
                    "blind"
                    if operation.termination_code == 0
                    else f"native:{operation.termination_code}"
                ),
            }
        )
    if operation.radius_mm is not None:
        result["radius_mm"] = operation.radius_mm
    if operation.angle_degrees is not None:
        result["angle_degrees"] = operation.angle_degrees
    if operation.diameter_mm is not None:
        result["diameter_mm"] = operation.diameter_mm
    if operation.second_length_mm is not None:
        result["second_length_mm"] = operation.second_length_mm
    if operation.axis_marker_offset is not None:
        result["axis_marker_offset"] = operation.axis_marker_offset
    if operation.axis_source_kind is not None:
        result["axis_source_kind"] = operation.axis_source_kind
    if operation.axis_source_id is not None:
        result["axis_source_id"] = operation.axis_source_id
    if operation.axis_source_offset is not None:
        result["axis_source_offset"] = operation.axis_source_offset
    if operation.end_spec_offset is not None:
        result["end_spec_offset"] = operation.end_spec_offset
    if operation.translation_mm is not None:
        result["translation_mm"] = operation.translation_mm
    if operation.scale_factors is not None:
        result["scale_factors"] = operation.scale_factors
    return result


def _feature_definition(
    feature: NativeFeature,
    operation: NativeOperation | None,
    sketches: Mapping[int, NativeSketch],
    planes: Mapping[int, NativePlane],
) -> (
    ExtrusionFeature
    | FilletFeature
    | RevolutionFeature
    | HoleFeature
    | ChamferFeature
    | ShellFeature
    | ReferencePlaneFeature
    | DomeFeature
    | MoveBodyFeature
    | CombineFeature
    | ScaleFeature
    | NativeFeatureDefinition
):
    if (
        operation is not None
        and operation.kind in {"join", "cut", "surface"}
        and operation.length_mm is not None
    ):
        return ExtrusionFeature(
            length=ParameterValue(operation.length_mm, ValueKind.LENGTH, "mm"),
            end_condition=(
                ExtrusionEndCondition.BLIND
                if operation.termination_code == 0
                else f"native:{operation.termination_code}"
            ),
            reversed=operation.kind == "cut",
            second_length=(
                ParameterValue(
                    operation.second_length_mm,
                    ValueKind.LENGTH,
                    "mm",
                )
                if operation.second_length_mm is not None
                else None
            ),
        )
    if (
        operation is not None
        and operation.kind in {"revolve_join", "revolve_cut"}
        and operation.angle_degrees is not None
        and operation.profile_id in sketches
        and operation.axis_marker_offset is not None
    ):
        return RevolutionFeature(
            angle=ParameterValue(
                operation.angle_degrees,
                ValueKind.ANGLE,
                "deg",
            ),
            axis_entity_id=_marker_id(
                operation.profile_id,
                operation.axis_marker_offset,
            ),
            reversed=operation.kind == "revolve_cut",
        )
    if (
        operation is not None
        and operation.kind in {"revolve_join", "revolve_cut"}
        and operation.angle_degrees is not None
        and operation.axis_source_kind is not None
        and operation.axis_source_id is not None
    ):
        return RevolutionFeature(
            angle=ParameterValue(
                operation.angle_degrees,
                ValueKind.ANGLE,
                "deg",
            ),
            axis_entity_id=_axis_source_id(
                operation.axis_source_kind,
                operation.axis_source_id,
            ),
            reversed=operation.kind == "revolve_cut",
        )
    if (
        operation is not None
        and operation.kind == "hole"
        and operation.diameter_mm is not None
        and operation.length_mm is not None
    ):
        return HoleFeature(
            diameter=ParameterValue(
                operation.diameter_mm,
                ValueKind.LENGTH,
                "mm",
            ),
            depth=ParameterValue(
                operation.length_mm,
                ValueKind.LENGTH,
                "mm",
            ),
        )
    if (
        operation is not None
        and operation.kind == "fillet"
        and operation.radius_mm is not None
    ):
        return FilletFeature(
            radius=ParameterValue(operation.radius_mm, ValueKind.LENGTH, "mm")
        )
    if (
        operation is not None
        and operation.kind == "chamfer"
        and operation.length_mm is not None
        and operation.mode == "equal_distance"
    ):
        return ChamferFeature(
            distance=ParameterValue(
                operation.length_mm,
                ValueKind.LENGTH,
                "mm",
            )
        )
    if (
        operation is not None
        and operation.kind == "shell"
        and operation.length_mm is not None
    ):
        return ShellFeature(
            thickness=ParameterValue(
                operation.length_mm,
                ValueKind.LENGTH,
                "mm",
            )
        )
    if (
        operation is not None
        and operation.kind == "dome"
        and operation.length_mm is not None
    ):
        return DomeFeature(
            height=ParameterValue(
                operation.length_mm,
                ValueKind.LENGTH,
                "mm",
            )
        )
    if operation is not None and operation.kind == "move_body":
        translation = operation.translation_mm
        if translation is not None:
            return MoveBodyFeature(translation=Vector3(*translation))
    if operation is not None and operation.kind == "combine_join":
        return CombineFeature(BooleanOperation.JOIN)
    if operation is not None and operation.kind == "scale":
        factors = operation.scale_factors
        if factors is not None:
            return ScaleFeature(Vector3(*factors))
    plane = planes.get(feature.object_id)
    reference_ids = plane.reference_ids if plane is not None else ()
    offset = _operation_dimension_value(feature.dimensions, "offset")
    if plane is not None and len(reference_ids) == 1 and offset is not None:
        return ReferencePlaneFeature(
            support_plane_id=_plane_id(feature.object_id),
            reference_plane_id=_plane_id(reference_ids[0]),
            offset=ParameterValue(offset, ValueKind.LENGTH, "mm"),
        )
    return NativeFeatureDefinition(
        format_id=_FORMAT_ID,
        type_id=feature.kind or feature.xml_tag,
        object_data=frozen_mapping(
            {
                "native_object_id": feature.object_id,
                "native_class": feature.class_name,
                "native_stream": feature.native_stream,
                "xml_tag": feature.xml_tag,
                "properties": feature.properties,
                "dimensions": tuple(
                    {
                        "name": dimension.name,
                        "value_mm": dimension.value_mm,
                        "kind": dimension.kind,
                        "source_text": dimension.source_text,
                        "native_value": dimension.native_value,
                        "native_offset": dimension.native_offset,
                        "native_role": dimension.native_role,
                        "operands": tuple(
                            {
                                "offset": operand.offset,
                                "kind_code": operand.kind_code,
                                "entity_index": operand.entity_index,
                            }
                            for operand in dimension.operands
                        ),
                    }
                    for dimension in feature.dimensions
                ),
                "record_data": feature.data,
                "operation": (
                    _operation_attributes(operation) if operation is not None else None
                ),
            }
        ),
    )


def _operation_dimension_value(
    dimensions: tuple[NativeDimension, ...], kind: str
) -> float | None:
    return next(
        (dimension.value_mm for dimension in dimensions if dimension.kind == kind),
        None,
    )


def _feature_kind(feature: NativeFeature) -> FeatureKind:
    if getattr(feature, "class_name", "") in {"moSketchHole", "moHoleWzd_c"}:
        return FeatureKind.HOLE
    return _FEATURE_KIND_BY_NATIVE.get(
        feature.kind.casefold().strip(), FeatureKind.NATIVE
    )


def _brep_payloads(
    archive: SldprtArchive, options: ReadOptions
) -> tuple[tuple[BrepPayload, ...], tuple[Diagnostic, ...]]:
    if not options.include_brep:
        return (), ()
    payloads: list[BrepPayload] = []
    diagnostics: list[Diagnostic] = []
    for record in archive.records:
        if not contains_parasolid_payload(record.data):
            continue
        try:
            decoded = decode_partition_stream(record.data, record.name)
        except SldprtFormatError as exc:
            if options.strict:
                raise
            diagnostics.append(
                Diagnostic(
                    code="sldprt.parasolid_decode_failed",
                    message=str(exc),
                    severity=Severity.WARNING,
                    attributes=frozen_mapping({"stream": record.name}),
                )
            )
            continue
        for native in decoded:
            payloads.append(_brep_payload(len(payloads), native))
    if not payloads and options.strict:
        raise SldprtFormatError("SLDPRT contains no readable Parasolid payload")
    return tuple(payloads), tuple(diagnostics)


def _brep_payload(index: int, native: ParasolidPayload) -> BrepPayload:
    return BrepPayload(
        id=f"sldprt:brep:{index}",
        format_id="parasolid",
        kind=native.kind,
        schema=native.schema,
        sha256=native.sha256,
        data=native.data,
        source_stream=native.stream,
        provenance=Provenance(
            adapter=_FORMAT_ID,
            native_id=f"{native.stream}:{native.wrapper_offset}",
            spans=(
                ProvenanceSpan(
                    native.stream,
                    native.wrapper_offset,
                    native.compressed_offset
                    + native.compressed_size
                    - native.wrapper_offset,
                    "parasolid-wrapper",
                ),
            ),
        ),
        attributes=frozen_mapping(
            {
                "description": native.description,
                "wrapper_offset": native.wrapper_offset,
                "magic_offset": native.magic_offset,
                "compressed_offset": native.compressed_offset,
                "compressed_size": native.compressed_size,
                "uncompressed_size": native.uncompressed_size,
            }
        ),
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )


def _typed_brep(payloads: Sequence[BrepPayload]) -> BrepModel | None:
    groups: dict[str, list[BrepPayload]] = {}
    for index, payload in enumerate(payloads):
        groups.setdefault(payload.source_stream or f"payload:{index}", []).append(
            payload
        )
    models: list[BrepModel] = []
    for group in groups.values():
        decoded = tuple(
            model
            for payload in group
            if payload.data is not None
            and (model := decode_brep_model(payload.data)) is not None
        )
        if len(decoded) == 1:
            models.append(decoded[0])
    return models[0] if len(models) == 1 else None


def _bounding_box(model: NativeModel) -> BoundingBox | None:
    sketch_by_id = {sketch.object_id: sketch for sketch in model.sketches}
    plane_by_id = {plane.object_id: plane for plane in model.planes}
    points: list[tuple[float, float, float]] = []
    for operation in model.operations:
        if operation.kind != "join" or operation.profile_id is None:
            continue
        sketch = sketch_by_id.get(operation.profile_id)
        if sketch is None:
            continue
        plane = plane_by_id.get(sketch.support_plane_id)
        if plane is None or operation.length_mm is None:
            continue
        direction = tuple(value * operation.length_mm for value in plane.normal)
        for profile in sketch.profiles:
            for local in _profile_extrema(profile):
                base = tuple(
                    plane.origin_mm[index]
                    + plane.u_axis[index] * local[0]
                    + plane.v_axis[index] * local[1]
                    for index in range(3)
                )
                points.append(base)
                points.append(
                    tuple(base[index] + direction[index] for index in range(3))
                )
    if not points:
        return None
    return BoundingBox(
        minimum=Vector3(*(min(point[index] for point in points) for index in range(3))),
        maximum=Vector3(*(max(point[index] for point in points) for index in range(3))),
    )


def _profile_extrema(profile: NativeProfile) -> tuple[tuple[float, float], ...]:
    if profile.kind == "rectangle":
        x0, y0, x1, y1 = profile.coordinates
        return ((x0, y0), (x0, y1), (x1, y0), (x1, y1))
    if profile.kind == "circle":
        x, y, radius = profile.coordinates
        return (
            (x - radius, y),
            (x + radius, y),
            (x, y - radius),
            (x, y + radius),
        )
    return ()


def _feature_provenance(feature: NativeFeature) -> Provenance:
    return _provenance(
        str(feature.object_id),
        feature.native_offset,
        (
            feature.native_end - feature.native_offset
            if feature.native_offset is not None and feature.native_end is not None
            else None
        ),
        "feature-record",
        confidence=1.0 if feature.native_offset is not None else 0.6,
        stream=feature.native_stream,
    )


def _feature_span_provenance(sketch: NativeSketch) -> Provenance:
    return _provenance(
        str(sketch.object_id),
        sketch.native_offset,
        sketch.native_end - sketch.native_offset,
        "sketch-record",
        stream=sketch.native_stream,
    )


def _provenance(
    native_id: str,
    offset: int | None,
    length: int | None,
    kind: str,
    *,
    confidence: float = 1.0,
    stream: str = RESOLVED_FEATURES_STREAM,
) -> Provenance:
    spans = (
        (ProvenanceSpan(stream, offset, length or 0, kind),)
        if offset is not None
        else ()
    )
    return Provenance(
        adapter=_FORMAT_ID,
        native_id=native_id,
        confidence=confidence,
        spans=spans,
    )


def _configuration_id(native_id: int) -> str:
    return f"sldprt:configuration:{native_id}"


def _feature_id(native_id: int) -> str:
    return f"sldprt:feature:{native_id}"


def _plane_id(native_id: int) -> str:
    return f"sldprt:plane:{native_id}"


def _sketch_id(native_id: int) -> str:
    return f"sldprt:sketch:{native_id}"


def _parameter_id(native_id: int, name: str) -> str:
    return f"sldprt:parameter:{native_id}:{name}"


def _parameter_entries(
    native_id: int, dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeDimension, str], ...]:
    occurrences: defaultdict[str, int] = defaultdict(int)
    result: list[tuple[NativeDimension, str]] = []
    for dimension in dimensions:
        occurrences[dimension.name] += 1
        occurrence = occurrences[dimension.name]
        parameter_id = _parameter_id(native_id, dimension.name)
        if occurrence > 1:
            parameter_id += f":{occurrence}"
        result.append((dimension, parameter_id))
    return tuple(result)


def _selection_id(
    native_id: int,
    local_id: int,
    kind: str = "edge",
    producer_id: int | None = None,
) -> str:
    producer = f":{producer_id}" if producer_id is not None else ""
    return f"sldprt:selection:{native_id}:{kind}{producer}:{local_id}"


def _profile_id(native_id: int, profile_index: int) -> str:
    return f"sldprt:sketch:{native_id}:profile:{profile_index}"


def _profile_edge_id(native_id: int, profile_index: int, edge_index: int) -> str:
    return f"sldprt:sketch:{native_id}:profile:{profile_index}:edge:{edge_index}"


def _axis_source_id(kind: str, native_id: int) -> str:
    return f"sldprt:{kind}:{native_id}"


def _marker_id(native_id: int, offset: int) -> str:
    return f"sldprt:sketch:{native_id}:native:{offset}"
