# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream
from io import StringIO as TextStream

from interchange import CadDocument

from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.ContractTypes import IsBinaryTarget
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import RunCheckedMut
from convert.adapters.base.WriteResult import WriteResult


# stream writes stage payloads so policy failures never mutate caller owned destinations
def WriteStreamMut(
    DocumentData: CadDocument,
    AdapterData: CadWriterAdapter,
    TargetData: KTargetType,
    OptionsData: WriteOptions,
    AllowCarrier: bool,
    NeedSelfContained: bool,
) -> WriteResult:
    StagedStream = ByteStream() if IsBinaryTarget(TargetData) else TextStream()
    ResultData = RunCheckedMut(
        DocumentData,
        AdapterData,
        StagedStream,
        OptionsData,
        AllowCarrier,
        NeedSelfContained,
    )
    if ResultData.OutputPath is not None:
        raise RegistryError("stream writer returned a filesystem path")
    PayloadData = StagedStream.getvalue()
    WriterData = getattr(TargetData, "write", None)
    if not callable(WriterData):
        raise TypeError("destination must be a writable path or stream")
    WrittenCount = WriterData(PayloadData)
    if WrittenCount is not None and WrittenCount != len(PayloadData):
        raise OSError(
            f"short destination write: expected {len(PayloadData)}, wrote {WrittenCount}"
        )
    return ResultData
