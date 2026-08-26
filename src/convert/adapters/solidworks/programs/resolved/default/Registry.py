# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramComposer import BuildProgram
from convert.adapters.solidworks.programs.resolved.default.Methods.Archive.SuCArchive.ReadClass import (
    KMethodProgram as KMethodA,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Archive.SuCArchive.WriteString import (
    KMethodProgram as KMethodB,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldarchiveu.Functions.MoGetModelnameFromPath import (
    KMethodProgram as KMethodC,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldarchiveu.MoSharedFileDefC.Serialize import (
    KMethodProgram as KMethodD,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmfcu.MoLineVizC.Serialize import (
    KMethodProgram as KMethodE,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmfcu.SuObArray.SerializePtr import (
    KMethodProgram as KMethodF,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmfcu.UtLineWidthC.Serialize import (
    KMethodProgram as KMethodG,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmgu.Functions.ReadOperator import (
    KMethodProgram as KMethodH,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmgu.MgMatrixC.Restore import (
    KMethodProgram as KMethodI,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmgu.MgPointC.Restore import (
    KMethodProgram as KMethodJ,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmgu.MgPointC.RestoreTwoD import (
    KMethodProgram as KMethodK,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmgu.MgVectorC.Restore import (
    KMethodProgram as KMethodL,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmgu.MgXformC.LinearComponent import (
    KMethodProgram as KMethodM,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmgu.MgXformC.Restore import (
    KMethodProgram as KMethodN,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.BentRefArr.Serialize import (
    KMethodProgram as KMethodO,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.DimensionC.Serialize import (
    KMethodProgram as KMethodP,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.Functions.MoLoadBodyFromArchive import (
    KMethodProgram as KMethodQ,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoArrowSizeC.Serialize import (
    KMethodProgram as KMethodR,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoBodyFeatureC.Serialize import (
    KMethodProgram as KMethodS,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoCompLoopC.Serialize import (
    KMethodProgram as KMethodT,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoCompRefC.Serialize import (
    KMethodProgram as KMethodU,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoConceptC.SerializeLWData import (
    KMethodProgram as KMethodV,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoDimPatternRegenStatusC.Serialize import (
    KMethodProgram as KMethodW,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoDimTextC.GetRuntimeClass import (
    KMethodProgram as KMethodX,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KMethodProgram as KMethodY,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoDisplayItemC.Serialize import (
    KMethodProgram as KMethodZ,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoDynSurfIdArr.Serialize import (
    KMethodProgram as KMethodAA,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoEdgeSurfIdKeeperC.Serialize import (
    KMethodProgram as KMethodAB,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoEntVisPropC.Serialize import (
    KMethodProgram as KMethodAC,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KMethodProgram as KMethodAD,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoFeatureC.Serialize import (
    KMethodProgram as KMethodAE,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoFolderC.Serialize import (
    KMethodProgram as KMethodAF,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoFtrFolderC.Serialize import (
    KMethodProgram as KMethodAG,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoMateBeltDimC.GetThisClass import (
    KMethodProgram as KMethodAH,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoModelFeatureC.Serialize import (
    KMethodProgram as KMethodAI,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoNodeC.SerializeLWData import (
    KMethodProgram as KMethodAJ,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoPSMeshToleranceHandlerC.Serialize import (
    KMethodProgram as KMethodAK,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KMethodProgram as KMethodAL,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoRefPlnDataC.SerializePlaneData import (
    KMethodProgram as KMethodAM,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoReferenceCurveC.Serialize import (
    KMethodProgram as KMethodAN,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoSMAndFPFeatIdPair.Serialize import (
    KMethodProgram as KMethodAO,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoSelectionSetNodeC.GetThisClass import (
    KMethodProgram as KMethodAP,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoSubFavoriteFolderC.GetRuntimeClass import (
    KMethodProgram as KMethodAQ,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoSwiftFRC.GetThisClass import (
    KMethodProgram as KMethodAR,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoThreedViewC.Serialize import (
    KMethodProgram as KMethodAS,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoVectorParameterC.GetThisClass import (
    KMethodProgram as KMethodAT,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoVisPropC.Serialize import (
    KMethodProgram as KMethodAU,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoVisualOverlayObjectC.GetThisClass import (
    KMethodProgram as KMethodAV,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoWeldFavoriteC.GetRuntimeClass import (
    KMethodProgram as KMethodAW,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.MoXformStockC.GetThisClass import (
    KMethodProgram as KMethodAX,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgDim.Serialize import (
    KMethodProgram as KMethodAY,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgEntHandle.Serialize import (
    KMethodProgram as KMethodAZ,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgLogDim.Serialize import (
    KMethodProgram as KMethodBA,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgLogGThreeDim.Serialize import (
    KMethodProgram as KMethodBB,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgSketch.IPostLoad import (
    KMethodProgram as KMethodBC,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgSketch.LoadSketchInPlace import (
    KMethodProgram as KMethodBD,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KMethodProgram as KMethodBE,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgSketch.Serialize import (
    KMethodProgram as KMethodBF,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KMethodProgram as KMethodBG,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Sldmodu.StructConnectionCutSurfIdRepC.GetThisClass import (
    KMethodProgram as KMethodBH,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Swccu.Functions.ReadOperator import (
    KMethodProgram as KMethodBI,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Swccu.SuCArchive.ReadCount import (
    KMethodProgram as KMethodBJ,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Swccu.SuCArchive.ReadObject import (
    KMethodProgram as KMethodBK,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Synthetic.ArchiveContinuationBase import (
    KMethodProgram as KMethodBL,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Synthetic.DisplayDimensionIndices import (
    KMethodProgram as KMethodBM,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Synthetic.ExtrusionDepthScalar import (
    KMethodProgram as KMethodBN,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Synthetic.PerBodyChooserIndex import (
    KMethodProgram as KMethodBO,
)
from convert.adapters.solidworks.programs.resolved.default.Methods.Synthetic.SketchChainEntityIndices import (
    KMethodProgram as KMethodBP,
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
)


# composed tables stay immutable because generated registries expose stable format facts
KFieldOwners, KResolvedOps = BuildProgram(
    KMethodPrograms,
    "ResolvedFeatures",
)

# generated registry exports remain explicit for facade composition and extension imports
__all__ = [
    "KFieldOwners",
    "KResolvedOps",
    "KMethodPrograms",
    "FieldOwners",
    "ResolvedOps",
]

# compatibility binding preserves its established public import after decomposition
FieldOwners = KFieldOwners

# compatibility binding preserves its established public import after decomposition
ResolvedOps = KResolvedOps
