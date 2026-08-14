# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramComposer import BuildStreams
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Archive.SuCArchive.ReadClass import (
    KMethodProgram as KMethodA,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Archive.SuCArchive.WriteString import (
    KMethodProgram as KMethodB,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldappu.UiBaseDocC.Serialize import (
    KMethodProgram as KMethodC,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldarchiveu.Functions.MoGetModelnameFromPath import (
    KMethodProgram as KMethodD,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldarchiveu.MoSharedFileDefC.Serialize import (
    KMethodProgram as KMethodE,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldarchiveu.MoStampC.GetRuntimeClass import (
    KMethodProgram as KMethodF,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldasmu.UiAssemblyDocC.Serialize import (
    KMethodProgram as KMethodG,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldasmu.UiSaveAssemblyAsPartSettingsC.Serialize import (
    KMethodProgram as KMethodH,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.ApLineStyleMgrC.Load import (
    KMethodProgram as KMethodI,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoAngOrdinateDimDefC.Serialize import (
    KMethodProgram as KMethodJ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoAngleDimDefC.Serialize import (
    KMethodProgram as KMethodK,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoAnnotationDataHelperC.Serialize import (
    KMethodProgram as KMethodL,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoAnnotationDefsC.Serialize import (
    KMethodProgram as KMethodM,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoAuxLabelDataC.Serialize import (
    KMethodProgram as KMethodN,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoBOMTableDefsC.Serialize import (
    KMethodProgram as KMethodO,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoBalloonDefsC.Serialize import (
    KMethodProgram as KMethodP,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoBaseAnnotationDefsC.Serialize import (
    KMethodProgram as KMethodQ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoBaseDimDefC.Serialize import (
    KMethodProgram as KMethodR,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoBendNoteDefsC.Serialize import (
    KMethodProgram as KMethodS,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoBendTableDefsC.Serialize import (
    KMethodProgram as KMethodT,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoCenterMarkSymDataHelperC.Serialize import (
    KMethodProgram as KMethodU,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoChamferDimDefC.Serialize import (
    KMethodProgram as KMethodV,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoConfigC.Serialize import (
    KMethodProgram as KMethodW,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDatumDefsC.Serialize import (
    KMethodProgram as KMethodX,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDatumFeatureDataHelperC.Serialize import (
    KMethodProgram as KMethodY,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDatumTargetDataHelperC.Serialize import (
    KMethodProgram as KMethodZ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDensityUnitsC.Serialize import (
    KMethodProgram as KMethodAA,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDetailDefsC.Serialize import (
    KMethodProgram as KMethodAB,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDetailLabelDataC.Serialize import (
    KMethodProgram as KMethodAC,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDiameterDimDefC.Serialize import (
    KMethodProgram as KMethodAD,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDimDefsC.Serialize import (
    KMethodProgram as KMethodAE,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoDrViewLabelDataC.Serialize import (
    KMethodProgram as KMethodAF,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoEnergyUnitsC.Serialize import (
    KMethodProgram as KMethodAG,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoFamilyTableDefsC.Serialize import (
    KMethodProgram as KMethodAH,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoForceUnitsC.Serialize import (
    KMethodProgram as KMethodAI,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoGTolDataHelperC.Serialize import (
    KMethodProgram as KMethodAJ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoGTolDlgDataFrameC.Serialize import (
    KMethodProgram as KMethodAK,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoGeneralTableDefsC.Serialize import (
    KMethodProgram as KMethodAL,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoGtolDefsC.Serialize import (
    KMethodProgram as KMethodAM,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoHoleCalloutDimDefC.Serialize import (
    KMethodProgram as KMethodAN,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoHoleTableDefsC.Serialize import (
    KMethodProgram as KMethodAO,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoLabelDefsC.Serialize import (
    KMethodProgram as KMethodAP,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoLengthUserUnitsC.Serialize import (
    KMethodProgram as KMethodAQ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoLineStyleC.Serialize import (
    KMethodProgram as KMethodAR,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoLineVizC.Serialize import (
    KMethodProgram as KMethodAS,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoLinearDimDefC.Serialize import (
    KMethodProgram as KMethodAT,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoMiscLabelDataC.Serialize import (
    KMethodProgram as KMethodAU,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoNoteDataHelperC.Serialize import (
    KMethodProgram as KMethodAV,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoNoteDefsC.Serialize import (
    KMethodProgram as KMethodAW,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoOrdinateDimDefC.Serialize import (
    KMethodProgram as KMethodAX,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoPunchTableDefsC.Serialize import (
    KMethodProgram as KMethodAY,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoRadialDimDefC.Serialize import (
    KMethodProgram as KMethodAZ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoRevisionTableDefsC.Serialize import (
    KMethodProgram as KMethodBA,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoSFDataHelperC.Serialize import (
    KMethodProgram as KMethodBB,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoSFDefsC.Serialize import (
    KMethodProgram as KMethodBC,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoSectionLabelDataC.Serialize import (
    KMethodProgram as KMethodBD,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoSwiftGtsOptionsC.Serialize import (
    KMethodProgram as KMethodBE,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoTableDefsC.Serialize import (
    KMethodProgram as KMethodBF,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoUserPropertyC.Restore import (
    KMethodProgram as KMethodBG,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoUserUnitsC.Serialize import (
    KMethodProgram as KMethodBH,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoViewLocationLabelDefsC.Serialize import (
    KMethodProgram as KMethodBI,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoVisualPropertiesC.Serialize import (
    KMethodProgram as KMethodBJ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoWeldDataHelperC.Serialize import (
    KMethodProgram as KMethodBK,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoWeldDefsC.Serialize import (
    KMethodProgram as KMethodBL,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.MoWeldTableDefsC.Serialize import (
    KMethodProgram as KMethodBM,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.SuObArray.SerializePtr import (
    KMethodProgram as KMethodBN,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.UiLFConfigC.Serialize import (
    KMethodProgram as KMethodBO,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.UoMaterialProperties.Restore import (
    KMethodProgram as KMethodBP,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.UtCharFormatC.Serialize import (
    KMethodProgram as KMethodBQ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.UtLineWidthC.Serialize import (
    KMethodProgram as KMethodBR,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmfcu.UtLineWidthPrintDataC.Serialize import (
    KMethodProgram as KMethodBS,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmgu.Functions.ReadOperator import (
    KMethodProgram as KMethodBT,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmgu.MgBBoxC.Restore import (
    KMethodProgram as KMethodBU,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmgu.MgMatrixC.Restore import (
    KMethodProgram as KMethodBV,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmgu.MgPointC.Restore import (
    KMethodProgram as KMethodBW,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmgu.MgPointC.RestoreTwoD import (
    KMethodProgram as KMethodBX,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmgu.MgVectorC.Restore import (
    KMethodProgram as KMethodBY,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmgu.MgXformC.Restore import (
    KMethodProgram as KMethodBZ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.BentRefArr.Serialize import (
    KMethodProgram as KMethodCA,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.DimensionC.Serialize import (
    KMethodProgram as KMethodCB,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.Functions.MoLoadBodyFromArchive import (
    KMethodProgram as KMethodCC,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoArrowSizeC.Serialize import (
    KMethodProgram as KMethodCD,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoAssemblyC.LoadSmartReplacementData import (
    KMethodProgram as KMethodCE,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoAssemblyC.SerializeLWData import (
    KMethodProgram as KMethodCF,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoAssemblyC.SerializeResolvedData import (
    KMethodProgram as KMethodCG,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoAtomC.GetRuntimeClass import (
    KMethodProgram as KMethodCH,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoBaseSwiftFGeomRefC.Serialize import (
    KMethodProgram as KMethodCI,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoCompLoopC.Serialize import (
    KMethodProgram as KMethodCJ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoCompRefC.Serialize import (
    KMethodProgram as KMethodCK,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoComponentC.Serialize import (
    KMethodProgram as KMethodCL,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoConceptC.SerializeLWData import (
    KMethodProgram as KMethodCM,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoConfigObjectWeldmemberFeatDataC.UpdateParentConfigObject import (
    KMethodProgram as KMethodCN,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoCustomPropertyList.GetThisClass import (
    KMethodProgram as KMethodCO,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoCustomPropsInfoC.GetRuntimeClass import (
    KMethodProgram as KMethodCP,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoDecalManagerDSC.ReorderDecals import (
    KMethodProgram as KMethodCQ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KMethodProgram as KMethodCR,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoEntVisPropC.Serialize import (
    KMethodProgram as KMethodCS,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoFaceVizPropsC.Restore import (
    KMethodProgram as KMethodCT,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoFeatureC.Serialize import (
    KMethodProgram as KMethodCU,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoFolderC.Serialize import (
    KMethodProgram as KMethodCV,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoFtrFolderC.Serialize import (
    KMethodProgram as KMethodCW,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoGhostPolylineDataC.GetThisClass import (
    KMethodProgram as KMethodCX,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoIgnorableCompareObj.Serialize import (
    KMethodProgram as KMethodCY,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoLightFeatureC.IsUniqueIdName import (
    KMethodProgram as KMethodCZ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoMassPropC.Serialize import (
    KMethodProgram as KMethodDA,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoModelFeatureC.Serialize import (
    KMethodProgram as KMethodDB,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoNodeC.SerializeLWData import (
    KMethodProgram as KMethodDC,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoPSMeshToleranceHandlerC.Serialize import (
    KMethodProgram as KMethodDD,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KMethodProgram as KMethodDE,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoPartConfigurationC.SerializeMBSMDataObjects import (
    KMethodProgram as KMethodDF,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoRefPlnDataC.SerializePlaneData import (
    KMethodProgram as KMethodDG,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoRelationC.GetRuntimeClass import (
    KMethodProgram as KMethodDH,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoSMAndFPFeatIdPair.Serialize import (
    KMethodProgram as KMethodDI,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoSectionPartC.IMoveLogsToHeaderOfDrawing import (
    KMethodProgram as KMethodDJ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoSelectionSetNodeC.GetThisClass import (
    KMethodProgram as KMethodDK,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoSubFavoriteFolderC.GetRuntimeClass import (
    KMethodProgram as KMethodDL,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoSwiftFRC.GetThisClass import (
    KMethodProgram as KMethodDM,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoThreedViewC.Serialize import (
    KMethodProgram as KMethodDN,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoToolboxPartSpecArrayC.SetDialogSettings import (
    KMethodProgram as KMethodDO,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoVectorParameterC.GetThisClass import (
    KMethodProgram as KMethodDP,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoViewC.Serialize import (
    KMethodProgram as KMethodDQ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoVisPropC.Serialize import (
    KMethodProgram as KMethodDR,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoVisualOverlayObjectC.GetThisClass import (
    KMethodProgram as KMethodDS,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.MoXformStockC.GetThisClass import (
    KMethodProgram as KMethodDT,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.PWMaterialManagerC.Restore import (
    KMethodProgram as KMethodDU,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgDim.Serialize import (
    KMethodProgram as KMethodDV,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgEntHandle.Serialize import (
    KMethodProgram as KMethodDW,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgLogDim.Serialize import (
    KMethodProgram as KMethodDX,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgLogGThreeDim.Serialize import (
    KMethodProgram as KMethodDY,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgSketch.IPostLoad import (
    KMethodProgram as KMethodDZ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgSketch.LoadSketchInPlace import (
    KMethodProgram as KMethodEA,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KMethodProgram as KMethodEB,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgSketch.Serialize import (
    KMethodProgram as KMethodEC,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KMethodProgram as KMethodED,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.SwSceneC.RemoveFloorCustomVizProps import (
    KMethodProgram as KMethodEE,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Sldmodu.UoModelDataC.Restore import (
    KMethodProgram as KMethodEF,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Slduiu.PVDocSpecificOptionsDataC.Serialize import (
    KMethodProgram as KMethodEG,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Slduiu.UiLineFontMgrC.GetThisClass import (
    KMethodProgram as KMethodEH,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Slduiu.UiModelDocC.ReplaceCompIdInDisplayDataMap import (
    KMethodProgram as KMethodEI,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Slduiu.UiModelDocC.Serialize import (
    KMethodProgram as KMethodEJ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Slduiu.UiModelDocC.SerializeSWItemsOfOLEObjects import (
    KMethodProgram as KMethodEK,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Slduiu.UiModelMapC.OnViewAllComments import (
    KMethodProgram as KMethodEL,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Slduiu.UiUserModelEnvC.GetRuntimeClass import (
    KMethodProgram as KMethodEM,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Swccu.Functions.ReadOperator import (
    KMethodProgram as KMethodEN,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Swccu.SuCArchive.GetObjectSchema import (
    KMethodProgram as KMethodEO,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Swccu.SuCArchive.ReadCount import (
    KMethodProgram as KMethodEP,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.AssemblyConfigurationArchivePrefix import (
    KMethodProgram as KMethodEQ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.AssemblyConfigurationVersionPreamble import (
    KMethodProgram as KMethodER,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.ConfigurationManagerArchivePrefix import (
    KMethodProgram as KMethodES,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.ConfigurationManagerInlineObjectTag import (
    KMethodProgram as KMethodET,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.ConfigurationManagerVersionPreamble import (
    KMethodProgram as KMethodEU,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.DefinitionDocumentClassIdentifierTail import (
    KMethodProgram as KMethodEV,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.DefinitionDocumentFlags import (
    KMethodProgram as KMethodEW,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.DefinitionJournalInlineState import (
    KMethodProgram as KMethodEX,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.MoLengthUserUnitsCDetailScalarTriplet import (
    KMethodProgram as KMethodEY,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.MoRelMgrCDetailScalarTriplet import (
    KMethodProgram as KMethodEZ,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.MoRelMgrCStatusNameTable import (
    KMethodProgram as KMethodFA,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.MoSketchBlockMgrCPersistentIdentifier import (
    KMethodProgram as KMethodFB,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.MoTransRefPlaneDataCFirstInlineTransformRow import (
    KMethodProgram as KMethodFC,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.MoTransRefPlaneDataCInlineFlag import (
    KMethodProgram as KMethodFD,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.MoTransRefPlaneDataCSecondInlineTransformRow import (
    KMethodProgram as KMethodFE,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.ModelHeaderArchivePrefix import (
    KMethodProgram as KMethodFF,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.ModelHeaderLogListPreamble import (
    KMethodProgram as KMethodFG,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.ModelHeaderStringArrayPreamble import (
    KMethodProgram as KMethodFH,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.ModelHeaderUserAndLogPreamble import (
    KMethodProgram as KMethodFI,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Methods.Synthetic.ResolvedFeatureContinuationBase import (
    KMethodProgram as KMethodFJ,
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
    KMethodDB,
    KMethodDC,
    KMethodDD,
    KMethodDE,
    KMethodDF,
    KMethodDG,
    KMethodDH,
    KMethodDI,
    KMethodDJ,
    KMethodDK,
    KMethodDL,
    KMethodDM,
    KMethodDN,
    KMethodDO,
    KMethodDP,
    KMethodDQ,
    KMethodDR,
    KMethodDS,
    KMethodDT,
    KMethodDU,
    KMethodDV,
    KMethodDW,
    KMethodDX,
    KMethodDY,
    KMethodDZ,
    KMethodEA,
    KMethodEB,
    KMethodEC,
    KMethodED,
    KMethodEE,
    KMethodEF,
    KMethodEG,
    KMethodEH,
    KMethodEI,
    KMethodEJ,
    KMethodEK,
    KMethodEL,
    KMethodEM,
    KMethodEN,
    KMethodEO,
    KMethodEP,
    KMethodEQ,
    KMethodER,
    KMethodES,
    KMethodET,
    KMethodEU,
    KMethodEV,
    KMethodEW,
    KMethodEX,
    KMethodEY,
    KMethodEZ,
    KMethodFA,
    KMethodFB,
    KMethodFC,
    KMethodFD,
    KMethodFE,
    KMethodFF,
    KMethodFG,
    KMethodFH,
    KMethodFI,
    KMethodFJ,
)


# composed tables stay immutable because generated registries expose stable format facts
KFieldOwners, KStreamPrograms = BuildStreams(
    KMethodPrograms,
    (
        "Contents/CMgr",
        "Contents/Config-0",
        "Contents/Config-0-ResolvedFeatures",
        "Contents/Definition",
        "Contents/Config-0-ModelHeader",
    ),
)

# generated registry exports remain explicit for facade composition and extension imports
__all__ = ["KFieldOwners", "KStreamPrograms", "KMethodPrograms"]

# compatibility binding preserves its established public import after decomposition
globals()["FieldOwners"] = KFieldOwners

# compatibility binding preserves its established public import after decomposition
globals()["StreamPrograms"] = KStreamPrograms
