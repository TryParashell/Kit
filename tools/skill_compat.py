# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from importlib import import_module as ImportModule
from typing import Any as AnyValue

from tools.descriptions import KDescriptions
from tools.skill_args import ParseArgs
from tools.skill_checker import CheckSkills
from tools.skill_cli import MainRun
from tools.skill_paths import GetSourcePath, GetStaleDirs, GetTargetPath
from tools.skill_render import RenderSkill
from tools.skill_source import StripSource
from tools.skill_specs import ValidateSpecs
from tools.skill_writer import WriteSkills
from tools.yaml_scalar import QuoteYaml


# legacy lookups preserve downstream imports while compliant names own current implementations
KLegacyApi = {
    "ROOT": ("tools.skill_paths", "KRootPath"),
    "SOURCE_DIR": ("tools.skill_paths", "KSourceDir"),
    "TARGET_DIR": ("tools.skill_paths", "KTargetDir"),
    "LICENSE": "LicenseRef-PolyForm-Strict-1.0.0",
    "DESCRIPTIONS": KDescriptions,
    "KIRO_METADATA": ("tools.skill_metadata", "KSkillMetadata"),
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
def GetLegacyAttr(NameText: str) -> AnyValue:
    try:
        ApiValue = KLegacyApi[NameText]
    except KeyError as ErrorInfo:
        raise AttributeError(NameText) from ErrorInfo
    if isinstance(ApiValue, tuple):
        ModuleName, SymbolName = ApiValue
        ApiValue = getattr(ImportModule(ModuleName), SymbolName)
    return ApiValue
