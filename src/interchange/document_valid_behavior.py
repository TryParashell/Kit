# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# document validation methods preserve the historical model surface without owning rules
class DocumentValid:
    locals()["__slots__"] = ()

    # validation remains a model method while independent rules stay in focused modules
    def GetErrors(SelfValue) -> tuple[str, ...]:
        from .document_validate import GetDocErrors

        return GetDocErrors(SelfValue)

    # explicit assertion gives model callers the established aggregate exception behavior
    def AssertValid(SelfValue) -> None:
        from .document_validate import AssertValid

        AssertValid(SelfValue)
