"""Content digests for approvals, manifests and version snapshots.

Every hash in the platform comes from here (ADR-011, ADR-015). A second
implementation is a review defect: two implementations that disagree by one
byte make approval verification non-reproducible, and approval verification is
what the provisioning safety chain rests on.

The exclusion sets below must stay identical to ``DIGEST_EXCLUSIONS`` in
``packages/contracts/ts/src/digest.ts``. The shared fixtures assert it.
"""

from __future__ import annotations

import hashlib
import hmac
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import canonical_bytes

__all__ = ["digest", "document_digest", "digests_match", "DIGEST_EXCLUSIONS"]

DIGEST_EXCLUSIONS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "OdooSandboxManifest": ("checksum", "approvals"),
        "BlueprintPackage": ("checksum", "approvals"),
        "DiscoveryPackage": ("checksum", "approvals"),
    }
)


def digest(value: Any) -> str:
    """Digest of an arbitrary value, computed over its canonical form."""
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def document_digest(document: Mapping[str, Any], kind: str) -> str:
    """Digest of a document, excluding the fields it cannot contain when its
    own hash is computed — its checksum, and the approvals appended after the
    hash exists.

    Exclusions are top-level only and declared per kind, so the excluded set
    cannot drift between the Python and TypeScript implementations.
    """
    exclusions = DIGEST_EXCLUSIONS.get(kind)
    if exclusions is None:
        raise KeyError(
            f'No digest exclusion set declared for kind "{kind}". '
            "Add it to DIGEST_EXCLUSIONS and to the TypeScript mapping."
        )
    subject = {key: value for key, value in document.items() if key not in exclusions}
    return digest(subject)


def digests_match(left: str, right: str) -> bool:
    """Compare two digest strings without leaking timing information."""
    return hmac.compare_digest(left, right)
