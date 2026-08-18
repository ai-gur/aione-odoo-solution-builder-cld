/**
 * RFC 8785 (JSON Canonicalization Scheme) serialization.
 *
 * Canonical form is the only input to any digest computed by the platform
 * (ADR-015). The Python implementation in `packages/contracts/python` must
 * produce byte-identical output for the same value; the shared fixtures in
 * `packages/contracts/fixtures` prove it.
 *
 * JavaScript gets JCS almost for free: `JSON.stringify` already emits ES6
 * `Number::toString` number formatting and RFC 8785 string escaping, and
 * comparing strings with `<` compares UTF-16 code units, which is exactly the
 * key ordering the specification requires. The work here is refusing the
 * values JCS cannot represent rather than formatting the ones it can.
 */

export type CanonicalValue =
  | null
  | boolean
  | number
  | string
  | CanonicalValue[]
  | { [key: string]: CanonicalValue };

export class CanonicalizationError extends Error {
  // Declared as a field rather than a constructor parameter property, so the
  // source runs under Node's strip-only TypeScript support with no build step.
  path: string;

  constructor(message: string, path: string) {
    super(`${message} (at ${path || "<root>"})`);
    this.name = "CanonicalizationError";
    this.path = path;
  }
}

function serialize(value: unknown, path: string): string {
  if (value === null) return "null";

  switch (typeof value) {
    case "boolean":
      return value ? "true" : "false";

    case "number": {
      if (!Number.isFinite(value)) {
        throw new CanonicalizationError(
          `Non-finite number ${String(value)} cannot be canonicalized`,
          path,
        );
      }
      if (Math.abs(value) > Number.MAX_SAFE_INTEGER) {
        // Beyond 2^53 every double is integral, and the two runtimes disagree
        // about what the source text meant: Python reads 12345678901234567890
        // as an exact integer, JavaScript as 12345678901234567000. Identical
        // documents would then produce different digests. Refuse the value
        // instead, and require a string (ADR-015).
        throw new CanonicalizationError(
          `Number magnitude ${String(value)} exceeds the safe integer range; represent it as a string`,
          path,
        );
      }
      // JSON.stringify(-0) yields "0", which is what ES6 Number::toString
      // requires and therefore what JCS requires.
      return JSON.stringify(value);
    }

    case "string":
      return JSON.stringify(value);

    case "undefined":
      throw new CanonicalizationError(
        "undefined is not a JSON value; omit the property instead",
        path,
      );

    case "bigint":
      throw new CanonicalizationError(
        "bigint cannot be canonicalized; use a string or an integer within Number.MAX_SAFE_INTEGER",
        path,
      );

    case "function":
    case "symbol":
      throw new CanonicalizationError(`${typeof value} is not a JSON value`, path);
  }

  if (Array.isArray(value)) {
    const items = value.map((item, index) => serialize(item, `${path}[${index}]`));
    return `[${items.join(",")}]`;
  }

  if (value instanceof Date) {
    throw new CanonicalizationError(
      "Date cannot be canonicalized; format it as an RFC 3339 string first",
      path,
    );
  }

  const record = value as Record<string, unknown>;
  // Sort by UTF-16 code unit, which is what `<` does on JavaScript strings.
  const keys = Object.keys(record).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  const members = keys.map((key) => {
    const child = record[key];
    if (child === undefined) {
      throw new CanonicalizationError(
        `Property "${key}" is undefined; omit it or use null`,
        path,
      );
    }
    return `${JSON.stringify(key)}:${serialize(child, path ? `${path}.${key}` : key)}`;
  });
  return `{${members.join(",")}}`;
}

/** Returns the RFC 8785 canonical JSON text for a value. */
export function canonicalize(value: CanonicalValue): string {
  return serialize(value, "");
}

/** Returns the canonical form as UTF-8 bytes, which is what gets hashed. */
export function canonicalBytes(value: CanonicalValue): Uint8Array {
  return new TextEncoder().encode(canonicalize(value));
}
