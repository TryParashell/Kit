# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
import sys as SystemLib


# repository resolution stays shared so every runtime policy checks the same source tree
KRootPath = FilePath(__file__).parents[3]

# runtime inspection stays constrained to production packages rather than test infrastructure
KSourcePath = KRootPath / "src"

# controlled adapter discovery owns the only permitted dynamic production import
KDynamicImportPath = (
    KSourcePath
    / "convert"
    / "adapters"
    / "registry"
    / "AdapterDiscovery.py"
)

# cad modules stay forbidden because production runtime must remain application independent
KCadRoots = {
    "FreeCADGui",
    "FreeCAD",
    "NXOpen",
    "OCC",
    "Part",
    "Sketcher",
    "OCP",
    "adsk",
    "cadquery",
    "pycatia",
}

# network modules stay forbidden because conversion must remain deterministic and offline
KNetworkRoots = {
    "aiohttp",
    "ftplib",
    "httpx",
    "requests",
    "socket",
    "ssl",
    "urllib",
    "urllib3",
    "websockets",
}

# native bridges stay forbidden because the wheel must remain portable pure python
KNativeRoots = {
    "cffi",
    "clr",
    "comtypes",
    "ctypes",
    "lxml",
    "numpy",
    "pythoncom",
    "scipy",
    "win32com",
}

# process modules stay forbidden because runtime conversion cannot execute external software
KProcessRoots = {"multiprocessing", "runpy", "subprocess"}

# one combined set gives syntax checks a stable forbidden import contract
KForbiddenRoots = KCadRoots | KNetworkRoots | KNativeRoots | KProcessRoots

# dynamic code primitives stay forbidden because source execution must remain auditable
KForbiddenNames = {"__import__", "compile", "eval", "exec"}

# process and native calls stay forbidden even when their modules enter indirectly
KForbiddenAttrs = {
    "CDLL",
    "OleDLL",
    "PyDLL",
    "WinDLL",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "execv",
    "execve",
    "execvp",
    "execvpe",
    "import_module",
    "popen",
    "spawnl",
    "spawnle",
    "spawnlp",
    "spawnlpe",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
    "system",
}

# environment mutation stays forbidden because output cannot depend on host secrets or state
KEnvAttrs = {"environ", "getenv", "putenv", "unsetenv"}

# native library suffixes identify wheel payloads that would break runtime portability
KNativeSuffixes = (".dll", ".dylib", ".pyd", ".so")

# standard library and project packages form the complete allowed runtime import boundary
KAllowedRoots = frozenset(SystemLib.stdlib_module_names) | {"convert", "interchange"}
