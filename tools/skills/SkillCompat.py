# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from importlib import import_module as ImportModule
from typing import NamedTuple

from tools.skills.Descriptions import KDescriptions
from tools.skills.SkillArgs import ParseArgs
from tools.skills.SkillChecker import CheckSkills
from tools.skills.SkillCli import MainRun
from tools.skills.SkillPaths import GetSourcePath, GetStaleDirs, GetTargetPath
from tools.skills.SkillRender import RenderSkill
from tools.skills.SkillSource import StripSource
from tools.skills.SkillSpecs import ValidateSpecs
from tools.skills.SkillWriter import WriteSkills
from tools.skills.YamlScalar import QuoteYaml


# delayed imports keep compatibility names available without introducing eager dependency cycles
class ImportPayload(NamedTuple):
    ModuleName: str
    SymbolName: str


# legacy lookups preserve downstream imports while compliant names own current implementations
KLegacyApi: dict[str, object | ImportPayload] = {
    "ROOT": ImportPayload("tools.skills.SkillPaths", "KRootPath"),
    "SOURCE_DIR": ImportPayload("tools.skills.SkillPaths", "KSourceDir"),
    "TARGET_DIR": ImportPayload("tools.skills.SkillPaths", "KTargetDir"),
    "LICENSE": "LicenseRef-PolyForm-Strict-1.0.0",
    "DESCRIPTIONS": KDescriptions,
    "KIRO_METADATA": ImportPayload("tools.skills.SkillMetadata", "KSkillMetadata"),
    "source_body": StripSource,
    "quote_yaml": QuoteYaml,
    "source_path": GetSourcePath,
    "target_path": GetTargetPath,
    "stale_skill_directories": GetStaleDirs,
    "render_skill": RenderSkill,
    "validate_specs": ValidateSpecs,
    "write_skills": WriteSkills,
    "check_skills": CheckSkills,
    "parse_args": ParseArgs,
    "main": MainRun,
}


# compatibility resolution prevents module restructuring from breaking existing automation
def GetLegacyAttr(NameText: str) -> object:
    try:
        ApiValue = KLegacyApi[NameText]
    except KeyError as ErrorInfo:
        raise AttributeError(NameText) from ErrorInfo
    if isinstance(ApiValue, ImportPayload):
        ApiValue = getattr(
            # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
            ImportModule(ApiValue.ModuleName),
            ApiValue.SymbolName,
        )
    return ApiValue
