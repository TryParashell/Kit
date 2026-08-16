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

    # validation remains concrete so callers receive the runtime tuple contract directly
    def validate(self) -> tuple[str, ...]:
        from interchange.document.validation.DocumentValidate import (
            GetDocErrors,
        )  # lgtm[py/cyclic-import]
        from interchange.document.validation.DocumentBoundary import (
            GetDocument,
        )  # lgtm[py/cyclic-import]

        DocumentValue = GetDocument(self)
        if DocumentValue is None:
            raise TypeError("validation requires a CadDocument")
        return GetDocErrors(DocumentValue)

    # assertion remains concrete so callers avoid object returning compatibility lookup
    def assert_valid(self) -> None:
        from interchange.document.validation.DocumentValidate import (
            AssertValid,
        )  # lgtm[py/cyclic-import]
        from interchange.document.validation.DocumentBoundary import (
            GetDocument,
        )  # lgtm[py/cyclic-import]

        DocumentValue = GetDocument(self)
        if DocumentValue is None:
            raise TypeError("validation requires a CadDocument")
        AssertValid(DocumentValue)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def GetErrors(self) -> tuple[str, ...]:
        return self.validate()

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def AssertValid(self) -> None:
        self.assert_valid()
