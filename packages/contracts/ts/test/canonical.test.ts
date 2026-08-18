import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { canonicalize, CanonicalizationError } from "../src/canonical.ts";
import { digest, documentDigest, digestsMatch } from "../src/digest.ts";

const fixturePath = fileURLToPath(
  new URL("../../fixtures/canonicalization.json", import.meta.url),
);
const fixtures = JSON.parse(readFileSync(fixturePath, "utf8"));

describe("canonicalize", () => {
  for (const testCase of fixtures.cases) {
    it(testCase.name, () => {
      assert.equal(canonicalize(testCase.value), testCase.canonical);
    });
  }

  it("rejects non-finite numbers", () => {
    assert.throws(() => canonicalize(Number.NaN as never), CanonicalizationError);
    assert.throws(() => canonicalize(Number.POSITIVE_INFINITY as never), CanonicalizationError);
  });

  it("rejects numbers outside the safe integer range", () => {
    // These are the values where Python and JavaScript would disagree about
    // the canonical form, and therefore about the digest.
    for (const unsafe of fixtures.rejected.unsafeNumbers) {
      assert.throws(
        () => canonicalize({ n: unsafe }),
        CanonicalizationError,
        `expected ${unsafe} to be refused`,
      );
    }
  });

  it("rejects undefined properties rather than dropping them", () => {
    assert.throws(
      () => canonicalize({ a: undefined } as never),
      CanonicalizationError,
    );
  });

  it("is stable regardless of property insertion order", () => {
    const first = canonicalize({ a: 1, b: { c: 2, d: 3 } });
    const second = canonicalize({ b: { d: 3, c: 2 }, a: 1 });
    assert.equal(first, second);
  });
});

describe("digest", () => {
  it("produces a sha256-prefixed lowercase hex digest", () => {
    const value = digest({ a: 1 });
    assert.match(value, /^sha256:[0-9a-f]{64}$/);
  });

  it("differs when any byte of the canonical form differs", () => {
    assert.notEqual(digest({ a: 1 }), digest({ a: 2 }));
    assert.notEqual(digest({ a: 1 }), digest({ a: "1" }));
  });

  it("ignores the excluded fields for a document kind", () => {
    const { kind, document, equivalentDocument } = fixtures.digestExclusions;
    assert.equal(documentDigest(document, kind), documentDigest(equivalentDocument, kind));
  });

  it("refuses a kind with no declared exclusion set", () => {
    assert.throws(() => documentDigest({ a: 1 }, "UnknownKind"), /No digest exclusion set/);
  });

  it("compares digests without a length shortcut mismatch", () => {
    assert.ok(digestsMatch("sha256:abc", "sha256:abc"));
    assert.ok(!digestsMatch("sha256:abc", "sha256:abd"));
    assert.ok(!digestsMatch("sha256:abc", "sha256:ab"));
  });
});
