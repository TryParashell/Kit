# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json as JsonLib
from dataclasses import dataclass as Dataclass
from pathlib import Path as FilePath
from typing import cast


# donor file integrity evidence needs a stable validated representation
@Dataclass(frozen=True, slots=True)
class StreamDigest:
    file: str
    length: int
    sha256: str


# manifest donors combine their resolved stream and container evidence
@Dataclass(frozen=True, slots=True)
class DonorRecord:
    container: dict[str, StreamDigest]
    resolved: StreamDigest


# fixture inventory totals require validation before integrity assertions run
@Dataclass(frozen=True, slots=True)
class DonorManifest:
    container_bytes: int
    donor_count: int
    donors: dict[str, DonorRecord]
    resolved_bytes: int


# container stream names need paired metadata for fixture cross checks
@Dataclass(frozen=True, slots=True)
class ContainerStream:
    file: str
    name: str


# donor metadata needs a concrete contract before topology assertions consume it
@Dataclass(frozen=True, slots=True)
class DonorMetadata:
    arc_counts: tuple[int, ...]
    axis_directions: tuple[tuple[float, float] | None, ...]
    container_streams: tuple[ContainerStream, ...]
    depth_present: tuple[bool, ...]
    donor_id: str
    feature_ids: tuple[int, ...]
    feature_names: tuple[str, ...]
    features: tuple[tuple[str, str, str, str], ...]
    inherited_directions: tuple[bool | None, ...]
    measured: bool
    mo_version: int
    point_counts: tuple[int, ...]
    sketch_ids: tuple[int, ...]
    sketch_names: tuple[str, ...]
    spare_equations: tuple[str, ...]
    spare_plane_frames: tuple[int, ...]
    spare_plane_ids: tuple[int, ...]
    spare_plane_names: tuple[str, ...]
    stream_bytes: int
    swept_arc_counts: tuple[int, ...]


# decoded json needs a checked mapping boundary before typed construction
def ObjectValue(Value: object, Label: str) -> dict[object, object]:
    assert isinstance(Value, dict), f"{Label} must be an object"
    return cast(dict[object, object], Value)


# schema fields must exist before their values can be validated
def FieldValue(RecordInfo: dict[object, object], Label: str) -> object:
    assert Label in RecordInfo, f"missing {Label}"
    return RecordInfo[Label]


# fixture identifiers and digests are only meaningful as strings
def StringValue(Value: object, Label: str) -> str:
    assert isinstance(Value, str), f"{Label} must be a string"
    return Value


# byte counts and versions must exclude boolean json values
def IntegerValue(Value: object, Label: str) -> int:
    assert isinstance(Value, int) and not isinstance(
        Value, bool
    ), f"{Label} must be an integer"
    return Value


# boolean metadata drives explicit feature depth expectations
def BooleanValue(Value: object, Label: str) -> bool:
    assert isinstance(Value, bool), f"{Label} must be a boolean"
    return Value


# array fields need a checked sequence boundary before item parsing
def ArrayValue(Value: object, Label: str) -> list[object]:
    assert isinstance(Value, list), f"{Label} must be an array"
    return cast(list[object], Value)


# manifest digest records share one exact schema across all streams
def ParseStreamDigest(Value: object, Label: str) -> StreamDigest:
    RecordInfo = ObjectValue(Value, Label)
    return StreamDigest(
        file=StringValue(FieldValue(RecordInfo, "file"), f"{Label}.file"),
        length=IntegerValue(FieldValue(RecordInfo, "length"), f"{Label}.length"),
        sha256=StringValue(FieldValue(RecordInfo, "sha256"), f"{Label}.sha256"),
    )


# each donor entry combines independently validated stream inventories
def ParseDonorRecord(Value: object, Label: str) -> DonorRecord:
    RecordInfo = ObjectValue(Value, Label)
    ContainerInfo = ObjectValue(
        FieldValue(RecordInfo, "container"), f"{Label}.container"
    )
    Container = {
        StringValue(NameText, f"{Label}.container key"): ParseStreamDigest(
            Entry, f"{Label}.container"
        )
        for NameText, Entry in ContainerInfo.items()
    }
    return DonorRecord(
        container=Container,
        resolved=ParseStreamDigest(
            FieldValue(RecordInfo, "resolved"), f"{Label}.resolved"
        ),
    )


# manifest decoding must reject malformed fixture inventories at the boundary
def LoadDonorManifest(TargetPath: FilePath) -> DonorManifest:
    assert TargetPath.is_file(), f"missing donor fixture manifest {TargetPath}"
    Payload: object = JsonLib.loads(TargetPath.read_text(encoding="utf-8"))
    RecordInfo = ObjectValue(Payload, str(TargetPath))
    DonorsInfo = ObjectValue(FieldValue(RecordInfo, "donors"), "donors")
    Donors = {
        StringValue(DonorId, "donor id"): ParseDonorRecord(Entry, "donor")
        for DonorId, Entry in DonorsInfo.items()
    }
    return DonorManifest(
        container_bytes=IntegerValue(
            FieldValue(RecordInfo, "container_bytes"), "container_bytes"
        ),
        donor_count=IntegerValue(FieldValue(RecordInfo, "donor_count"), "donor_count"),
        donors=Donors,
        resolved_bytes=IntegerValue(
            FieldValue(RecordInfo, "resolved_bytes"), "resolved_bytes"
        ),
    )


# integer metadata arrays support count consistency assertions across features
def IntegerValues(Value: object, Label: str) -> tuple[int, ...]:
    return tuple(
        IntegerValue(ItemValue, Label) for ItemValue in ArrayValue(Value, Label)
    )


# string metadata arrays support named feature and plane consistency assertions
def StringValues(Value: object, Label: str) -> tuple[str, ...]:
    return tuple(
        StringValue(ItemValue, Label) for ItemValue in ArrayValue(Value, Label)
    )


# depth metadata must align directly with each decoded feature topology
def BooleanValues(Value: object, Label: str) -> tuple[bool, ...]:
    return tuple(
        BooleanValue(ItemValue, Label) for ItemValue in ArrayValue(Value, Label)
    )


# topology fixtures require exactly four string coordinates per feature
def FeatureValues(Value: object, Label: str) -> tuple[tuple[str, str, str, str], ...]:
    Features: list[tuple[str, str, str, str]] = []
    for Entry in ArrayValue(Value, Label):
        Coordinates = ArrayValue(Entry, Label)
        assert len(Coordinates) == 4, f"{Label} must contain four coordinates"
        Features.append(
            (
                StringValue(Coordinates[0], Label),
                StringValue(Coordinates[1], Label),
                StringValue(Coordinates[2], Label),
                StringValue(Coordinates[3], Label),
            )
        )
    return tuple(Features)


# direction vectors retain their optional state while excluding malformed entries
def AxisDirections(Value: object, Label: str) -> tuple[tuple[float, float] | None, ...]:
    Directions: list[tuple[float, float] | None] = []
    for Entry in ArrayValue(Value, Label):
        if Entry is None:
            Directions.append(None)
            continue
        Coordinates = ArrayValue(Entry, Label)
        assert len(Coordinates) == 2, f"{Label} vectors must have two coordinates"
        XValue = Coordinates[0]
        YValue = Coordinates[1]
        assert isinstance(XValue, (int, float)) and not isinstance(
            XValue, bool
        ), f"{Label} coordinate must be numeric"
        assert isinstance(YValue, (int, float)) and not isinstance(
            YValue, bool
        ), f"{Label} coordinate must be numeric"
        Directions.append((float(XValue), float(YValue)))
    return tuple(Directions)


# inherited direction markers permit only their documented optional boolean state
def InheritedDirections(Value: object, Label: str) -> tuple[bool | None, ...]:
    Directions: list[bool | None] = []
    for Entry in ArrayValue(Value, Label):
        assert Entry is None or isinstance(
            Entry, bool
        ), f"{Label} entries must be booleans or null"
        Directions.append(Entry)
    return tuple(Directions)


# stream inventory records need paired string fields for container comparisons
def ContainerStreams(Value: object, Label: str) -> tuple[ContainerStream, ...]:
    return tuple(
        ContainerStream(
            file=StringValue(FieldValue(ObjectValue(Entry, Label), "file"), "file"),
            name=StringValue(FieldValue(ObjectValue(Entry, Label), "name"), "name"),
        )
        for Entry in ArrayValue(Value, Label)
    )


# metadata decoding validates every documented field before tests inspect relations
def LoadDonorMetadata(TargetPath: FilePath) -> DonorMetadata:
    assert TargetPath.is_file(), f"missing donor fixture metadata {TargetPath}"
    Payload: object = JsonLib.loads(TargetPath.read_text(encoding="utf-8"))
    RecordInfo = ObjectValue(Payload, str(TargetPath))
    return DonorMetadata(
        arc_counts=IntegerValues(FieldValue(RecordInfo, "arc_counts"), "arc_counts"),
        axis_directions=AxisDirections(
            FieldValue(RecordInfo, "axis_directions"), "axis_directions"
        ),
        container_streams=ContainerStreams(
            FieldValue(RecordInfo, "container_streams"), "container_streams"
        ),
        depth_present=BooleanValues(
            FieldValue(RecordInfo, "depth_present"), "depth_present"
        ),
        donor_id=StringValue(FieldValue(RecordInfo, "donor_id"), "donor_id"),
        feature_ids=IntegerValues(FieldValue(RecordInfo, "feature_ids"), "feature_ids"),
        feature_names=StringValues(
            FieldValue(RecordInfo, "feature_names"), "feature_names"
        ),
        features=FeatureValues(FieldValue(RecordInfo, "features"), "features"),
        inherited_directions=InheritedDirections(
            FieldValue(RecordInfo, "inherited_directions"), "inherited_directions"
        ),
        measured=BooleanValue(FieldValue(RecordInfo, "measured"), "measured"),
        mo_version=IntegerValue(FieldValue(RecordInfo, "mo_version"), "mo_version"),
        point_counts=IntegerValues(
            FieldValue(RecordInfo, "point_counts"), "point_counts"
        ),
        sketch_ids=IntegerValues(FieldValue(RecordInfo, "sketch_ids"), "sketch_ids"),
        sketch_names=StringValues(
            FieldValue(RecordInfo, "sketch_names"), "sketch_names"
        ),
        spare_equations=StringValues(
            FieldValue(RecordInfo, "spare_equations"), "spare_equations"
        ),
        spare_plane_frames=IntegerValues(
            FieldValue(RecordInfo, "spare_plane_frames"), "spare_plane_frames"
        ),
        spare_plane_ids=IntegerValues(
            FieldValue(RecordInfo, "spare_plane_ids"), "spare_plane_ids"
        ),
        spare_plane_names=StringValues(
            FieldValue(RecordInfo, "spare_plane_names"), "spare_plane_names"
        ),
        stream_bytes=IntegerValue(
            FieldValue(RecordInfo, "stream_bytes"), "stream_bytes"
        ),
        swept_arc_counts=IntegerValues(
            FieldValue(RecordInfo, "swept_arc_counts"), "swept_arc_counts"
        ),
    )
