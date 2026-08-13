# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .base import AdapterInfo
from .base import CarrierReason
from .base import CadAdapter
from .base import CadReaderAdapter
from .base import CadWriterAdapter
from .base import CapabilityTransfer
from .base import Destination
from .base import ProbeResult
from .base import ReadOptions
from .base import Source
from .base import TransferMode
from .base import WriteOptions
from .base import WriteResult
from .base import is_windows_device_name as IsDeviceName
from .registry import AdapterBinding
from .registry import AdapterDiscoveryError
from .registry import AdapterNotFoundError
from .registry import AdapterRegistry
from .registry import AdapterRegistryError
from .registry import AmbiguousAdapterError
from .registry import ApplicationUsabilityError
from .registry import CapabilityLossError

# legacy helper spelling remains available because payload validation imports this public name
globals()["is_windows_device_name"] = IsDeviceName

# package exports stay explicit so split implementation modules never leak into wildcard imports
__all__ = (
    "AdapterBinding",
    "AdapterDiscoveryError",
    "AdapterInfo",
    "AdapterNotFoundError",
    "AdapterRegistry",
    "AdapterRegistryError",
    "AmbiguousAdapterError",
    "ApplicationUsabilityError",
    "CadAdapter",
    "CadReaderAdapter",
    "CadWriterAdapter",
    "CapabilityLossError",
    "CapabilityTransfer",
    "CarrierReason",
    "Destination",
    "ProbeResult",
    "ReadOptions",
    "Source",
    "TransferMode",
    "WriteOptions",
    "WriteResult",
    "is_windows_device_name",
)

del IsDeviceName

for ModuleName in tuple(globals()):
    if ModuleName not in __all__ and ModuleName not in {
        "__builtins__",
        "__all__",
        "__cached__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__path__",
        "__spec__",
        "base",
        "catia",
        "freecad",
        "json",
        "registry",
    }:
        globals().pop(ModuleName, None)

del ModuleName
