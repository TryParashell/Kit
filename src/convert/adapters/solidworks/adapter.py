from __future__ import annotations

from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass, replace
import hashlib
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
    AssemblyData,
    Body,
    BooleanOperation,
    BoundingBox,
    BrepModel,
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    CircleGeometry,
    ComponentDefinition,
    ComponentDocument,
    ComponentInstance,
    ComponentKind,
    Configuration,
    ConstraintReference,
    Diagnostic,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    GeometryKind,
    LineGeometry,
    MateAlignment,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4,
    Mesh,
    NativeFeatureDefinition,
    NativeGeometry,
    Parameter,
    ParameterRole,
    ParameterValue,
    PointGeometry,
    PayloadRole,
    Provenance,
    ProvenanceSpan,
    Selection,
    SelectionPathElement,
    Severity,
    Sketch,
    SketchConstraint,
    SketchEntity,
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
    NativeAssemblyOccurrence,
    NativeMate,
    NativeMateEntity,
    NativeMateList,
    decode_native_assembly,
)
from .container import SldprtArchive, SldprtFormatError, build_sldprt
from .format import (
    COMPONENT_TREE_STREAM,
    CONTAINER_VERSIONS,
    CONTENT_TYPES_STREAM,
    DISPLAY_LISTS_STREAM,
    FORMAT_ID_BY_SUFFIX,
    INFO,
    KEYWORDS_STREAM,
    KIT_DOCUMENT_STREAM,
    KIT_NATIVE_STREAM,
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
    NativeFeature,
    NativeMarker,
    NativeModel,
    NativeOperation,
    NativeProfile,
    NativeSketch,
    decode_native_model,
)
from .parasolid import (
    ParasolidPayload,
    ParasolidWriteError,
    contains_parasolid_payload,
    decode_brep_model,
    decode_partition_stream,
    encode_brep_model,
    is_native_parasolid_payload,
)


_FORMAT_ID = INFO.format_id
_ASSEMBLY_FORMAT_ID = INFO.aliases[0]
_SOURCE_BYTES_KEY = "solidworks_source_bytes"
_SOURCE_SHA256_KEY = "solidworks_source_sha256"
_SOURCE_SEMANTIC_SHA256_KEY = "solidworks_source_semantic_sha256"
_SOURCE_FORMAT_KEY = "solidworks_source_format_id"
_SOURCE_KEYS = frozenset(
    {
        _SOURCE_BYTES_KEY,
        _SOURCE_SHA256_KEY,
        _SOURCE_SEMANTIC_SHA256_KEY,
        _SOURCE_FORMAT_KEY,
    }
)
_NUMBER_TEXT = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


@dataclass(frozen=True, slots=True)
class _GeneratedStreams:
    streams: dict[str, bytes]
    native_brep: str
    native_capabilities: frozenset[Capability]
    compatibility: str
    application_usable: bool
    vendor_loadable: bool


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
        if RESOLVED_FEATURES_STREAM in names and KEYWORDS_STREAM in names:
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
        model = decode_native_model(
            archive.require(KEYWORDS_STREAM), archive.require(RESOLVED_FEATURES_STREAM)
        )
        configurations = _configurations(model, settings.configuration)
        parameters = _parameters(model)
        parameter_ids = {parameter.id for parameter in parameters}
        planes = _planes(model, parameter_ids)
        sketches = _sketches(model, parameter_ids)
        selections = _selections(model)
        timeline = _timeline(model, selections)
        payloads, payload_diagnostics = _brep_payloads(archive, settings)
        brep = _typed_brep(payloads)
        final_feature = _final_body_feature_id(
            timeline,
            frozenset(
                _feature_id(operation.object_id) for operation in model.operations
            ),
        )
        body_feature = _solid_body_feature(model.features)
        bodies = (
            Body(
                id="sldprt:body:1",
                name=body_feature.name if body_feature is not None else "Body 1",
                final_feature_id=final_feature,
                topology=TopologySummary(
                    solid_count=1 if model.operations else 0,
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
            if settings.values.get("portable") is True and document.assembly is not None
            else _preserved_source(document, path)
        )
        diagnostics = document.diagnostics
        if preserved is None:
            template = _source_template(document, path)
            if settings.values.get("allow_non_native", True) is not True:
                kind = "edited native-backed" if template is not None else "source-less"
                raise SldprtFormatError(
                    f"{kind} SOLIDWORKS writing requires "
                    "WriteOptions(values={'allow_non_native': True})"
                )
            streams, native_brep = _generated_streams(document, template)
            file_id = (
                SldprtArchive.from_bytes(template).file_id
                if template is not None
                else int.from_bytes(
                    hashlib.sha256(streams[KIT_DOCUMENT_STREAM]).digest()[:4],
                    "big",
                )
            )
            data = build_sldprt(streams, file_id=file_id or 1)
            mode = "template" if template is not None else "generated"
            native_content = (
                "source-preserved"
                if template is not None
                else (
                    "neutral-brep"
                    if native_brep == "generated"
                    else "parasolid-import" if native_brep == "preserved" else "none"
                )
            )
            diagnostics = (
                *diagnostics,
                Diagnostic(
                    code="sldprt.neutral_write",
                    message=(
                        "neutral edits are stored in the Kit stream and are not "
                        "represented as native SOLIDWORKS feature edits"
                    ),
                    severity=Severity.WARNING,
                ),
            )
            if native_brep.startswith("unsupported:"):
                diagnostics = (
                    *diagnostics,
                    Diagnostic(
                        code="sldprt.native_brep_unsupported",
                        message=native_brep.removeprefix("unsupported:"),
                        severity=Severity.WARNING,
                    ),
                )
        else:
            data = preserved
            mode = "exact"
            native_content = "exact"
            native_brep = "exact"
        compatibility = (
            _replay_compatibility(data)
            if mode == "exact"
            else (
                "native-source-with-kit-neutral"
                if mode == "template"
                else (
                    "native-brep-with-kit-neutral"
                    if native_content in {"neutral-brep", "parasolid-import"}
                    else "kit-neutral-only"
                )
            )
        )
        native_exact = mode == "exact" and compatibility == "native-exact"
        output = _write_destination(destination, data, settings.overwrite)
        archive = SldprtArchive.from_bytes(data, output or "<memory>")
        requirements = (
            ("referenced SOLIDWORKS component files",)
            if mode == "exact" and document.assembly is not None
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
                    "neutral_edits_are_native": native_exact,
                    "vendor_loadable": native_exact,
                    "native_geometry": native_brep
                    in {"exact", "generated", "preserved"},
                    "native_brep": native_brep,
                    "native_history": native_exact,
                    "native_assembly": native_exact and document.assembly is not None,
                    "native_self_contained": native_exact and document.assembly is None,
                    "referenced_files_written": 0,
                    "container_version": archive.format_version,
                    "file_id": archive.file_id,
                    "stream_count": len(archive.records),
                    "runtime": "python-stdlib",
                }
            ),
            requirements=requirements,
            application_usable=native_exact,
            vendor_loadable=native_exact,
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
            "solidworks.container_compatibility": "kit-neutral-only",
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


def _replay_compatibility(data: bytes) -> str:
    archive = SldprtArchive.from_bytes(data)
    return (
        "kit-neutral-only" if KIT_DOCUMENT_STREAM in archive.streams else "native-exact"
    )


def _generated_streams(
    document: CadDocument, template: bytes | None = None
) -> tuple[dict[str, bytes], str]:
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
        return streams, "template"
    configuration = next(
        (item.name for item in portable.configurations if item.active),
        portable.configurations[0].name if portable.configurations else "Default",
    )
    model_name = PureWindowsPath(portable.source.path).stem
    streams = {
        CONTENT_TYPES_STREAM: (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Default Extension="bin" ContentType="application/octet-stream"/>'
            b"</Types>"
        ),
        RELATIONSHIPS_STREAM: (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
        ),
        SOLIDWORKS_STREAM: _solidworks_xml(model_name, configuration),
        KIT_DOCUMENT_STREAM: embedded,
    }
    payload, native_brep = _parasolid_payload(portable)
    if payload is not None:
        streams[PARTITION_STREAM] = payload
    return streams, native_brep


def _parasolid_payload(document: CadDocument) -> tuple[bytes | None, str]:
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
        return max(candidates, key=len), "preserved"
    if document.brep is None or document.assembly is not None:
        return None, "none"
    try:
        return encode_brep_model(document.brep), "generated"
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
    model = decode_native_model(
        archive.require(KEYWORDS_STREAM), archive.require(RESOLVED_FEATURES_STREAM)
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
    documents, document_ids, resolved_paths, document_diagnostics = _assembly_documents(
        adapter, native, index, settings
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
    if unresolved and settings.strict:
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
    if settings.values.get("resolve_components", True) is False:
        return {}
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


def _configurations(
    model: NativeModel, requested: str | None
) -> tuple[Configuration, ...]:
    available = {item.name for item in model.configurations}
    if requested is not None and requested not in available:
        raise SldprtFormatError(
            f"configuration {requested!r} is unavailable; choices are {sorted(available)}"
        )
    active = requested or model.configurations[0].name
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
                    value=ParameterValue(dimension.value_mm, ValueKind.LENGTH, "mm"),
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
                        )
                        if dimension.native_offset is not None
                        else _feature_provenance(feature)
                    ),
                    attributes=frozen_mapping(
                        {
                            "source_text": dimension.source_text,
                            "dimension_kind": dimension.kind,
                            "native_value": native_value,
                            "native_unit": "m",
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
    return tuple(parameters)


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
                                RESOLVED_FEATURES_STREAM,
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
    index_map: dict[int, str] = {}
    coordinates_by_prefix = {
        prefix: tuple(
            marker.coordinates_mm
            for marker in sketch.markers
            if marker.prefix == prefix
        )
        for prefix in {marker.prefix for marker in sketch.markers}
    }
    for marker in sketch.markers:
        if marker.offset in profile_offsets:
            continue
        entity = _marker_entity(sketch, marker, coordinates_by_prefix)
        entities.append(entity)
        if marker.object_index is not None:
            index_map[marker.object_index] = entity.id
    reference_map.update(
        {f"native-index:{index}": entity_id for index, entity_id in index_map.items()}
    )
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
            }
        ),
    )


def _marker_entity(
    sketch: NativeSketch,
    marker: NativeMarker,
    coordinates_by_prefix: dict[str, tuple[tuple[float, float] | None, ...]],
) -> SketchEntity:
    entity_id = _marker_id(sketch.object_id, marker.offset)
    if marker.semantic == "point" and marker.coordinates_mm is not None:
        kind = GeometryKind.POINT
        geometry: Any = PointGeometry(Vector2(*marker.coordinates_mm))
    elif marker.semantic == "line" and marker.endpoint_indices is not None:
        coordinates = coordinates_by_prefix[marker.prefix]
        start = _coordinate_reference(coordinates, marker.endpoint_indices[0])
        end = _coordinate_reference(coordinates, marker.endpoint_indices[1])
        if start is not None and end is not None and start != end:
            kind = GeometryKind.LINE
            geometry = LineGeometry(Vector2(*start), Vector2(*end))
        else:
            kind = GeometryKind.NATIVE
            geometry = _native_marker_geometry(marker)
    else:
        kind = GeometryKind.NATIVE
        geometry = _native_marker_geometry(marker)
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
                "semantic": marker.semantic,
                "marker_prefix": marker.prefix,
            }
        ),
    )


def _coordinate_reference(
    coordinates: tuple[tuple[float, float] | None, ...], index: int
) -> tuple[float, float] | None:
    return coordinates[index] if 0 <= index < len(coordinates) else None


def _native_marker_geometry(marker: NativeMarker) -> NativeGeometry:
    return NativeGeometry(
        format_id=_FORMAT_ID,
        entity_type=marker.semantic,
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
        references = [
            ConstraintReference(reference_map[reference])
            for reference in constraint.references
            if reference in reference_map
        ]
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
        producers = operation.dependencies
        producer = producers[-1] if producers else 0
        for local_id in operation.selected_local_ids:
            result.append(
                Selection(
                    id=_selection_id(operation.object_id, local_id),
                    name=f"{operation.name} edge {local_id}",
                    path=(
                        SelectionPathElement(
                            entity_kind="feature",
                            entity_id=_feature_id(producer),
                            subelement=f"edge:{local_id}",
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
                                else "native_subelement"
                            ),
                        }
                    ),
                    provenance=Provenance(
                        adapter=_FORMAT_ID,
                        native_id=f"{operation.object_id}:edge:{local_id}",
                        spans=tuple(
                            ProvenanceSpan(
                                RESOLVED_FEATURES_STREAM,
                                offset,
                                38,
                                "edge-selection",
                            )
                            for offset in operation.selection_offsets
                        ),
                    ),
                )
            )
    return tuple(result)


def _timeline(
    model: NativeModel, selections: tuple[Selection, ...]
) -> tuple[FeatureStep, ...]:
    operation_by_id = {operation.object_id: operation for operation in model.operations}
    sketch_by_id = {sketch.object_id: sketch for sketch in model.sketches}
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
        elif (
            feature.kind.casefold() in PLANE_FEATURE_TYPES
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
            elif operation.kind == "fillet":
                operation_value = None
            else:
                operation_value = operation.kind
            selected = tuple(
                selection_id
                for local_id in operation.selected_local_ids
                for selection_id in (_selection_id(operation.object_id, local_id),)
                if selection_id in selection_ids
            )
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
                definition=_feature_definition(feature, operation),
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
    }
    if operation.length_mm is not None:
        result.update(
            {
                "length_mm": operation.length_mm,
                "direction_multiplier": -1 if operation.kind == "cut" else 1,
                "end_condition": (
                    "blind"
                    if operation.termination_code == 0
                    else f"native:{operation.termination_code}"
                ),
            }
        )
    if operation.radius_mm is not None:
        result["radius_mm"] = operation.radius_mm
    return result


def _feature_definition(
    feature: NativeFeature, operation: NativeOperation | None
) -> ExtrusionFeature | FilletFeature | NativeFeatureDefinition:
    if operation is not None and operation.length_mm is not None:
        return ExtrusionFeature(
            length=ParameterValue(operation.length_mm, ValueKind.LENGTH, "mm"),
            end_condition=(
                ExtrusionEndCondition.BLIND
                if operation.termination_code == 0
                else f"native:{operation.termination_code}"
            ),
            reversed=operation.kind == "cut",
        )
    if operation is not None and operation.radius_mm is not None:
        return FilletFeature(
            radius=ParameterValue(operation.radius_mm, ValueKind.LENGTH, "mm")
        )
    return NativeFeatureDefinition(
        format_id=_FORMAT_ID,
        type_id=feature.kind or feature.xml_tag,
        object_data=frozen_mapping(
            {
                "native_object_id": feature.object_id,
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


def _feature_kind(feature: NativeFeature) -> FeatureKind:
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
        if any("delta" in payload.kind.casefold() for payload in group):
            continue
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
    )


def _feature_span_provenance(sketch: NativeSketch) -> Provenance:
    return _provenance(
        str(sketch.object_id),
        sketch.native_offset,
        sketch.native_end - sketch.native_offset,
        "sketch-record",
    )


def _provenance(
    native_id: str,
    offset: int | None,
    length: int | None,
    kind: str,
    *,
    confidence: float = 1.0,
) -> Provenance:
    spans = (
        (ProvenanceSpan(RESOLVED_FEATURES_STREAM, offset, length or 0, kind),)
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


def _selection_id(native_id: int, local_id: int) -> str:
    return f"sldprt:selection:{native_id}:edge:{local_id}"


def _profile_id(native_id: int, profile_index: int) -> str:
    return f"sldprt:sketch:{native_id}:profile:{profile_index}"


def _profile_edge_id(native_id: int, profile_index: int, edge_index: int) -> str:
    return f"sldprt:sketch:{native_id}:profile:{profile_index}:edge:{edge_index}"


def _marker_id(native_id: int, offset: int) -> str:
    return f"sldprt:sketch:{native_id}:native:{offset}"
