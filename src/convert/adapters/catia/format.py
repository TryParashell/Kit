from __future__ import annotations

from types import MappingProxyType

from convert.adapters.base import AdapterInfo
from interchange import Capability


PART_DOCUMENT_TYPE = "CATPart"
PRODUCT_DOCUMENT_TYPE = "CATProduct"
DOCUMENT_TYPE_BY_SUFFIX = MappingProxyType(
    {
        ".catpart": PART_DOCUMENT_TYPE,
        ".catproduct": PRODUCT_DOCUMENT_TYPE,
    }
)
SUFFIX_BY_DOCUMENT_TYPE = MappingProxyType(
    {document_type: suffix for suffix, document_type in DOCUMENT_TYPE_BY_SUFFIX.items()}
)
INFO = AdapterInfo(
    format_id="catia.v5",
    name="CATIA V5",
    version="5",
    extensions=tuple(DOCUMENT_TYPE_BY_SUFFIX),
    capabilities=frozenset(Capability),
    media_types=(
        "application/x-catia-part",
        "application/x-catia-product",
    ),
    part_extensions=(SUFFIX_BY_DOCUMENT_TYPE[PART_DOCUMENT_TYPE],),
    assembly_extensions=(SUFFIX_BY_DOCUMENT_TYPE[PRODUCT_DOCUMENT_TYPE],),
)
