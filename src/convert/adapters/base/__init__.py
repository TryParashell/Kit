# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.AdapterProtocols import CadAdapter
from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.ContractTypes import IsBinaryTarget
from convert.adapters.base.ContractTypes import IsDeviceName
from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.ProbeResult import ProbeResult
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.TransferContract import CarrierReason
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult

from interchange import Capability
from interchange import Diagnostic

# historical path annotations need resolution after records move behind this compatibility facade
globals()["Path"] = FilePath

# historical unconstrained annotations need resolution after records move behind this compatibility facade
globals()["Any"] = AnyValue

# historical mapping annotations need resolution after records move behind this compatibility facade
globals()["Mapping"] = TypeMap

# historical capability annotations need resolution after records move behind this compatibility facade
globals()["Capability"] = Capability

# historical diagnostic annotations need resolution after records move behind this compatibility facade
globals()["Diagnostic"] = Diagnostic

for PublicType in (
    AdapterInfo,
    ProbeResult,
    ReadOptions,
    WriteOptions,
    WriteResult,
    CapTransfer,
    CarrierReason,
    TransferMode,
):
    setattr(PublicType, "__module__", __name__)

setattr(CapTransfer, "__name__", "CapabilityTransfer")
setattr(CapTransfer, "__qualname__", "CapabilityTransfer")


# source annotation stays stable because every existing adapter imports this public contract
globals()["Source"] = KSourceType

# destination annotation stays stable because every existing writer imports this public contract
globals()["Destination"] = KTargetType

# transfer contract name stays stable because writer implementations construct it directly
globals()["CapabilityTransfer"] = CapTransfer

# windows helper name stays stable because payload validation imports the historical spelling
globals()["is_windows_device_name"] = IsDeviceName

# binary helper name stays stable because existing writers use the historical spelling
globals()["is_binary_destination"] = IsBinaryTarget
