/**
 * Content digests for approvals, manifests and version snapshots (ADR-011,
 * ADR-015).
 *
 * Every hash in the platform comes from here. A second implementation is a
 * review defect, because two implementations that disagree by one byte make
 * approval verification non-reproducible, and approval verification is what
 * the provisioning safety chain rests on.
 */

import { createHash } from "node:crypto";
import { canonicalBytes, type CanonicalValue } from "./canonical.ts";

/** Fields excluded from a document's own digest, by document kind. */
export const DIGEST_EXCLUSIONS: Readonly<Record<string, readonly string[]>> = Object.freeze({
  OdooSandboxManifest: Object.freeze(["checksum", "approvals"]),
  BlueprintPackage: Object.freeze(["checksum", "approvals"]),
  DiscoveryPackage: Object.freeze(["checksum", "approvals"]),
});

/** A `sha256:<hex>` digest string. */
export type Digest = `sha256:${string}`;

/** Digest of an arbitrary value, computed over its canonical form. */
export function digest(value: CanonicalValue): Digest {
  const hash = createHash("sha256").update(canonicalBytes(value)).digest("hex");
  return `sha256:${hash}`;
}

/**
 * Digest of a document, excluding the fields a document cannot contain when
 * its own hash is computed — its checksum, and the approvals appended after
 * the hash exists.
 *
 * Exclusions are top-level only and declared per kind, so the excluded set
 * cannot drift between the TypeScript and Python implementations.
 */
export function documentDigest(
  document: Record<string, CanonicalValue>,
  kind: string,
): Digest {
  const exclusions = DIGEST_EXCLUSIONS[kind];
  if (!exclusions) {
    throw new Error(
      `No digest exclusion set declared for kind "${kind}". Add it to DIGEST_EXCLUSIONS and to the Python mapping.`,
    );
  }
  const subject: Record<string, CanonicalValue> = {};
  for (const [key, value] of Object.entries(document)) {
    if (!exclusions.includes(key)) subject[key] = value;
  }
  return digest(subject);
}

/** Constant-time-ish equality for digest strings. */
export function digestsMatch(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let difference = 0;
  for (let i = 0; i < a.length; i += 1) {
    difference |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return difference === 0;
}
