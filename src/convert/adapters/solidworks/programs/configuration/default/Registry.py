# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramComposer import BuildProgram
from convert.adapters.solidworks.programs.configuration.default.Methods.Archive.SuCArchive.ReadClass import (
    KMethodProgram as KMethodA,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Archive.SuCArchive.WriteString import (
    KMethodProgram as KMethodB,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.GcCurvatureObjectC.Serialize import (
    KMethodProgram as KMethodC,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.GcXhatchC.Serialize import (
    KMethodProgram as KMethodD,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoAngOrdinateDimDefC.Serialize import (
    KMethodProgram as KMethodE,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoAngleDimDefC.Serialize import (
    KMethodProgram as KMethodF,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoAnnotationDataHelperC.Serialize import (
    KMethodProgram as KMethodG,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoAnnotationDefsC.Serialize import (
    KMethodProgram as KMethodH,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoAuxLabelDataC.Serialize import (
    KMethodProgram as KMethodI,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoBOMTableDefsC.Serialize import (
    KMethodProgram as KMethodJ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoBalloonDefsC.Serialize import (
    KMethodProgram as KMethodK,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoBaseAnnotationDefsC.Serialize import (
    KMethodProgram as KMethodL,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoBaseDimDefC.Serialize import (
    KMethodProgram as KMethodM,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoBendNoteDefsC.Serialize import (
    KMethodProgram as KMethodN,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoBendTableDefsC.Serialize import (
    KMethodProgram as KMethodO,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoCenterMarkSymDataHelperC.Serialize import (
    KMethodProgram as KMethodP,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoChamferDimDefC.Serialize import (
    KMethodProgram as KMethodQ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDatumDefsC.Serialize import (
    KMethodProgram as KMethodR,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDatumFeatureDataHelperC.Serialize import (
    KMethodProgram as KMethodS,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDatumTargetDataHelperC.Serialize import (
    KMethodProgram as KMethodT,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDensityUnitsC.Serialize import (
    KMethodProgram as KMethodU,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDetailDefsC.Serialize import (
    KMethodProgram as KMethodV,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDetailLabelDataC.Serialize import (
    KMethodProgram as KMethodW,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDiameterDimDefC.Serialize import (
    KMethodProgram as KMethodX,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDimDefsC.Serialize import (
    KMethodProgram as KMethodY,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoDrViewLabelDataC.Serialize import (
    KMethodProgram as KMethodZ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoEnergyUnitsC.Serialize import (
    KMethodProgram as KMethodAA,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoFamilyTableDefsC.Serialize import (
    KMethodProgram as KMethodAB,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoFeatColorTabC.Serialize import (
    KMethodProgram as KMethodAC,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoForceUnitsC.Serialize import (
    KMethodProgram as KMethodAD,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoGTolDataHelperC.Serialize import (
    KMethodProgram as KMethodAE,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoGTolDlgDataFrameC.Serialize import (
    KMethodProgram as KMethodAF,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoGeneralTableDefsC.Serialize import (
    KMethodProgram as KMethodAG,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoGtolDefsC.Serialize import (
    KMethodProgram as KMethodAH,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoHoleCalloutDimDefC.Serialize import (
    KMethodProgram as KMethodAI,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoHoleTableDefsC.Serialize import (
    KMethodProgram as KMethodAJ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoLabelDefsC.Serialize import (
    KMethodProgram as KMethodAK,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoLengthUserUnitsC.Serialize import (
    KMethodProgram as KMethodAL,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoLinearDimDefC.Serialize import (
    KMethodProgram as KMethodAM,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoMiscLabelDataC.Serialize import (
    KMethodProgram as KMethodAN,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoNoteDataHelperC.Serialize import (
    KMethodProgram as KMethodAO,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoNoteDefsC.Serialize import (
    KMethodProgram as KMethodAP,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoOrdinateDimDefC.Serialize import (
    KMethodProgram as KMethodAQ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoPunchTableDefsC.Serialize import (
    KMethodProgram as KMethodAR,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoRadialDimDefC.Serialize import (
    KMethodProgram as KMethodAS,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoRevisionTableDefsC.Serialize import (
    KMethodProgram as KMethodAT,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoSFDataHelperC.Serialize import (
    KMethodProgram as KMethodAU,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoSFDefsC.Serialize import (
    KMethodProgram as KMethodAV,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoSectionLabelDataC.Serialize import (
    KMethodProgram as KMethodAW,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoSwiftGtsOptionsC.Serialize import (
    KMethodProgram as KMethodAX,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoTableDefsC.Serialize import (
    KMethodProgram as KMethodAY,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoUserPropertyC.Restore import (
    KMethodProgram as KMethodAZ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoUserUnitsC.Serialize import (
    KMethodProgram as KMethodBA,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoViewLocationLabelDefsC.Serialize import (
    KMethodProgram as KMethodBB,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoVisualPropertiesC.Serialize import (
    KMethodProgram as KMethodBC,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoWeldDataHelperC.Serialize import (
    KMethodProgram as KMethodBD,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoWeldDefsC.Serialize import (
    KMethodProgram as KMethodBE,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.MoWeldTableDefsC.Serialize import (
    KMethodProgram as KMethodBF,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.UiLFConfigC.Serialize import (
    KMethodProgram as KMethodBG,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.UoMaterialProperties.Restore import (
    KMethodProgram as KMethodBH,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.UoRVAppearanceProperties.Restore import (
    KMethodProgram as KMethodBI,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.UtCharFormatC.Serialize import (
    KMethodProgram as KMethodBJ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.UtLineWidthC.Serialize import (
    KMethodProgram as KMethodBK,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmfcu.UtLineWidthPrintDataC.Serialize import (
    KMethodProgram as KMethodBL,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmgu.MgBBoxC.Restore import (
    KMethodProgram as KMethodBM,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmgu.MgMatrixC.Restore import (
    KMethodProgram as KMethodBN,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmgu.MgVectorC.Restore import (
    KMethodProgram as KMethodBO,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmgu.MgXformC.Restore import (
    KMethodProgram as KMethodBP,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoAtomC.GetRuntimeClass import (
    KMethodProgram as KMethodBQ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoCachedBoundingBoxMapC.Get import (
    KMethodProgram as KMethodBR,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoConceptC.SerializeLWData import (
    KMethodProgram as KMethodBS,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoDervPartCTRefEntHolderC.GetThisClass import (
    KMethodProgram as KMethodBT,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoEntVisPropC.Serialize import (
    KMethodProgram as KMethodBU,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoFaceVizPropsC.Restore import (
    KMethodProgram as KMethodBV,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoFeatureC.Serialize import (
    KMethodProgram as KMethodBW,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoFolderC.Serialize import (
    KMethodProgram as KMethodBX,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoGhostPolylineDataC.GetThisClass import (
    KMethodProgram as KMethodBY,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoIgnorableCompareObj.Serialize import (
    KMethodProgram as KMethodBZ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoLightFeatureC.IsUniqueIdName import (
    KMethodProgram as KMethodCA,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoMassPropC.Serialize import (
    KMethodProgram as KMethodCB,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoMassPropCacheC.GetRuntimeClass import (
    KMethodProgram as KMethodCC,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoModelFeatureC.Serialize import (
    KMethodProgram as KMethodCD,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoNodeC.SerializeLWData import (
    KMethodProgram as KMethodCE,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoPartC.LoadExternalGhostBodies import (
    KMethodProgram as KMethodCF,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoPartConfigurationC.SerializeMBSMDataObjects import (
    KMethodProgram as KMethodCG,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoRelationC.GetRuntimeClass import (
    KMethodProgram as KMethodCH,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoSMAndFPFeatIdPair.Serialize import (
    KMethodProgram as KMethodCI,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoThreedViewC.Serialize import (
    KMethodProgram as KMethodCJ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoToolboxPartSpecArrayC.SetDialogSettings import (
    KMethodProgram as KMethodCK,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoVectorParameterC.GetThisClass import (
    KMethodProgram as KMethodCL,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoViewC.Serialize import (
    KMethodProgram as KMethodCM,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoVisPropC.Serialize import (
    KMethodProgram as KMethodCN,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.MoVisualOverlayObjectC.GetThisClass import (
    KMethodProgram as KMethodCO,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KMethodProgram as KMethodCP,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldmodu.UoModelDataC.Restore import (
    KMethodProgram as KMethodCQ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Sldsmmu.MoMultiBodySheetmetalOrganizerC.ResetDataAncestorForSMFeat import (
    KMethodProgram as KMethodCR,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Swccu.Functions.ReadOperator import (
    KMethodProgram as KMethodCS,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Swccu.SuCArchive.ReadCount import (
    KMethodProgram as KMethodCT,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Swccu.SuCArchive.ReadObject import (
    KMethodProgram as KMethodCU,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Synthetic.MoLengthUserUnitsCDetailScalarTriplet import (
    KMethodProgram as KMethodCV,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Synthetic.MoRelMgrCDetailScalarTriplet import (
    KMethodProgram as KMethodCW,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Synthetic.MoRelMgrCStatusNameTable import (
    KMethodProgram as KMethodCX,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Synthetic.MoSketchBlockMgrCPersistentIdentifier import (
    KMethodProgram as KMethodCY,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Synthetic.MoTransRefPlaneDataCFirstInlineTransformRow import (
    KMethodProgram as KMethodCZ,
)
from convert.adapters.solidworks.programs.configuration.default.Methods.Synthetic.MoTransRefPlaneDataCSecondInlineTransformRow import (
    KMethodProgram as KMethodDA,
)


# explicit ordering keeps generated imports deterministic while offsets govern composition
KMethodPrograms = (
    KMethodA,
    KMethodB,
    KMethodC,
    KMethodD,
    KMethodE,
    KMethodF,
    KMethodG,
    KMethodH,
    KMethodI,
    KMethodJ,
    KMethodK,
    KMethodL,
    KMethodM,
    KMethodN,
    KMethodO,
    KMethodP,
    KMethodQ,
    KMethodR,
    KMethodS,
    KMethodT,
    KMethodU,
    KMethodV,
    KMethodW,
    KMethodX,
    KMethodY,
    KMethodZ,
    KMethodAA,
    KMethodAB,
    KMethodAC,
    KMethodAD,
    KMethodAE,
    KMethodAF,
    KMethodAG,
    KMethodAH,
    KMethodAI,
    KMethodAJ,
    KMethodAK,
    KMethodAL,
    KMethodAM,
    KMethodAN,
    KMethodAO,
    KMethodAP,
    KMethodAQ,
    KMethodAR,
    KMethodAS,
    KMethodAT,
    KMethodAU,
    KMethodAV,
    KMethodAW,
    KMethodAX,
    KMethodAY,
    KMethodAZ,
    KMethodBA,
    KMethodBB,
    KMethodBC,
    KMethodBD,
    KMethodBE,
    KMethodBF,
    KMethodBG,
    KMethodBH,
    KMethodBI,
    KMethodBJ,
    KMethodBK,
    KMethodBL,
    KMethodBM,
    KMethodBN,
    KMethodBO,
    KMethodBP,
    KMethodBQ,
    KMethodBR,
    KMethodBS,
    KMethodBT,
    KMethodBU,
    KMethodBV,
    KMethodBW,
    KMethodBX,
    KMethodBY,
    KMethodBZ,
    KMethodCA,
    KMethodCB,
    KMethodCC,
    KMethodCD,
    KMethodCE,
    KMethodCF,
    KMethodCG,
    KMethodCH,
    KMethodCI,
    KMethodCJ,
    KMethodCK,
    KMethodCL,
    KMethodCM,
    KMethodCN,
    KMethodCO,
    KMethodCP,
    KMethodCQ,
    KMethodCR,
    KMethodCS,
    KMethodCT,
    KMethodCU,
    KMethodCV,
    KMethodCW,
    KMethodCX,
    KMethodCY,
    KMethodCZ,
    KMethodDA,
)


# composed tables stay immutable because generated registries expose stable format facts
KFieldOwners, KConfigOps = BuildProgram(
    KMethodPrograms,
    "Configuration",
)

# compatibility binding preserves its established public import after decomposition
globals()["FieldOwners"] = KFieldOwners

# compatibility binding preserves its established public import after decomposition
globals()["ConfigOps"] = KConfigOps
