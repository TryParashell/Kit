# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramComposer import BuildProgram
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Archive.SuCArchive.ReadClass import (
    KMethodProgram as KMethodA,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Archive.SuCArchive.WriteString import (
    KMethodProgram as KMethodB,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldarchiveu.Functions.MoGetModelnameFromPath import (
    KMethodProgram as KMethodC,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldarchiveu.MoSharedFileDefC.Serialize import (
    KMethodProgram as KMethodD,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmfcu.MoLineVizC.Serialize import (
    KMethodProgram as KMethodE,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmfcu.SuObArray.SerializePtr import (
    KMethodProgram as KMethodF,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmfcu.UtLineWidthC.Serialize import (
    KMethodProgram as KMethodG,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmgu.Functions.ReadOperator import (
    KMethodProgram as KMethodH,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmgu.MgMatrixC.Restore import (
    KMethodProgram as KMethodI,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmgu.MgPointC.Restore import (
    KMethodProgram as KMethodJ,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmgu.MgPointC.RestoreTwoD import (
    KMethodProgram as KMethodK,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmgu.MgVectorC.Restore import (
    KMethodProgram as KMethodL,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmgu.MgXformC.LinearComponent import (
    KMethodProgram as KMethodM,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmgu.MgXformC.Restore import (
    KMethodProgram as KMethodN,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.BentRefArr.Serialize import (
    KMethodProgram as KMethodO,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.DimensionC.Serialize import (
    KMethodProgram as KMethodP,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.Functions.MoLoadBodyFromArchive import (
    KMethodProgram as KMethodQ,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoAPatternC.GetThisClass import (
    KMethodProgram as KMethodR,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoArrowSizeC.Serialize import (
    KMethodProgram as KMethodS,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoBodyFeatureC.Serialize import (
    KMethodProgram as KMethodT,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoCSysRefPlnDataC.Serialize import (
    KMethodProgram as KMethodU,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoCompBEntRefC.Serialize import (
    KMethodProgram as KMethodV,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoCompBucketDataC.Serialize import (
    KMethodProgram as KMethodW,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoCompLoopC.Serialize import (
    KMethodProgram as KMethodX,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoCompRefC.Serialize import (
    KMethodProgram as KMethodY,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoConceptC.SerializeLWData import (
    KMethodProgram as KMethodZ,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoDimPatternRegenStatusC.Serialize import (
    KMethodProgram as KMethodAA,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoDimTextC.GetRuntimeClass import (
    KMethodProgram as KMethodAB,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KMethodProgram as KMethodAC,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoDisplayItemC.Serialize import (
    KMethodProgram as KMethodAD,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoDynSurfIdArr.Serialize import (
    KMethodProgram as KMethodAE,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoEdgeSurfIdKeeperC.Serialize import (
    KMethodProgram as KMethodAF,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoEntVisPropC.Serialize import (
    KMethodProgram as KMethodAG,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KMethodProgram as KMethodAH,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoFeatureC.Serialize import (
    KMethodProgram as KMethodAI,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoFolderC.Serialize import (
    KMethodProgram as KMethodAJ,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoFtrFolderC.Serialize import (
    KMethodProgram as KMethodAK,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoMateBeltDimC.GetThisClass import (
    KMethodProgram as KMethodAL,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoModelFeatureC.Serialize import (
    KMethodProgram as KMethodAM,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoNodeC.SerializeLWData import (
    KMethodProgram as KMethodAN,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoOrigDimDataC.Serialize import (
    KMethodProgram as KMethodAO,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoPSMeshToleranceHandlerC.Serialize import (
    KMethodProgram as KMethodAP,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KMethodProgram as KMethodAQ,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoRefPlnDataC.SerializePlaneData import (
    KMethodProgram as KMethodAR,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoRefSurfaceC.Serialize import (
    KMethodProgram as KMethodAS,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoReferenceCurveC.Serialize import (
    KMethodProgram as KMethodAT,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoSMAndFPFeatIdPair.Serialize import (
    KMethodProgram as KMethodAU,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoSelectionSetNodeC.GetThisClass import (
    KMethodProgram as KMethodAV,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoSubFavoriteFolderC.GetRuntimeClass import (
    KMethodProgram as KMethodAW,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoSwiftFRC.GetThisClass import (
    KMethodProgram as KMethodAX,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoThreedViewC.Serialize import (
    KMethodProgram as KMethodAY,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoVectorParameterC.GetThisClass import (
    KMethodProgram as KMethodAZ,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoVisPropC.Serialize import (
    KMethodProgram as KMethodBA,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoVisualOverlayObjectC.GetThisClass import (
    KMethodProgram as KMethodBB,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoWeldFavoriteC.GetRuntimeClass import (
    KMethodProgram as KMethodBC,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.MoXformStockC.GetThisClass import (
    KMethodProgram as KMethodBD,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgDim.Serialize import (
    KMethodProgram as KMethodBE,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgEntHandle.Serialize import (
    KMethodProgram as KMethodBF,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgLogDim.Serialize import (
    KMethodProgram as KMethodBG,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgLogGOneDim.Serialize import (
    KMethodProgram as KMethodBH,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgLogGThreeDim.Serialize import (
    KMethodProgram as KMethodBI,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgSketch.IPostLoad import (
    KMethodProgram as KMethodBJ,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgSketch.LoadSketchInPlace import (
    KMethodProgram as KMethodBK,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KMethodProgram as KMethodBL,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgSketch.Serialize import (
    KMethodProgram as KMethodBM,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KMethodProgram as KMethodBN,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Sldmodu.StructConnectionCutSurfIdRepC.GetThisClass import (
    KMethodProgram as KMethodBO,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Swccu.Functions.ReadOperator import (
    KMethodProgram as KMethodBP,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Swccu.SuCArchive.ReadCount import (
    KMethodProgram as KMethodBQ,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Swccu.SuCArchive.ReadObject import (
    KMethodProgram as KMethodBR,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Synthetic.ArchiveContinuationBase import (
    KMethodProgram as KMethodBS,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Synthetic.BodyChooserBoundingBoxes import (
    KMethodProgram as KMethodBT,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Synthetic.DisplayDimensionDerivedScalars import (
    KMethodProgram as KMethodBU,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Synthetic.DisplayDimensionDirectSlots import (
    KMethodProgram as KMethodBV,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Synthetic.DisplayDimensionIndices import (
    KMethodProgram as KMethodBW,
)
from convert.adapters.solidworks.programs.resolved.boss.pattern.linear.Methods.Synthetic.SketchChainEntityIndices import (
    KMethodProgram as KMethodBX,
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
)


# composed tables stay immutable because generated registries expose stable format facts
KFieldOwners, KResolvedOps = BuildProgram(
    KMethodPrograms,
    "ResolvedFeatures",
)

# generated registry exports remain explicit for facade composition and extension imports
__all__ = ["KFieldOwners", "KResolvedOps", "KMethodPrograms"]

# compatibility binding preserves its established public import after decomposition
globals()["FieldOwners"] = KFieldOwners

# compatibility binding preserves its established public import after decomposition
globals()["ResolvedOps"] = KResolvedOps
