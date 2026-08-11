# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse
from collections.abc import Mapping
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any

# repository-relative imports keep the audit runnable without installing Kit
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from convert import write_document  # noqa: E402
from convert.adapters.freecad import read_freecad  # noqa: E402
from convert.adapters.solidworks import SldprtArchive  # noqa: E402
from convert.adapters.solidworks.native import HasVendorPartEncoding  # noqa: E402


# command-line parsing keeps recursive scope and failure policy explicit
def ParseArguments() -> argparse.Namespace:
    ParserData = argparse.ArgumentParser(
        description=(
            "Audit FCStd files through the CAD-free first-principles SOLIDWORKS "
            "writer. No CAD application or vendor automation is launched."
        )
    )
    ParserData.add_argument(
        "roots",
        nargs="*",
        type=Path,
        default=(REPOSITORY_ROOT,),
        help="file or directory roots to scan recursively",
    )
    ParserData.add_argument(
        "--json",
        action="store_true",
        help="emit the complete machine-readable audit instead of one row per file",
    )
    ParserData.add_argument(
        "--require-vendor-loadable",
        action="store_true",
        help="return a non-zero status unless every discovered FCStd is vendor-loadable",
    )
    ParserData.add_argument("--worker-source", type=Path, help=argparse.SUPPRESS)
    ParserData.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    ParserData.add_argument("--worker-index", type=int, help=argparse.SUPPRESS)
    return ParserData.parse_args()


# deterministic discovery prevents duplicate files when scan roots overlap
def DiscoverSources(RootPaths: tuple[Path, ...]) -> tuple[Path, ...]:
    SourcePaths: set[Path] = set()
    for RootPath in RootPaths:
        ResolvedPath = RootPath.expanduser().resolve()
        if ResolvedPath.is_file():
            if ResolvedPath.suffix.casefold() == ".fcstd":
                SourcePaths.add(ResolvedPath)
            continue
        if not ResolvedPath.is_dir():
            raise FileNotFoundError(f"audit root does not exist: {ResolvedPath}")
        SourcePaths.update(
            ItemPath.resolve()
            for ItemPath in ResolvedPath.rglob("*")
            if ItemPath.is_file() and ItemPath.suffix.casefold() == ".fcstd"
        )
    return tuple(sorted(SourcePaths, key=lambda ItemPath: str(ItemPath).casefold()))


# source feature types explain each writer verdict without relying on file names
def FeatureTypes(DocumentData: Any) -> tuple[str, ...]:
    TypeNames: set[str] = set()
    for FeatureData in DocumentData.feature_timeline:
        FreeCadData = FeatureData.attributes.get("freecad")
        TypeName = (
            FreeCadData.get("type_id", "") if isinstance(FreeCadData, Mapping) else ""
        )
        TypeNames.add(str(TypeName or FeatureData.kind))
    return tuple(sorted(TypeNames))


# one-file auditing exercises parse, first-principles write, and container readback
def AuditSource(
    SourcePath: Path,
    OutputRoot: Path,
    SourceIndex: int,
) -> dict[str, Any]:
    RelativePath = (
        str(SourcePath.relative_to(REPOSITORY_ROOT))
        if SourcePath.is_relative_to(REPOSITORY_ROOT)
        else str(SourcePath)
    )
    try:
        DocumentData = read_freecad(SourcePath)
        SourceFeatureTypes = FeatureTypes(DocumentData)
        if DocumentData.assembly is None and not HasVendorPartEncoding(DocumentData):
            return {
                "path": RelativePath,
                "kind": "part",
                "feature_types": SourceFeatureTypes,
                "application_usable": False,
                "vendor_loadable": False,
                "near_lossless": False,
                "native_capabilities": (),
                "requirements": ("no_typed_native_feature_program",),
                "bytes": 0,
                "streams": 0,
                "error": "",
            }
        TargetSuffix = ".SLDASM" if DocumentData.assembly is not None else ".SLDPRT"
        TargetPath = OutputRoot / f"audit-{SourceIndex:04d}{TargetSuffix}"
        ResultData = write_document(
            DocumentData,
            TargetPath,
            allow_carrier=True,
        )
        TargetData = TargetPath.read_bytes()
        ArchiveData = SldprtArchive.from_bytes(TargetData)
        NativeCapabilities = tuple(
            sorted(ItemData.value for ItemData in ResultData.native_capabilities)
        )
        return {
            "path": RelativePath,
            "kind": "assembly" if DocumentData.assembly is not None else "part",
            "feature_types": SourceFeatureTypes,
            "application_usable": ResultData.application_usable,
            "vendor_loadable": ResultData.vendor_loadable,
            "near_lossless": ResultData.near_lossless,
            "native_capabilities": NativeCapabilities,
            "requirements": ResultData.requirements,
            "bytes": len(TargetData),
            "streams": len(ArchiveData.streams),
            "error": "",
        }
    except Exception as ErrorData:
        return {
            "path": RelativePath,
            "kind": "unknown",
            "feature_types": (),
            "application_usable": False,
            "vendor_loadable": False,
            "near_lossless": False,
            "native_capabilities": (),
            "requirements": (),
            "bytes": 0,
            "streams": 0,
            "error": f"{type(ErrorData).__name__}: {ErrorData}",
        }


# process isolation lets the recursive audit survive malformed or memory intensive files
def AuditSourceIsolated(
    SourcePath: Path,
    OutputRoot: Path,
    SourceIndex: int,
) -> dict[str, Any]:
    try:
        ProcessData = subprocess.run(
            (
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker-source",
                str(SourcePath),
                "--worker-output",
                str(OutputRoot),
                "--worker-index",
                str(SourceIndex),
            ),
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired as ErrorData:
        RelativePath = (
            str(SourcePath.relative_to(REPOSITORY_ROOT))
            if SourcePath.is_relative_to(REPOSITORY_ROOT)
            else str(SourcePath)
        )
        return {
            "path": RelativePath,
            "kind": "unknown",
            "feature_types": (),
            "application_usable": False,
            "vendor_loadable": False,
            "near_lossless": False,
            "native_capabilities": (),
            "requirements": (),
            "bytes": 0,
            "streams": 0,
            "error": f"isolated worker timed out after {ErrorData.timeout} seconds",
        }
    OutputLines = tuple(
        LineData.strip()
        for LineData in ProcessData.stdout.splitlines()
        if LineData.strip()
    )
    if ProcessData.returncode == 0 and OutputLines:
        try:
            ResultData = json.loads(OutputLines[-1])
        except json.JSONDecodeError:
            ResultData = None
        if isinstance(ResultData, dict):
            return ResultData
    RelativePath = (
        str(SourcePath.relative_to(REPOSITORY_ROOT))
        if SourcePath.is_relative_to(REPOSITORY_ROOT)
        else str(SourcePath)
    )
    ErrorText = ProcessData.stderr.strip() or ProcessData.stdout.strip()
    if len(ErrorText) > 1000:
        ErrorText = ErrorText[-1000:]
    return {
        "path": RelativePath,
        "kind": "unknown",
        "feature_types": (),
        "application_usable": False,
        "vendor_loadable": False,
        "near_lossless": False,
        "native_capabilities": (),
        "requirements": (),
        "bytes": 0,
        "streams": 0,
        "error": (
            f"isolated worker exited {ProcessData.returncode}"
            + (f": {ErrorText}" if ErrorText else "")
        ),
    }


# the audit summary groups unsupported families while retaining every file verdict
def Main() -> int:
    ArgumentsData = ParseArguments()
    if ArgumentsData.worker_source is not None:
        if ArgumentsData.worker_output is None or ArgumentsData.worker_index is None:
            raise SystemExit("audit worker arguments are incomplete")
        print(
            json.dumps(
                AuditSource(
                    ArgumentsData.worker_source.resolve(),
                    ArgumentsData.worker_output.resolve(),
                    ArgumentsData.worker_index,
                ),
                separators=(",", ":"),
            )
        )
        return 0
    SourcePaths = DiscoverSources(tuple(ArgumentsData.roots))
    with TemporaryDirectory(prefix="kit-fcstd-audit-") as TemporaryPath:
        OutputRoot = Path(TemporaryPath)
        ResultsData = tuple(
            AuditSourceIsolated(SourcePath, OutputRoot, SourceIndex)
            for SourceIndex, SourcePath in enumerate(SourcePaths)
        )
    UnsupportedTypes = Counter(
        TypeName
        for ResultData in ResultsData
        if not ResultData["vendor_loadable"]
        for TypeName in ResultData["feature_types"]
    )
    VendorOnlyTypes = Counter(
        TypeName
        for ResultData in ResultsData
        if ResultData["vendor_loadable"] and not ResultData["application_usable"]
        for TypeName in ResultData["feature_types"]
    )
    SummaryData = {
        "files": len(ResultsData),
        "application_usable": sum(
            bool(ResultData["application_usable"]) for ResultData in ResultsData
        ),
        "vendor_loadable": sum(
            bool(ResultData["vendor_loadable"]) for ResultData in ResultsData
        ),
        "vendor_only": sum(
            bool(ResultData["vendor_loadable"])
            and not bool(ResultData["application_usable"])
            for ResultData in ResultsData
        ),
        "near_lossless": sum(
            bool(ResultData["near_lossless"]) for ResultData in ResultsData
        ),
        "errors": sum(bool(ResultData["error"]) for ResultData in ResultsData),
        "unsupported_feature_types": dict(sorted(UnsupportedTypes.items())),
        "vendor_only_feature_types": dict(sorted(VendorOnlyTypes.items())),
    }
    if ArgumentsData.json:
        print(json.dumps({"summary": SummaryData, "files": ResultsData}, indent=2))
    else:
        for ResultData in ResultsData:
            StateValue = (
                "usable"
                if ResultData["application_usable"]
                else (
                    "vendor-only"
                    if ResultData["vendor_loadable"]
                    else "error" if ResultData["error"] else "unsupported"
                )
            )
            DetailValue = (
                ResultData["error"]
                or ",".join(ResultData["feature_types"])
                or ",".join(ResultData["requirements"])
            )
            print(f"{StateValue:11} {ResultData['path']} {DetailValue}")
        print(json.dumps(SummaryData, sort_keys=True))
    HasFailures = any(not ResultData["vendor_loadable"] for ResultData in ResultsData)
    return int(ArgumentsData.require_vendor_loadable and HasFailures)


if __name__ == "__main__":
    raise SystemExit(Main())
