from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

SWDOC_PART = 1
SWDOC_ASSEMBLY = 2
SWOPEN_SILENT = 1
SWSAVE_SILENT = 1

FILE_LOAD_ERRORS = {
    1: "generic-error",
    2: "file-not-found",
    4: "id-mismatch",
    8: "read-only",
    16: "shared-file-violation",
    32: "future-version",
    64: "liveparts-unsupported",
    128: "invalid-file-type-or-corrupt",
    256: "viewonly-not-supported",
    512: "critical-data-repair",
    1024: "drawing-of-future-version",
    2048: "lower-revision",
    4096: "add-in-interrupt",
    8192: "application-busy",
}

FILE_LOAD_WARNINGS = {
    1: "already-open",
    2: "read-only",
    4: "shared-file-violation",
    8: "viewonly-restrictions",
    16: "missing-external-references",
    32: "drawing-sheet-in-viewonly",
    64: "model-out-of-date",
    128: "view-missing-reference",
    256: "revision-table-gap",
    512: "read-only-lock-fail",
    1024: "component-missing-reference",
    2048: "needs-regen",
    4096: "base-part-not-loaded",
    8192: "invisible-components",
    16384: "dimensions-referenced-incorrectly",
}


class SolidWorksUnavailable(RuntimeError):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class FeatureRecord:
    name: str
    type_name: str
    suppressed: bool
    dimensions: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class SolidPropertyRecord:
    volume_mm3: float
    surface_area_mm2: float
    center_of_mass_mm: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class PartInspection:
    path: Path
    opened: bool
    load_errors: tuple[str, ...]
    load_warnings: tuple[str, ...]
    rebuilt: bool
    features: tuple[FeatureRecord, ...]
    body_count: int
    solid: SolidPropertyRecord | None
    parameters: tuple[tuple[str, float], ...] = field(default=())

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.features)

    @property
    def feature_type_names(self) -> tuple[str, ...]:
        return tuple(item.type_name for item in self.features)


def _decode_flags(value: int, table: dict[int, str]) -> tuple[str, ...]:
    if value <= 0:
        return ()
    return tuple(
        label for bit, label in sorted(table.items()) if value & bit
    ) or (f"unknown-{value}",)


def _is_dispatch(value: object) -> bool:
    try:
        from win32com.client.dynamic import CDispatch
    except ImportError:
        return False
    return isinstance(value, CDispatch)


def _com_value(owner: object, name: str) -> object:
    attribute = getattr(owner, name)
    if _is_dispatch(attribute) or not callable(attribute):
        return attribute
    return attribute()


def solidworks_available() -> bool:
    try:
        import winreg
    except ImportError:
        return False
    try:
        import win32com.client
    except ImportError:
        return False
    del win32com
    for root in (winreg.HKEY_CLASSES_ROOT,):
        try:
            with winreg.OpenKey(root, r"SldWorks.Application\CLSID") as key:
                value = winreg.QueryValueEx(key, "")[0]
        except OSError:
            continue
        if isinstance(value, str) and value.startswith("{"):
            return True
    return False


class SolidWorksSession:
    __slots__ = ("_app", "_pythoncom", "_variant", "_initialized")

    def __init__(self) -> None:
        try:
            import pythoncom
            from win32com.client import VARIANT, Dispatch
        except ImportError as exc:
            raise SolidWorksUnavailable(
                "pywin32 is required for the SOLIDWORKS oracle"
            ) from exc
        pythoncom.CoInitialize()
        self._initialized = True
        self._pythoncom = pythoncom
        self._variant = VARIANT
        try:
            self._app = Dispatch("SldWorks.Application")
        except Exception as exc:
            pythoncom.CoUninitialize()
            self._initialized = False
            raise SolidWorksUnavailable(
                f"cannot start SOLIDWORKS via COM: {exc}"
            ) from exc
        self._app.Visible = False
        self._app.UserControl = False
        self._app.FrameState = 1

    @property
    def revision(self) -> str:
        return str(_com_value(self._app, "RevisionNumber"))

    def close(self) -> None:
        if not self._initialized:
            return
        try:
            self._app.CloseAllDocuments(True)
        except Exception:
            pass
        try:
            self._app.ExitApp()
        except Exception:
            pass
        self._app = None
        try:
            self._pythoncom.CoUninitialize()
        finally:
            self._initialized = False

    def __enter__(self) -> SolidWorksSession:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _byref_long(self) -> object:
        return self._variant(
            self._pythoncom.VT_BYREF | self._pythoncom.VT_I4, 0
        )

    @contextmanager
    def _document(self, path: Path, doc_type: int) -> Iterator[tuple[object, tuple[str, ...], tuple[str, ...]]]:
        errors = self._byref_long()
        warnings = self._byref_long()
        model = self._app.OpenDoc6(
            str(path),
            doc_type,
            SWOPEN_SILENT,
            "",
            errors,
            warnings,
        )
        error_flags = _decode_flags(int(errors.value or 0), FILE_LOAD_ERRORS)
        warning_flags = _decode_flags(int(warnings.value or 0), FILE_LOAD_WARNINGS)
        try:
            yield model, error_flags, warning_flags
        finally:
            if model is not None:
                try:
                    self._app.CloseDoc(str(_com_value(model, "GetTitle")))
                except Exception:
                    pass

    def inspect_part(
        self,
        path: Path,
        *,
        rebuild: bool = True,
        parameter_names: tuple[str, ...] = (),
    ) -> PartInspection:
        with self._document(path, SWDOC_PART) as (model, errors, warnings):
            if model is None:
                return PartInspection(
                    path=path,
                    opened=False,
                    load_errors=errors or ("open-returned-null",),
                    load_warnings=warnings,
                    rebuilt=False,
                    features=(),
                    body_count=0,
                    solid=None,
                )
            rebuilt = bool(model.ForceRebuild3(False)) if rebuild else False
            features = _read_features(model)
            bodies = _read_body_count(model)
            solid = _read_solid_properties(model)
            parameters = _read_parameters(model, parameter_names)
            return PartInspection(
                path=path,
                opened=True,
                load_errors=errors,
                load_warnings=warnings,
                rebuilt=rebuilt,
                features=features,
                body_count=bodies,
                solid=solid,
                parameters=parameters,
            )

    def drive_parameter(
        self,
        path: Path,
        parameter: str,
        value_mm: float,
    ) -> PartInspection:
        with self._document(path, SWDOC_PART) as (model, errors, warnings):
            if model is None:
                return PartInspection(
                    path=path,
                    opened=False,
                    load_errors=errors or ("open-returned-null",),
                    load_warnings=warnings,
                    rebuilt=False,
                    features=(),
                    body_count=0,
                    solid=None,
                )
            handle = model.Parameter(parameter)
            if handle is None:
                return PartInspection(
                    path=path,
                    opened=True,
                    load_errors=(*errors, f"parameter-missing:{parameter}"),
                    load_warnings=warnings,
                    rebuilt=False,
                    features=_read_features(model),
                    body_count=_read_body_count(model),
                    solid=_read_solid_properties(model),
                )
            handle.SystemValue = value_mm / 1000.0
            rebuilt = bool(model.ForceRebuild3(False))
            return PartInspection(
                path=path,
                opened=True,
                load_errors=errors,
                load_warnings=warnings,
                rebuilt=rebuilt,
                features=_read_features(model),
                body_count=_read_body_count(model),
                solid=_read_solid_properties(model),
                parameters=_read_parameters(model, (parameter,)),
            )

    def resave_part(self, source: Path, target: Path) -> str:
        with self._document(source, SWDOC_PART) as (model, errors, _warnings):
            if model is None:
                return f"open-failed:{errors}"
            save_errors = self._byref_long()
            save_warnings = self._byref_long()
            model.Extension.SaveAs2(
                str(target),
                0,
                SWSAVE_SILENT,
                None,
                "",
                False,
                save_errors,
                save_warnings,
            )
            return (
                f"errors={_decode_flags(int(save_errors.value or 0), FILE_LOAD_ERRORS)} "
                f"exists={target.is_file()}"
            )

    def author_part(self, script: object, path: Path) -> PartInspection:
        model = self._app.NewDocument(_part_template(self._app), 0, 0.0, 0.0)
        if model is None:
            raise SolidWorksUnavailable("cannot create a new SOLIDWORKS part")
        try:
            script(self._app, model)
            errors = self._byref_long()
            warnings = self._byref_long()
            model.Extension.SaveAs2(
                str(path),
                0,
                SWSAVE_SILENT,
                None,
                "",
                False,
                errors,
                warnings,
            )
            saved_errors = _decode_flags(int(errors.value or 0), FILE_LOAD_ERRORS)
            return PartInspection(
                path=path,
                opened=True,
                load_errors=saved_errors,
                load_warnings=_decode_flags(
                    int(warnings.value or 0), FILE_LOAD_WARNINGS
                ),
                rebuilt=bool(model.ForceRebuild3(False)),
                features=_read_features(model),
                body_count=_read_body_count(model),
                solid=_read_solid_properties(model),
            )
        finally:
            try:
                self._app.CloseDoc(str(_com_value(model, "GetTitle")))
            except Exception:
                pass


def _part_template(app: object) -> str:
    template = app.GetUserPreferenceStringValue(8)
    if isinstance(template, str) and template:
        return template
    raise SolidWorksUnavailable("no default SOLIDWORKS part template is configured")


def _read_features(model: object) -> tuple[FeatureRecord, ...]:
    records: list[FeatureRecord] = []
    try:
        feature = _com_value(model, "FirstFeature")
    except Exception:
        return ()
    seen = 0
    while feature is not None and seen < 4096:
        seen += 1
        try:
            name = str(_com_value(feature, "Name"))
            type_name = str(_com_value(feature, "GetTypeName2"))
            suppressed = bool(_com_value(feature, "IsSuppressed"))
        except Exception:
            break
        records.append(
            FeatureRecord(
                name=name,
                type_name=type_name,
                suppressed=suppressed,
                dimensions=_read_feature_dimensions(feature),
            )
        )
        try:
            feature = _com_value(feature, "GetNextFeature")
        except Exception:
            break
    return tuple(records)


def _read_feature_dimensions(feature: object) -> tuple[tuple[str, float], ...]:
    values: list[tuple[str, float]] = []
    try:
        display = _com_value(feature, "GetFirstDisplayDimension")
    except Exception:
        return ()
    guard = 0
    while display is not None and guard < 256:
        guard += 1
        try:
            dimension = _com_value(display, "GetDimension")
            values.append(
                (
                    str(_com_value(dimension, "FullName")),
                    float(_com_value(dimension, "SystemValue")) * 1000.0,
                )
            )
        except Exception:
            break
        try:
            display = feature.GetNextDisplayDimension(display)
        except Exception:
            break
    return tuple(values)


def _read_body_count(model: object) -> int:
    try:
        part = model
        bodies = part.GetBodies2(0, True)
    except Exception:
        return 0
    if bodies is None:
        return 0
    try:
        return len(bodies)
    except TypeError:
        return 0


def _read_solid_properties(model: object) -> SolidPropertyRecord | None:
    import pythoncom
    from win32com.client import VARIANT

    status = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    try:
        values = model.Extension.GetMassProperties(1, status)
    except Exception:
        return None
    if values is None:
        return None
    try:
        numbers = tuple(float(value) for value in values)
    except TypeError:
        return None
    if len(numbers) < 6:
        return None
    return SolidPropertyRecord(
        volume_mm3=numbers[3] * 1.0e9,
        surface_area_mm2=numbers[4] * 1.0e6,
        center_of_mass_mm=(
            numbers[0] * 1000.0,
            numbers[1] * 1000.0,
            numbers[2] * 1000.0,
        ),
    )


def _read_parameters(
    model: object, names: tuple[str, ...]
) -> tuple[tuple[str, float], ...]:
    values: list[tuple[str, float]] = []
    for name in names:
        try:
            handle = model.Parameter(name)
        except Exception:
            continue
        if handle is None:
            continue
        try:
            values.append((name, float(_com_value(handle, "SystemValue")) * 1000.0))
        except Exception:
            continue
    return tuple(values)
