from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.canonical import CanonicalError, decode_bytes, dumps, loads_exact  # noqa: E402


@pytest.mark.parametrize(
    ("hex_value", "expected"),
    [
        ("0000000000000000", b"0"),
        ("8000000000000000", b"0"),
        ("0000000000000001", b"5e-324"),
        ("8000000000000001", b"-5e-324"),
        ("7fefffffffffffff", b"1.7976931348623157e+308"),
        ("ffefffffffffffff", b"-1.7976931348623157e+308"),
        ("4340000000000000", b"9007199254740992"),
        ("c340000000000000", b"-9007199254740992"),
        ("4430000000000000", b"295147905179352830000"),
        ("44b52d02c7e14af5", b"9.999999999999997e+22"),
        ("44b52d02c7e14af6", b"1e+23"),
        ("44b52d02c7e14af7", b"1.0000000000000001e+23"),
        ("444b1ae4d6e2ef4e", b"999999999999999700000"),
        ("444b1ae4d6e2ef4f", b"999999999999999900000"),
        ("444b1ae4d6e2ef50", b"1e+21"),
        ("3eb0c6f7a0b5ed8d", b"0.000001"),
        ("3eb0c6f7a0b5ed8c", b"9.999999999999997e-7"),
    ],
)
def test_rfc_8785_appendix_b_binary64_vectors(hex_value: str, expected: bytes) -> None:
    value = struct.unpack(">d", bytes.fromhex(hex_value))[0]
    assert dumps(value) == expected
    assert dumps(loads_exact(expected)) == expected


def test_integral_float_uses_ecmascript_number_form() -> None:
    assert dumps(1.0) == b"1"


def test_object_keys_sort_as_utf16_code_units() -> None:
    assert dumps({"\ue000": 1, "\U00010000": 2}) == '{"𐀀":2,"":1}'.encode()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), "\ud800"])
def test_non_i_json_values_are_rejected(value: object) -> None:
    with pytest.raises(CanonicalError):
        dumps(value)


def test_exact_binary64_integer_is_admitted_but_inexact_integer_requires_string() -> None:
    assert dumps(9007199254740992) == b"9007199254740992"
    with pytest.raises(CanonicalError):
        dumps(9007199254740993)


def test_exact_load_and_base64_reject_alternate_encodings() -> None:
    assert loads_exact(b'{"a":1}') == {"a": 1}
    with pytest.raises(CanonicalError):
        loads_exact(b'{"a":1 }')
    with pytest.raises(CanonicalError):
        decode_bytes("Zh==")
