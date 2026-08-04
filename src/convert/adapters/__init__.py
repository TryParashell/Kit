# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .base import (
    AdapterInfo,
    CarrierReason,
    CadAdapter,
    CadReaderAdapter,
    CadWriterAdapter,
    CapabilityTransfer,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    TransferMode,
    WriteOptions,
    WriteResult,
    is_windows_device_name,
)
from .registry import (
    AdapterBinding,
    AdapterDiscoveryError,
    ApplicationUsabilityError,
    CapabilityLossError,
    AdapterNotFoundError,
    AdapterRegistry,
    AdapterRegistryError,
    AmbiguousAdapterError,
)

__all__ = [name for name in globals() if not name.startswith("_")]
