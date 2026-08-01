from __future__ import annotations

import ast
import io
from pathlib import Path
import tokenize


SOURCE = Path(__file__).parents[2] / "src"
FORBIDDEN_ROOTS = {
    "FreeCAD",
    "Part",
    "Sketcher",
    "OCP",
    "cadquery",
    "comtypes",
    "ctypes",
    "multiprocessing",
    "pythoncom",
    "runpy",
    "subprocess",
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


def test_runtime_has_no_cad_or_process_dependencies() -> None:
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text("utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                assert not roots & FORBIDDEN_ROOTS, (path, roots & FORBIDDEN_ROOTS)
            if isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                assert root not in FORBIDDEN_ROOTS, (path, root)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in FORBIDDEN_NAMES, (path, node.func.id)
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in FORBIDDEN_ATTRIBUTES, (
                        path,
                        node.func.attr,
                    )


def test_source_contains_no_code_comments_or_stubs() -> None:
    for path in SOURCE.rglob("*.py"):
        source = path.read_bytes()
        tokens = tokenize.tokenize(io.BytesIO(source).readline)
        assert all(token.type != tokenize.COMMENT for token in tokens), path
        tree = ast.parse(source, filename=str(path))
        assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree)), path


def test_source_layout_uses_only_interchange_and_convert() -> None:
    packages = {
        path.name
        for path in SOURCE.iterdir()
        if path.is_dir() and any(path.rglob("*.py"))
    }
    assert packages == {"convert", "interchange"}
