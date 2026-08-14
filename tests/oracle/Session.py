# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from contextlib import contextmanager as Contextmanager
from dataclasses import dataclass as DataClass, field as MakeField
from pathlib import Path as FilePath
from typing import Iterator

# centralizes shared evidence so every related assertion uses one value
KPartInfo = 1

# centralizes shared evidence so every related assertion uses one value
KAssembly = 2

# centralizes shared evidence so every related assertion uses one value
KSilent = 1

# centralizes shared evidence so every related assertion uses one value
KSilentA = 1

# centralizes shared evidence so every related assertion uses one value
KErrors = {1: 'generic-error', 2: 'file-not-found', 4: 'id-mismatch', 8: 'read-only', 16: 'shared-file-violation', 32: 'future-version', 64: 'liveparts-unsupported', 128: 'invalid-file-type-or-corrupt', 256: 'viewonly-not-supported', 512: 'critical-data-repair', 1024: 'drawing-of-future-version', 2048: 'lower-revision', 4096: 'add-in-interrupt', 8192: 'application-busy'}

# centralizes shared evidence so every related assertion uses one value
KWarnings = {1: 'already-open', 2: 'read-only', 4: 'shared-file-violation', 8: 'viewonly-restrictions', 16: 'missing-external-references', 32: 'drawing-sheet-in-viewonly', 64: 'model-out-of-date', 128: 'view-missing-reference', 256: 'revision-table-gap', 512: 'read-only-lock-fail', 1024: 'component-missing-reference', 2048: 'needs-regen', 4096: 'base-part-not-loaded', 8192: 'invisible-components', 16384: 'dimensions-referenced-incorrectly'}

# keeps this focused behavior isolated so regressions remain immediately visible
class OracleMissing(RuntimeError):
    __slots__ = ()

# keeps this focused behavior isolated so regressions remain immediately visible
@DataClass(frozen=True, slots=True)
class FeatureRecord:
    NameText: str
    TypeName: str
    Suppressed: bool
    Dimensions: tuple[tuple[str, float], ...]

    # keeps this focused behavior isolated so regressions remain immediately visible
    def __getattr__(SelfRef, NameText: str):
        AliasName = KFeatureAliases.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return object.__getattribute__(SelfRef, AliasName)

# keeps this focused behavior isolated so regressions remain immediately visible
@DataClass(frozen=True, slots=True)
class SolidProps:
    VolumeMmThree: float
    SurfaceAreaMmTwo: float
    CenterOfMassMm: tuple[float, float, float]

    # keeps this focused behavior isolated so regressions remain immediately visible
    def __getattr__(SelfRef, NameText: str):
        AliasName = KSolidAliases.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return object.__getattribute__(SelfRef, AliasName)

# keeps this focused behavior isolated so regressions remain immediately visible
@DataClass(frozen=True, slots=True)
class PartInspection:
    TargetPath: FilePath
    Opened: bool
    LoadErrors: tuple[str, ...]
    LoadWarnings: tuple[str, ...]
    Rebuilt: bool
    Features: tuple[FeatureRecord, ...]
    BodyCount: int
    Solid: SolidProps | None
    Parameters: tuple[tuple[str, float], ...] = MakeField(default=())

    # keeps this focused behavior isolated so regressions remain immediately visible
    @property
    def FeatureNames(SelfRef) -> tuple[str, ...]:
        return tuple((ItemValue.name for ItemValue in SelfRef.features))

    # keeps this focused behavior isolated so regressions remain immediately visible
    @property
    def FeatureTN(SelfRef) -> tuple[str, ...]:
        return tuple((ItemValue.type_name for ItemValue in SelfRef.features))

    # keeps this focused behavior isolated so regressions remain immediately visible
    def __getattr__(SelfRef, NameText: str):
        AliasName = KPartAliases.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return object.__getattribute__(SelfRef, AliasName)

# keeps this focused behavior isolated so regressions remain immediately visible
def DecodeFlags(ItemValueA: int, LookupTable: dict[int, str]) -> tuple[str, ...]:
    if ItemValueA <= 0:
        return ()
    return tuple((Label for FlagBit, Label in sorted(LookupTable.items()) if ItemValueA & FlagBit)) or (f'unknown-{ItemValueA}',)

# keeps this focused behavior isolated so regressions remain immediately visible
def IsDispatch(ItemValueA: object) -> bool:
    try:
        from win32com.client.dynamic import CDispatch
    except ImportError:
        return False
    return isinstance(ItemValueA, CDispatch)

# keeps this focused behavior isolated so regressions remain immediately visible
def ComValue(Owner: object, NameText: str) -> object:
    Attribute = getattr(Owner, NameText)
    if IsDispatch(Attribute) or not callable(Attribute):
        return Attribute
    return Attribute()

# keeps this focused behavior isolated so regressions remain immediately visible
def IsOracleReady() -> bool:
    try:
        import winreg as Winreg
    except ImportError:
        return False
    try:
        import win32com.client as WinThreeTwocom
    except ImportError:
        return False
    del WinThreeTwocom
    for RootValue in (Winreg.HKEY_CLASSES_ROOT,):
        try:
            with Winreg.OpenKey(RootValue, 'SldWorks.Application\\CLSID') as LookupKey:
                ItemValueA = Winreg.QueryValueEx(LookupKey, '')[0]
        except OSError:
            continue
        if isinstance(ItemValueA, str) and ItemValueA.startswith('{'):
            return True
    return False

# keeps this focused behavior isolated so regressions remain immediately visible
def InitSessionMut(SelfRef) -> None:
    try:
        import pythoncom as PythoncomA
        from win32com.client import VARIANT, Dispatch
    except ImportError as ErrorInfo:
        raise OracleMissing('pywin32 is required for the SOLIDWORKS oracle') from ErrorInfo
    PythoncomA.CoInitialize()
    SelfRef.Initialized = True
    SelfRef.Pythoncom = PythoncomA
    SelfRef.Variant = VARIANT
    try:
        SelfRef.AppInfo = Dispatch('SldWorks.Application')
    except Exception as ErrorInfo:
        PythoncomA.CoUninitialize()
        SelfRef.Initialized = False
        raise OracleMissing(f'cannot start SOLIDWORKS via COM: {ErrorInfo}') from ErrorInfo
    SelfRef.AppInfo.Visible = False
    SelfRef.AppInfo.UserControl = False
    SelfRef.AppInfo.FrameState = 1

# keeps this focused behavior isolated so regressions remain immediately visible
class SessionLife:
    __slots__ = ()

    # keeps this focused behavior isolated so regressions remain immediately visible
    @property
    def Revision(SelfRef) -> str:
        return str(ComValue(SelfRef.AppInfo, 'RevisionNumber'))

    # keeps this focused behavior isolated so regressions remain immediately visible
    def Close(SelfRef) -> None:
        if not SelfRef.Initialized:
            return
        try:
            SelfRef.AppInfo.CloseAllDocuments(True)
        except Exception:
            pass
        try:
            SelfRef.AppInfo.ExitApp()
        except Exception:
            pass
        SelfRef.AppInfo = None
        try:
            SelfRef.Pythoncom.CoUninitialize()
        finally:
            SelfRef.Initialized = False

    # keeps this focused behavior isolated so regressions remain immediately visible
    def ByrefLong(SelfRef) -> object:
        return SelfRef.Variant(SelfRef.Pythoncom.VT_BYREF | SelfRef.Pythoncom.VT_I4, 0)

# keeps this focused behavior isolated so regressions remain immediately visible
class DocAccess:
    __slots__ = ()

    # keeps this focused behavior isolated so regressions remain immediately visible
    @Contextmanager
    def Document(SelfRef, TargetPath: FilePath, DocType: int) -> Iterator[tuple[object, tuple[str, ...], tuple[str, ...]]]:
        ErrorList = SelfRef.ByrefLong()
        WarningList = SelfRef.ByrefLong()
        ModelDoc = SelfRef.AppInfo.OpenDoc6(str(TargetPath), DocType, KSilent, '', ErrorList, WarningList)
        ErrorFlags = DecodeFlags(int(ErrorList.value or 0), KErrors)
        WarningFlags = DecodeFlags(int(WarningList.value or 0), KWarnings)
        try:
            yield (ModelDoc, ErrorFlags, WarningFlags)
        finally:
            if ModelDoc is not None:
                try:
                    SelfRef.AppInfo.CloseDoc(str(ComValue(ModelDoc, 'GetTitle')))
                except Exception:
                    pass

# keeps this focused behavior isolated so regressions remain immediately visible
class PartInspector:
    __slots__ = ()

    # keeps this focused behavior isolated so regressions remain immediately visible
    def InspectPart(SelfRef, TargetPath: FilePath, *, Rebuild: bool=True, ParameterNames: tuple[str, ...]=()) -> PartInspection:
        with SelfRef.Document(TargetPath, KPartInfo) as (ModelDoc, ErrorList, WarningList):
            if ModelDoc is None:
                return PartInspection(TargetPath=TargetPath, Opened=False, LoadErrors=ErrorList or ('open-returned-null',), LoadWarnings=WarningList, Rebuilt=False, Features=(), BodyCount=0, Solid=None)
            Rebuilt = bool(ModelDoc.ForceRebuild3(False)) if Rebuild else False
            Features = ReadFeatures(ModelDoc)
            Bodies = ReadBodyCount(ModelDoc)
            Solid = ReadSP(ModelDoc)
            Parameters = ReadParameters(ModelDoc, ParameterNames)
            return PartInspection(TargetPath=TargetPath, Opened=True, LoadErrors=ErrorList, LoadWarnings=WarningList, Rebuilt=Rebuilt, Features=Features, BodyCount=Bodies, Solid=Solid, Parameters=Parameters)

# keeps this focused behavior isolated so regressions remain immediately visible
class ParamDriver:
    __slots__ = ()

    # keeps this focused behavior isolated so regressions remain immediately visible
    def DriveParameter(SelfRef, TargetPath: FilePath, Parameter: str, ValueMm: float) -> PartInspection:
        with SelfRef.Document(TargetPath, KPartInfo) as (ModelDoc, ErrorList, WarningList):
            if ModelDoc is None:
                return PartInspection(TargetPath=TargetPath, Opened=False, LoadErrors=ErrorList or ('open-returned-null',), LoadWarnings=WarningList, Rebuilt=False, Features=(), BodyCount=0, Solid=None)
            Handle = ModelDoc.Parameter(Parameter)
            if Handle is None:
                return PartInspection(TargetPath=TargetPath, Opened=True, LoadErrors=(*ErrorList, f'parameter-missing:{Parameter}'), LoadWarnings=WarningList, Rebuilt=False, Features=ReadFeatures(ModelDoc), BodyCount=ReadBodyCount(ModelDoc), Solid=ReadSP(ModelDoc))
            Handle.SystemValue = ValueMm / 1000.0
            Rebuilt = bool(ModelDoc.ForceRebuild3(False))
            return PartInspection(TargetPath=TargetPath, Opened=True, LoadErrors=ErrorList, LoadWarnings=WarningList, Rebuilt=Rebuilt, Features=ReadFeatures(ModelDoc), BodyCount=ReadBodyCount(ModelDoc), Solid=ReadSP(ModelDoc), Parameters=ReadParameters(ModelDoc, (Parameter,)))

# keeps this focused behavior isolated so regressions remain immediately visible
class PartResaver:
    __slots__ = ()

    # keeps this focused behavior isolated so regressions remain immediately visible
    def ResavePart(SelfRef, SourceDoc: FilePath, TargetDoc: FilePath) -> str:
        with SelfRef.Document(SourceDoc, KPartInfo) as (ModelDoc, ErrorList, Warnings):
            if ModelDoc is None:
                return f'open-failed:{ErrorList}'
            SaveErrors = SelfRef.ByrefLong()
            SaveWarnings = SelfRef.ByrefLong()
            ModelDoc.Extension.SaveAs2(str(TargetDoc), 0, KSilentA, None, '', False, SaveErrors, SaveWarnings)
            return f'errors={DecodeFlags(int(SaveErrors.value or 0), KErrors)} exists={TargetDoc.is_file()}'

# keeps this focused behavior isolated so regressions remain immediately visible
class PartAuthor:
    __slots__ = ()

    # keeps this focused behavior isolated so regressions remain immediately visible
    def AuthorPart(SelfRef, Script: object, TargetPath: FilePath) -> PartInspection:
        ModelDoc = SelfRef.AppInfo.NewDocument(PartTemplate(SelfRef.AppInfo), 0, 0.0, 0.0)
        if ModelDoc is None:
            raise OracleMissing('cannot create a new SOLIDWORKS part')
        try:
            Script(SelfRef.AppInfo, ModelDoc)
            ErrorList = SelfRef.ByrefLong()
            WarningList = SelfRef.ByrefLong()
            ModelDoc.Extension.SaveAs2(str(TargetPath), 0, KSilentA, None, '', False, ErrorList, WarningList)
            SavedErrors = DecodeFlags(int(ErrorList.value or 0), KErrors)
            return PartInspection(TargetPath=TargetPath, Opened=True, LoadErrors=SavedErrors, LoadWarnings=DecodeFlags(int(WarningList.value or 0), KWarnings), Rebuilt=bool(ModelDoc.ForceRebuild3(False)), Features=ReadFeatures(ModelDoc), BodyCount=ReadBodyCount(ModelDoc), Solid=ReadSP(ModelDoc))
        finally:
            try:
                SelfRef.AppInfo.CloseDoc(str(ComValue(ModelDoc, 'GetTitle')))
            except Exception:
                pass

# keeps this focused behavior isolated so regressions remain immediately visible
class OracleSession(SessionLife, DocAccess, PartInspector, ParamDriver, PartResaver, PartAuthor):
    __slots__ = ('AppInfo', 'Pythoncom', 'Variant', 'Initialized')

    # keeps this focused behavior isolated so regressions remain immediately visible
    def __init__(SelfRef) -> None:
        InitSessionMut(SelfRef)

    # keeps this focused behavior isolated so regressions remain immediately visible
    def __enter__(SelfRef) -> OracleSession:
        return SelfRef

    # keeps this focused behavior isolated so regressions remain immediately visible
    def __exit__(SelfRef, *ExcInfo: object) -> None:
        SelfRef.Close()

    # keeps this focused behavior isolated so regressions remain immediately visible
    def __getattr__(SelfRef, NameText: str):
        AliasName = KSessionAliases.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return object.__getattribute__(SelfRef, AliasName)

# keeps this focused behavior isolated so regressions remain immediately visible
def PartTemplate(CadApp: object) -> str:
    Template = CadApp.GetUserPreferenceStringValue(8)
    if isinstance(Template, str) and Template:
        return Template
    raise OracleMissing('no default SOLIDWORKS part template is configured')

# keeps this focused behavior isolated so regressions remain immediately visible
def ReadFeatures(ModelDoc: object) -> tuple[FeatureRecord, ...]:
    RecordList: list[FeatureRecord] = []
    try:
        Feature = ComValue(ModelDoc, 'FirstFeature')
    except Exception:
        return ()
    SeenInfo = 0
    while Feature is not None and SeenInfo < 4096:
        SeenInfo += 1
        try:
            NameText = str(ComValue(Feature, 'Name'))
            TypeName = str(ComValue(Feature, 'GetTypeName2'))
            Suppressed = bool(ComValue(Feature, 'IsSuppressed'))
        except Exception:
            break
        RecordList.append(FeatureRecord(NameText=NameText, TypeName=TypeName, Suppressed=Suppressed, Dimensions=ReadFD(Feature)))
        try:
            Feature = ComValue(Feature, 'GetNextFeature')
        except Exception:
            break
    return tuple(RecordList)

# keeps this focused behavior isolated so regressions remain immediately visible
def ReadFD(Feature: object) -> tuple[tuple[str, float], ...]:
    ValueList: list[tuple[str, float]] = []
    try:
        Display = ComValue(Feature, 'GetFirstDisplayDimension')
    except Exception:
        return ()
    Guard = 0
    while Display is not None and Guard < 256:
        Guard += 1
        try:
            Dimension = ComValue(Display, 'GetDimension')
            ValueList.append((str(ComValue(Dimension, 'FullName')), float(ComValue(Dimension, 'SystemValue')) * 1000.0))
        except Exception:
            break
        try:
            Display = Feature.GetNextDisplayDimension(Display)
        except Exception:
            break
    return tuple(ValueList)

# keeps this focused behavior isolated so regressions remain immediately visible
def ReadBodyCount(ModelDoc: object) -> int:
    try:
        PartDoc = ModelDoc
        Bodies = PartDoc.GetBodies2(0, True)
    except Exception:
        return 0
    if Bodies is None:
        return 0
    try:
        return len(Bodies)
    except TypeError:
        return 0

# keeps this focused behavior isolated so regressions remain immediately visible
def ReadSP(ModelDoc: object) -> SolidProps | None:
    import pythoncom as PythoncomA
    from win32com.client import VARIANT
    Status = VARIANT(PythoncomA.VT_BYREF | PythoncomA.VT_I4, 0)
    try:
        ValueList = ModelDoc.Extension.GetMassProperties(1, Status)
    except Exception:
        return None
    if ValueList is None:
        return None
    try:
        Numbers = tuple((float(ItemValueA) for ItemValueA in ValueList))
    except TypeError:
        return None
    if len(Numbers) < 6:
        return None
    return SolidProps(VolumeMmThree=Numbers[3] * 1000000000.0, SurfaceAreaMmTwo=Numbers[4] * 1000000.0, CenterOfMassMm=(Numbers[0] * 1000.0, Numbers[1] * 1000.0, Numbers[2] * 1000.0))

# keeps this focused behavior isolated so regressions remain immediately visible
def ReadParameters(ModelDoc: object, NameList: tuple[str, ...]) -> tuple[tuple[str, float], ...]:
    ValueList: list[tuple[str, float]] = []
    for NameText in NameList:
        try:
            Handle = ModelDoc.Parameter(NameText)
        except Exception:
            continue
        if Handle is None:
            continue
        try:
            ValueList.append((NameText, float(ComValue(Handle, 'SystemValue')) * 1000.0))
        except Exception:
            continue
    return tuple(ValueList)

# centralizes shared evidence so every related assertion uses one value
KFeatureAliases = {'name': 'NameText', 'type_name': 'TypeName', 'suppressed': 'Suppressed', 'dimensions': 'Dimensions'}

# centralizes shared evidence so every related assertion uses one value
KSolidAliases = {'volume_mm3': 'VolumeMmThree', 'surface_area_mm2': 'SurfaceAreaMmTwo', 'center_of_mass_mm': 'CenterOfMassMm'}

# centralizes shared evidence so every related assertion uses one value
KPartAliases = {'path': 'TargetPath', 'opened': 'Opened', 'load_errors': 'LoadErrors', 'load_warnings': 'LoadWarnings', 'rebuilt': 'Rebuilt', 'features': 'Features', 'body_count': 'BodyCount', 'solid': 'Solid', 'parameters': 'Parameters', 'feature_names': 'FeatureNames', 'feature_type_names': 'FeatureTN'}

# centralizes shared evidence so every related assertion uses one value
KSessionAliases = {'revision': 'Revision', 'close': 'Close', 'inspect_part': 'InspectPart', 'drive_parameter': 'DriveParameter', 'resave_part': 'ResavePart', 'author_part': 'AuthorPart'}

# centralizes shared evidence so every related assertion uses one value
KModuleAliases = {'SolidWorksSession': OracleSession, 'SolidWorksUnavailable': OracleMissing, 'solidworks_available': IsOracleReady}

# keeps this focused behavior isolated so regressions remain immediately visible
def __getattr__(NameText: str):
    AliasValue = KModuleAliases.get(NameText)
    if AliasValue is None:
        raise AttributeError(NameText)
    return AliasValue
