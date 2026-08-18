"""RFC 8785 (JSON Canonicalization Scheme) serialization.

Canonical form is the only input to any digest computed by the platform
(ADR-015). This module must produce byte-identical output to the TypeScript
implementation in ``packages/contracts/ts``; the shared fixtures in
``packages/contracts/fixtures`` prove it.

Python needs more work than JavaScript for one reason: number formatting.
RFC 8785 defers to ECMAScript ``Number::toString``, and Python's ``repr`` uses
different thresholds for switching to exponential notation (``repr(1e16)`` is
``'1e+16'`` where JavaScript gives ``'10000000000000000'``). ``_format_number``
implements the ECMAScript algorithm rather than patching ``repr`` output.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

__all__ = ["canonicalize", "canonical_bytes", "CanonicalizationError"]


class CanonicalizationError(ValueError):
    """A value cannot be represented in canonical JSON."""

    def __init__(self, message: str, path: str) -> None:
        super().__init__(f"{message} (at {path or '<root>'})")
        self.path = path


# Short escapes required by RFC 8785 section 3.2.2.2. Every other control
# character below 0x20 uses the \u00xx form; everything at or above 0x20 except
# quote and backslash is emitted literally.
_SHORT_ESCAPES = {
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0C: "\\f",
    0x0D: "\\r",
    0x22: '\\"',
    0x5C: "\\\\",
}


def _format_string(value: str) -> str:
    out = ['"']
    for char in value:
        code = ord(char)
        escape = _SHORT_ESCAPES.get(code)
        if escape is not None:
            out.append(escape)
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(char)
    out.append('"')
    return "".join(out)


# Beyond 2^53 the two runtimes disagree about what a number literal meant:
# Python reads 12345678901234567890 as an exact integer, JavaScript as the
# double 12345678901234567000. Identical documents would then produce different
# digests, so both implementations refuse the value and require a string
# instead (ADR-015).
MAX_SAFE_INTEGER = 9007199254740991


def _format_number(value: float | int, path: str) -> str:
    if not isinstance(value, int) and (math.isnan(value) or math.isinf(value)):
        raise CanonicalizationError(
            f"Non-finite number {value} cannot be canonicalized", path
        )

    if abs(value) > MAX_SAFE_INTEGER:
        raise CanonicalizationError(
            f"Number magnitude {value} exceeds the safe integer range; "
            "represent it as a string",
            path,
        )

    if isinstance(value, int):
        return str(value)

    # ECMAScript String(-0) is "0", and so is String(0).
    if value == 0:
        return "0"

    sign = "-" if value < 0 else ""

    # repr gives the shortest round-tripping decimal, which is the same digit
    # sequence ECMAScript selects. normalize() strips trailing zeros so that
    # 100.0 yields digits "1" with exponent 2 rather than "1000" with -1.
    decimal_value = Decimal(repr(abs(value))).normalize()
    _, digit_tuple, exponent = decimal_value.as_tuple()
    digits = "".join(str(digit) for digit in digit_tuple)
    k = len(digits)
    # n is the position of the decimal point: value == 0.digits * 10**n
    n = k + int(exponent)

    if k <= n <= 21:
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + digits
    # Exponential notation.
    exponent_part = n - 1
    exponent_sign = "+" if exponent_part >= 0 else "-"
    mantissa = digits if k == 1 else digits[0] + "." + digits[1:]
    return f"{sign}{mantissa}e{exponent_sign}{abs(exponent_part)}"


def _sort_key(key: str) -> bytes:
    # RFC 8785 orders keys by UTF-16 code unit. Python compares by code point,
    # which differs for characters outside the Basic Multilingual Plane, so
    # sort on the UTF-16 big-endian encoding instead.
    return key.encode("utf-16-be")


def _serialize(value: Any, path: str) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _format_number(value, path)
    if isinstance(value, str):
        return _format_string(value)
    if isinstance(value, (list, tuple)):
        items = [_serialize(item, f"{path}[{index}]") for index, item in enumerate(value)]
        return "[" + ",".join(items) + "]"
    if isinstance(value, dict):
        members = []
        for key in sorted(value.keys(), key=_sort_key):
            if not isinstance(key, str):
                raise CanonicalizationError(
                    f"Object keys must be strings, found {type(key).__name__}", path
                )
            child_path = f"{path}.{key}" if path else key
            members.append(f"{_format_string(key)}:{_serialize(value[key], child_path)}")
        return "{" + ",".join(members) + "}"

    raise CanonicalizationError(
        f"{type(value).__name__} is not a JSON value; convert it before canonicalizing",
        path,
    )


def canonicalize(value: Any) -> str:
    """Return the RFC 8785 canonical JSON text for a value."""
    return _serialize(value, "")


def canonical_bytes(value: Any) -> bytes:
    """Return the canonical form as UTF-8 bytes, which is what gets hashed."""
    return canonicalize(value).encode("utf-8")
