"""Canonical JSON, hashing, and lossless byte helpers."""

from __future__ import annotations

import base64
import hashlib
import json
import math
from decimal import Decimal
from typing import Any


class CanonicalError(ValueError):
    pass


def _validate(value: Any) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        try:
            binary64 = float(value)
        except OverflowError as exc:
            raise CanonicalError("integer is not an exact finite binary64 value; encode it as a string") from exc
        if not math.isfinite(binary64) or int(binary64) != value:
            raise CanonicalError("integer is not an exact finite binary64 value; encode it as a string")
        return
    if isinstance(value, str):
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise CanonicalError("lone UTF-16 surrogates are not canonical JSON")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalError("non-finite numbers are not canonical JSON")
        return
    if isinstance(value, list):
        for item in value:
            _validate(item)
        return
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise CanonicalError("canonical JSON mapping keys must be strings")
        for key, item in value.items():
            _validate(key)
            _validate(item)
        return
    raise CanonicalError(f"unsupported canonical JSON value: {type(value).__name__}")


def _float_text(value: float) -> str:
    if value == 0:
        return "0"
    # Python and ECMAScript both begin from the shortest round-tripping binary64
    # decimal. RFC 8785 then differs only in fixed/scientific thresholds and
    # exponent spelling for that decimal representation.
    shortest = repr(value).lower()
    decimal = Decimal(shortest)
    absolute = abs(value)
    if 1e-6 <= absolute < 1e21:
        return format(decimal, "f").rstrip("0").rstrip(".") if "." in format(decimal, "f") else format(decimal, "f")
    mantissa, exponent = format(decimal.normalize(), "e").split("e")
    mantissa = mantissa.rstrip("0").rstrip(".")
    exponent_value = int(exponent)
    sign = "+" if exponent_value >= 0 else ""
    return f"{mantissa}e{sign}{exponent_value}"


def _render(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        # JSON numbers are binary64 values under RFC 8785.  Rendering through
        # that domain also applies ECMAScript's fixed/scientific thresholds to
        # exact integral inputs such as 10**21.
        return _float_text(float(value))
    if isinstance(value, float):
        return _float_text(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_render(item) for item in value) + "]"
    if isinstance(value, dict):
        # RFC 8785 orders property names by UTF-16 code units, not Unicode
        # scalar value. Supplementary characters therefore sort before some
        # BMP values even though Python's ordinary string order says otherwise.
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return "{" + ",".join(_render(key) + ":" + _render(value[key]) for key in keys) + "}"
    raise CanonicalError(f"unsupported canonical JSON value: {type(value).__name__}")


def dumps(value: Any) -> bytes:
    """Return RFC 8785 canonical UTF-8 JSON bytes."""
    _validate(value)
    return _render(value).encode("utf-8")


def loads_exact(raw: bytes) -> Any:
    def parse_integer(text: str) -> int | float:
        value = int(text)
        if abs(value) <= 9007199254740991:
            return value
        # Canonical binary64 output may be an integer token outside the
        # interoperable small-integer range.  Preserve its numeric domain as a
        # float so our own canonical output is accepted on read-back.
        return float(text)

    try:
        value = json.loads(raw.decode("utf-8"), parse_int=parse_integer)
    except (UnicodeDecodeError, json.JSONDecodeError, OverflowError) as exc:
        raise CanonicalError(f"invalid JSON: {exc}") from exc
    _validate(value)
    if dumps(value) != raw:
        raise CanonicalError("JSON is not in canonical form")
    return value


def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest(value: Any) -> str:
    return digest_bytes(dumps(value))


def encode_bytes(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def decode_bytes(text: str) -> bytes:
    if not isinstance(text, str):
        raise CanonicalError("base64 value must be a string")
    try:
        raw = base64.b64decode(text, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise CanonicalError("invalid canonical base64") from exc
    if encode_bytes(raw) != text:
        raise CanonicalError("non-canonical base64")
    return raw
