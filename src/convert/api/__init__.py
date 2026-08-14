# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath
import re as Regex
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange import CadDocument, PayloadRole
from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import (
    IsDeviceName,
    KSourceType as Source,
    KTargetType as Destination,
)
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry import AdapterRegistry
from convert.api.ApiAvailable import ListAdapters
from convert.api.ApiBrep import ExtractBrep
from convert.api.ApiContext import KAdapterRegistry, KConvertEngine
from convert.api.ApiConvert import ConvertFile
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from convert.api.Compatibility.AvailableCall import MakeAvailable
from convert.api.Compatibility.BrepCall import MakeBrepCall
from convert.api.Compatibility.ConvertCall import MakeConvertCall
from convert.api.Compatibility.OpenCall import MakeOpenCall
from convert.api.Compatibility.RegistryCall import MakeRegCall
from convert.api.Compatibility.WriteCall import MakeWriteCall
from convert.engine import ConversionEngine, ConversionResult

globals().update(
    {
        "_build_registry": MakeRegCall(),
        "available_adapters": MakeAvailable(),
        "convert": MakeConvertCall(),
        "extract_brep": MakeBrepCall(),
        "open_document": MakeOpenCall(),
        "write_document": MakeWriteCall(),
    }
)

globals().update(
    {
        "_engine": KConvertEngine,
        "registry": globals()["_build_registry"](),
    }
)

globals().update(
    {
        "Any": AnyValue,
        "Mapping": TypeMap,
        "Path": FilePath,
        "PayloadRole": PayloadRole,
        "frozen_mapping": FreezeMapping,
        "is_windows_device_name": IsDeviceName,
        "re": Regex,
    }
)
