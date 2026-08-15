# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.brep.validation.BrepView import BrepView


# shell validation preserves oriented face incidence required for closed regions
def GetShellErrors(
    ModelValue: BrepView, IdentitySets: dict[str, frozenset[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for ShellValue in ModelValue.shells:
        if not ShellValue.FaceUseIds:
            ErrorValues.append(f"B-rep shell {ShellValue.EntityId} is empty")
        for FaceUseId in ShellValue.FaceUseIds:
            if FaceUseId not in IdentitySets["FaceUses"]:
                ErrorValues.append(
                    f"B-rep shell {ShellValue.EntityId} references a missing face use"
                )
    for ShellUseValue in ModelValue.shell_uses:
        if ShellUseValue.ShellId not in IdentitySets["Shells"]:
            ErrorValues.append(
                f"B-rep shell use {ShellUseValue.EntityId} references a missing shell"
            )
    return tuple(ErrorValues)
