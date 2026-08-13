# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from tools.descriptions import KDescriptions
from tools.skill_metadata import KSkillMetadata
from tools.skill_paths import KRootPath, GetSourcePath
from tools.skill_source import StripSource
from tools.yaml_scalar import QuoteYaml


# shared license identity keeps every generated skill compatible with agent discovery
KLicenseName = "LicenseRef-PolyForm-Strict-1.0.0"


# single skill rendering guarantees checks compare the exact bytes writers produce
def RenderSkill(SkillName: str) -> str:
    SourceFile = GetSourcePath(SkillName)
    MetadataInfo = {
        "source": SourceFile.relative_to(KRootPath).as_posix(),
        "kiro-inclusion": "always",
        **KSkillMetadata.get(SkillName, {}),
    }
    FrontMatter = [
        "---",
        f"name: {SkillName}",
        f"description: {QuoteYaml(KDescriptions[SkillName])}",
        f"license: {KLicenseName}",
        "metadata:",
        *(
            f"  {KeyName}: {QuoteYaml(ValueText)}"
            for KeyName, ValueText in MetadataInfo.items()
        ),
        "---",
        "",
        "",
    ]
    SourceText = SourceFile.read_text(encoding="utf-8")
    return "\n".join(FrontMatter) + StripSource(SourceText)
