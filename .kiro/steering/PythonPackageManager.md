---
inclusion: always
---

# Python Package Manager

Use uv for Python dependency management everywhere except `Parashell/` and `modules/`.

- Replace pip commands with the equivalent uv command whenever they appear in scope.
- Use `pyproject.toml` and `uv.lock` for application and service dependencies.
- Use `uv add` and `uv remove` to change dependencies.
- Use `uv sync --frozen` in CI and `uv sync --frozen --no-dev --no-install-project` in runtime container builds.
- Use `uv run` for commands that need project dependencies.
- Use `astral-sh/setup-uv` in GitHub Actions and the official uv container image when Docker needs the uv binary.
- Do not introduce `requirements.txt`, `python -m pip`, `python3 -m pip`, or bare `pip` commands in scope.
- Do not modify `Parashell/` or `modules/` as part of pip-to-uv enforcement.
