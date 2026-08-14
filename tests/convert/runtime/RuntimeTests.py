# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import ast
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from tests.convert.runtime.IsolatedRuntime import KIsolatedRuntime

ROOT = Path(__file__).parents[3]
SOURCE = ROOT / "src"
DYNAMIC_IMPORT_PATH = SOURCE / "convert" / "adapters" / "AdapterDiscovery.py"
FORBIDDEN_ROOTS = {
    "FreeCADGui",
    "FreeCAD",
    "NXOpen",
    "OCC",
    "Part",
    "Sketcher",
    "OCP",
    "adsk",
    "aiohttp",
    "cadquery",
    "cffi",
    "clr",
    "comtypes",
    "ctypes",
    "ftplib",
    "httpx",
    "lxml",
    "multiprocessing",
    "numpy",
    "pycatia",
    "pythoncom",
    "requests",
    "runpy",
    "scipy",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
    "urllib3",
    "websockets",
    "win32com",
}
FORBIDDEN_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
}
FORBIDDEN_ATTRIBUTES = {
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
FORBIDDEN_ENVIRONMENT_ATTRIBUTES = {
    "environ",
    "getenv",
    "putenv",
    "unsetenv",
}
NATIVE_LIBRARY_SUFFIXES = (".dll", ".dylib", ".pyd", ".so")
ALLOWED_RUNTIME_ROOTS = frozenset(sys.stdlib_module_names) | {
    "convert",
    "interchange",
}


def test_runtime_has_no_cad_or_process_dependencies() -> None:
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text("utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                assert roots <= ALLOWED_RUNTIME_ROOTS, (
                    path,
                    roots - ALLOWED_RUNTIME_ROOTS,
                )
                assert not roots & FORBIDDEN_ROOTS, (path, roots & FORBIDDEN_ROOTS)
            if isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                if node.level == 0:
                    assert root in ALLOWED_RUNTIME_ROOTS, (path, root)
                assert root not in FORBIDDEN_ROOTS, (path, root)
                if node.module == "importlib":
                    for alias in node.names:
                        if alias.name == "import_module":
                            assert path == DYNAMIC_IMPORT_PATH, path
                            assert alias.asname == "ImportModule", path
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in FORBIDDEN_NAMES, (path, node.func.id)
                    if node.func.id == "import_module":
                        assert path == DYNAMIC_IMPORT_PATH, path
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in FORBIDDEN_ATTRIBUTES, (
                        path,
                        node.func.attr,
                    )
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "os":
                    assert node.attr not in FORBIDDEN_ENVIRONMENT_ATTRIBUTES, (
                        path,
                        node.attr,
                    )
            if isinstance(node, ast.ImportFrom) and node.module == "os":
                names = {alias.name for alias in node.names}
                assert not names & FORBIDDEN_ENVIRONMENT_ATTRIBUTES, (
                    path,
                    names & FORBIDDEN_ENVIRONMENT_ATTRIBUTES,
                )


# runtime source must contain no executable placeholder statements
def test_source_contains_no_stubs() -> None:
    for path in SOURCE.rglob("*.py"):
        source = path.read_bytes()
        tree = ast.parse(source, filename=str(path))
        assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree)), path


def test_every_source_file_opens_with_the_licence_header() -> None:
    expected = (
        "# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0",
        "# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin",
    )
    for path in SOURCE.rglob("*.py"):
        lines = path.read_text(encoding="utf-8").splitlines()
        assert tuple(lines[: len(expected)]) == expected, path


def test_source_layout_uses_only_interchange_and_convert() -> None:
    packages = {
        path.name
        for path in SOURCE.iterdir()
        if path.is_dir() and any(path.rglob("*.py"))
    }
    assert packages == {"convert", "interchange"}


def test_built_wheel_is_self_contained_and_runs_with_external_hooks_blocked(
    tmp_path: Path,
) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    wheel_directory = tmp_path / "wheel"
    completed = subprocess.run(
        (
            uv,
            "build",
            "--wheel",
            "--offline",
            "--no-progress",
            "--out-dir",
            str(wheel_directory),
        ),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = tuple(wheel_directory.glob("*.whl"))
    assert completed.returncode == 0
    assert len(wheels) == 1
    install_root = tmp_path / "site"
    with zipfile.ZipFile(wheels[0]) as archive:
        names = tuple(archive.namelist())
        assert not any(
            name.casefold().endswith(NATIVE_LIBRARY_SUFFIXES) for name in names
        )
        wheel_name = next(name for name in names if name.endswith("/WHEEL"))
        metadata_name = next(name for name in names if name.endswith("/METADATA"))
        entry_points_name = next(
            name for name in names if name.endswith("/entry_points.txt")
        )
        wheel_metadata = archive.read(wheel_name).decode("utf-8")
        assert "Root-Is-Purelib: true" in wheel_metadata
        assert "Tag: py3-none-any" in wheel_metadata
        metadata = BytesParser(policy=default).parsebytes(archive.read(metadata_name))
        requirements = tuple(metadata.get_all("Requires-Dist", ()))
        extras = tuple(metadata.get_all("Provides-Extra", ()))
        extra_markers = {
            marker
            for extra in extras
            for marker in (f"extra == '{extra}'", f'extra == "{extra}"')
        }
        assert all(
            any(marker in value.partition(";")[2] for marker in extra_markers)
            for value in requirements
        )
        assert archive.read(entry_points_name).decode("utf-8") == (
            "[kit]\nconvert = convert:convert\n"
        )
        archive.extractall(install_root)
    runtime_output = tmp_path / "runtime"
    runtime_output.mkdir()
    isolated = subprocess.run(
        (
            sys.executable,
            "-I",
            "-S",
            "-c",
            KIsolatedRuntime,
            str(install_root),
            str(ROOT),
            str(runtime_output),
        ),
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert isolated.returncode == 0, isolated.stderr
