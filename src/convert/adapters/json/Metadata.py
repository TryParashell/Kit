# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from convert.adapters.base import AdapterInfo
from convert.adapters.base import Destination
from convert.adapters.base import ProbeResult
from convert.adapters.base import Source
from convert.adapters.json.StreamIo import ReadPrefixMut
from interchange import CadDocument
from interchange import Capability


# this suffix is shared by probing registry metadata and path support checks
KSuffix = ".json"

# this immutable record keeps registry behavior identical across instances
KInfoValue = AdapterInfo(
    format_id="interchange.json",
    name="Kit interchange JSON",
    version="1.0",
    extensions=(KSuffix,),
    capabilities=frozenset(Capability),
    native_capabilities=frozenset(Capability),
    media_types=("application/vnd.parashell.kit+json",),
    part_extensions=(KSuffix,),
    assembly_extensions=(KSuffix,),
)


# this mixin keeps metadata checks independent of json serialization behavior
class JsonMetadata:

    # this property gives the registry stable adapter metadata
    @property
    def InfoAction(Instance) -> AdapterInfo:
        return KInfoValue

    # this probe reads only enough data to identify an interchange document
    def Probe(Instance, SourceValue: Source) -> ProbeResult:
        Suffix = ""
        if isinstance(SourceValue, (str, FilePath)):
            Suffix = FilePath(SourceValue).suffix.lower()
        try:
            Prefix = ReadPrefixMut(SourceValue, 4096)
        except OSError as ErrorInfo:
            return ProbeResult(KInfoValue.format_id, 0.0, str(ErrorInfo))
        if b'"$type"' in Prefix and b'"CadDocument"' in Prefix:
            return ProbeResult(KInfoValue.format_id, 1.0, "CadDocument type marker")
        Confidence = 0.5 if Suffix in KInfoValue.extensions else 0.0
        Reason = "JSON extension" if Confidence else "no interchange document marker"
        return ProbeResult(KInfoValue.format_id, Confidence, Reason)

    # this check accepts matching paths and writable stream objects
    def CanSupport(Instance, DocValue: CadDocument, Target: Destination) -> bool:
        if isinstance(Target, (str, FilePath)):
            return FilePath(Target).suffix.lower() in KInfoValue.extensions
        return callable(getattr(Target, "write", None))

    locals()["info"] = InfoAction
    locals()["probe"] = Probe
    locals()["supports"] = CanSupport
