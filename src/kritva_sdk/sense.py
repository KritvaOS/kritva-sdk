"""Typed Sense 0.1.0 sample models and context-free validation. Standard library only.

The normative sources are the vendored, pinned files under ``kritva_sdk/_schemas/sense/``: the prose contract
``SENSE_CONTRACT.md`` and, as a structural subset only, ``sense-sample.schema.json``. This module is a hand-written
implementation of the context-free rules of the prose contract (sections 3 to 5, the validity coupling of section 6
and the error codes of section 7). It does not import or depend on kritva-sense or jsonschema; equivalence with the
pinned reference validator is proven by tests that use it as an oracle (KOS-SDK-003, AC-008).

Deliberately NOT implemented here, because they need the consumer's context (contract section 6.1):

* freshness (``STALE_DATA`` from age, and the ``INVALID_TIMESTAMP`` clock-mismatch and future-sample checks),
* sequence continuity (``SEQUENCE_REGRESSION``),
* the consumer's usability decision.

A sample that passes ``validate_sample`` is structurally conformant only. It is not thereby fresh, in order or usable,
and a ``STALE``, ``INVALID`` or ``MISSING`` sample is conformant but is not a reading. For ``STALE`` and ``INVALID``
the measurements are the last known values kept for diagnosis; for ``MISSING`` they are empty.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from kritva_sdk.compat import supported_contracts
from kritva_sdk.errors import ContractError, UnsupportedContractVersion, Violation

__all__ = [
    "SENSE_CONTRACT_VERSION", "ERROR_CODES", "FRAMES", "CLOCKS", "TIMESTAMP_UNIT", "VALIDITY_STATES", "KINDS",
    "Measurement", "Timestamp", "SenseSample", "validate_sample", "parse_sample",
]

SENSE_CONTRACT_VERSION = "0.1.0"

ERROR_CODES: tuple[str, ...] = (
    "MISSING_FIELD", "MALFORMED_FIELD", "UNKNOWN_FIELD", "UNSUPPORTED_CONTRACT_VERSION", "INVALID_SENSOR_ID",
    "INVALID_TIMESTAMP", "INVALID_UNIT", "UNKNOWN_FRAME", "INVALID_VALIDITY", "NON_FINITE_VALUE",
    "SEQUENCE_REGRESSION", "STALE_DATA", "MISSING_DATA", "INVALID_DATA",
)
FRAMES: tuple[str, ...] = ("world", "base", "sensor")
CLOCKS: tuple[str, ...] = ("monotonic", "utc")
TIMESTAMP_UNIT = "ns"
VALIDITY_STATES: tuple[str, ...] = ("VALID", "STALE", "MISSING", "INVALID")

# kind -> {measurement name: required unit}; SI only (contract section 3.1).
KINDS: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "imu": MappingProxyType({"accel_x": "m/s^2", "accel_y": "m/s^2", "accel_z": "m/s^2",
                             "gyro_x": "rad/s", "gyro_y": "rad/s", "gyro_z": "rad/s"}),
    "range": MappingProxyType({"distance": "m"}),
    "encoder": MappingProxyType({"position": "rad"}),
    "temperature": MappingProxyType({"temperature": "K"}),
})

_REQUIRED = ("contract_version", "sensor_id", "kind", "sequence", "timestamp", "frame_id", "validity", "measurements")
_OPTIONAL = ("error_code",)
_SENSOR_ID = re.compile(r"^[a-z][a-z0-9_]{0,31}(\.[a-z0-9_]{1,32}){0,3}$")


def _v(code: str, path: str, message: str) -> Violation:
    return Violation(path=path, code=code, message=message)


def _is_int(x: object) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _is_number(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _timestamp_violations(ts: object) -> list[Violation]:
    if not isinstance(ts, dict):
        return [_v("INVALID_TIMESTAMP", "timestamp", "must be an object {clock, unit, value}")]
    out: list[Violation] = []
    for name in ("clock", "unit", "value"):
        if name not in ts:
            out.append(_v("INVALID_TIMESTAMP", f"timestamp.{name}", "required field is absent"))
    for name in ts:
        if name not in ("clock", "unit", "value"):
            out.append(_v("UNKNOWN_FIELD", f"timestamp.{name}", "field is not defined by the contract"))
    if "clock" in ts and ts["clock"] not in CLOCKS:
        out.append(_v("INVALID_TIMESTAMP", "timestamp.clock", "must be one of " + ", ".join(CLOCKS)))
    if "unit" in ts and ts["unit"] != TIMESTAMP_UNIT:
        out.append(_v("INVALID_TIMESTAMP", "timestamp.unit", f"must be {TIMESTAMP_UNIT!r}"))
    if "value" in ts and (not _is_int(ts["value"]) or ts["value"] < 0):
        out.append(_v("INVALID_TIMESTAMP", "timestamp.value", "must be an integer >= 0"))
    return out


def _measurement_violations(meas: object, kind: str | None, validity: str | None) -> list[Violation]:
    if not isinstance(meas, dict):
        return [_v("MALFORMED_FIELD", "measurements", "must be an object")]
    if validity == "MISSING":
        return [_v("MALFORMED_FIELD", "measurements", "must be empty when validity is MISSING")] if meas else []
    out: list[Violation] = []
    spec = KINDS[kind] if kind is not None else None
    if spec is not None:
        for name in spec:
            if name not in meas:
                out.append(_v("MISSING_FIELD", f"measurements.{name}", f"required for kind {kind}"))
    for name, item in meas.items():
        path = f"measurements.{name}"
        if spec is not None and name not in spec:
            out.append(_v("UNKNOWN_FIELD", path, f"not a measurement of kind {kind}"))
            continue
        if not isinstance(item, dict):
            out.append(_v("MALFORMED_FIELD", path, "must be an object {value, unit}"))
            continue
        for field in ("value", "unit"):
            if field not in item:
                out.append(_v("MISSING_FIELD", f"{path}.{field}", "required field is absent"))
        for field in item:
            if field not in ("value", "unit"):
                out.append(_v("UNKNOWN_FIELD", f"{path}.{field}", "field is not defined by the contract"))
        if "value" in item:
            value = item["value"]
            if not _is_number(value):
                out.append(_v("MALFORMED_FIELD", f"{path}.value", "must be a number"))
            elif isinstance(value, float) and not math.isfinite(value):
                out.append(_v("NON_FINITE_VALUE", f"{path}.value", "NaN and infinity are not allowed"))
        if "unit" in item and spec is not None and item["unit"] != spec[name]:
            out.append(_v("INVALID_UNIT", f"{path}.unit", f"must be {spec[name]!r} for {name}"))
    return out


def validate_sample(payload: object) -> tuple[Violation, ...]:
    """Return every context-free violation of ``payload`` against Sense 0.1.0, sorted by (path, code, message).

    An empty tuple means structural conformance only; freshness and sequence continuity are not evaluated (see the
    module docstring). This function never raises for malformed input and never builds a model.
    """
    if not isinstance(payload, dict):
        return (_v("MALFORMED_FIELD", "$", "sample must be an object"),)
    out: list[Violation] = []
    for name in _REQUIRED:
        if name not in payload:
            out.append(_v("MISSING_FIELD", name, "required field is absent"))
    for name in payload:
        if name not in _REQUIRED and name not in _OPTIONAL:
            out.append(_v("UNKNOWN_FIELD", f"{name}", f"field is not defined by contract {SENSE_CONTRACT_VERSION}"))

    if "contract_version" in payload:
        version = payload["contract_version"]
        supported = supported_contracts()["sense"]
        if not isinstance(version, str):
            out.append(_v("MALFORMED_FIELD", "contract_version", "must be a string"))
        elif version not in supported:
            out.append(_v("UNSUPPORTED_CONTRACT_VERSION", "contract_version",
                          f"{version} is not supported (supported: {', '.join(supported)})"))

    if "sensor_id" in payload:
        sid = payload["sensor_id"]
        if not isinstance(sid, str):
            out.append(_v("MALFORMED_FIELD", "sensor_id", "must be a string"))
        elif not _SENSOR_ID.match(sid):
            out.append(_v("INVALID_SENSOR_ID", "sensor_id", "does not match the stable identity pattern"))

    kind: str | None = None
    if "kind" in payload:
        raw_kind = payload["kind"]
        if not isinstance(raw_kind, str):
            out.append(_v("MALFORMED_FIELD", "kind", "must be a string"))
        elif raw_kind not in KINDS:
            out.append(_v("MALFORMED_FIELD", "kind", f"unknown kind {raw_kind!r}"))
        else:
            kind = raw_kind

    if "sequence" in payload and (not _is_int(payload["sequence"]) or payload["sequence"] < 0):
        out.append(_v("MALFORMED_FIELD", "sequence", "must be an integer >= 0"))

    if "timestamp" in payload:
        out.extend(_timestamp_violations(payload["timestamp"]))

    if "frame_id" in payload:
        frame = payload["frame_id"]
        if not isinstance(frame, str):
            out.append(_v("MALFORMED_FIELD", "frame_id", "must be a string"))
        elif frame not in FRAMES:
            out.append(_v("UNKNOWN_FRAME", "frame_id", f"{frame!r} is not a defined frame ({', '.join(FRAMES)})"))

    validity: str | None = None
    if "validity" in payload:
        raw_validity = payload["validity"]
        if isinstance(raw_validity, str) and raw_validity in VALIDITY_STATES:
            validity = raw_validity
        else:
            out.append(_v("INVALID_VALIDITY", "validity", "must be one of " + ", ".join(VALIDITY_STATES)))

    if "error_code" in payload:
        code = payload["error_code"]
        if not (isinstance(code, str) and code in ERROR_CODES):
            out.append(_v("MALFORMED_FIELD", "error_code", "not a code defined by the contract"))
    if validity is not None and validity != "VALID" and "error_code" not in payload:
        out.append(_v("MISSING_FIELD", "error_code", "required when validity is not VALID"))
    if validity == "VALID" and "error_code" in payload:
        out.append(_v("MALFORMED_FIELD", "error_code", "must be absent when validity is VALID"))

    if "measurements" in payload:
        out.extend(_measurement_violations(payload["measurements"], kind, validity))
    return tuple(sorted(out))


@dataclass(frozen=True, slots=True)
class Measurement:
    """One measurement: a finite number and its SI unit, exactly as carried on the wire (no conversion)."""

    value: int | float
    unit: str

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "unit": self.unit}


@dataclass(frozen=True, slots=True)
class Timestamp:
    """Sample time: ``clock`` is ``monotonic`` or ``utc``, ``unit`` is always ``ns``, ``value`` an integer >= 0."""

    clock: str
    value: int
    unit: str = TIMESTAMP_UNIT

    def __post_init__(self) -> None:
        violations = _timestamp_violations(self.to_dict())
        if violations:
            raise ContractError(tuple(violations))

    def to_dict(self) -> dict[str, Any]:
        return {"clock": self.clock, "unit": self.unit, "value": self.value}


def _payload_of(sample: "SenseSample") -> dict[str, Any]:
    ts = sample.timestamp.to_dict() if isinstance(sample.timestamp, Timestamp) else sample.timestamp
    meas = sample.measurements
    meas_payload = ({k: (m.to_dict() if isinstance(m, Measurement) else m) for k, m in meas.items()}
                    if isinstance(meas, Mapping) else meas)
    payload: dict[str, Any] = {
        "contract_version": sample.contract_version, "sensor_id": sample.sensor_id, "kind": sample.kind,
        "sequence": sample.sequence, "timestamp": ts, "frame_id": sample.frame_id, "validity": sample.validity,
        "measurements": meas_payload,
    }
    if sample.error_code is not None:
        payload["error_code"] = sample.error_code
    return payload


@dataclass(frozen=True, slots=True, eq=False)
class SenseSample:
    """An immutable, structurally conformant Sense 0.1.0 sample.

    Construction validates; a non-conformant value cannot be represented. ``error_code`` is ``None`` exactly when the
    wire sample has no ``error_code`` field. For ``MISSING`` the measurements are empty; for ``STALE`` and ``INVALID``
    they are the last known values and are not readings.
    """

    contract_version: str
    sensor_id: str
    kind: str
    sequence: int
    timestamp: Timestamp
    frame_id: str
    validity: str
    measurements: Mapping[str, Measurement]
    error_code: str | None = None

    def __post_init__(self) -> None:
        violations = validate_sample(_payload_of(self))
        if violations:
            raise ContractError(violations)
        object.__setattr__(self, "measurements", MappingProxyType(dict(self.measurements)))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dict: no unit conversion, no omitted field, ``error_code`` only if set."""
        return _payload_of(self)

    def _key(self) -> tuple[Any, ...]:
        return (self.contract_version, self.sensor_id, self.kind, self.sequence, self.timestamp, self.frame_id,
                self.validity, tuple(sorted(self.measurements.items())), self.error_code)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SenseSample) and self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    @classmethod
    def from_dict(cls, payload: object) -> "SenseSample":
        """Same as :func:`parse_sample`."""
        return parse_sample(payload)


def parse_sample(payload: object) -> SenseSample:
    """Validate ``payload`` and build a :class:`SenseSample`, or raise.

    An unsupported ``contract_version`` string raises :class:`UnsupportedContractVersion` immediately, before any
    other semantic validation is attempted under a version this release does not implement. Any other defect raises
    :class:`ContractError` carrying every violation in (path, code, message) order and the upstream codes.
    """
    if isinstance(payload, dict) and isinstance(payload.get("contract_version"), str):
        supported = supported_contracts()["sense"]
        if payload["contract_version"] not in supported:
            raise UnsupportedContractVersion.for_version("sense", payload["contract_version"], "contract_version", supported)
    violations = validate_sample(payload)
    if violations:
        raise ContractError(violations)
    assert isinstance(payload, dict)
    ts = payload["timestamp"]
    return SenseSample(
        contract_version=payload["contract_version"], sensor_id=payload["sensor_id"], kind=payload["kind"],
        sequence=payload["sequence"],
        timestamp=Timestamp(clock=ts["clock"], value=ts["value"], unit=ts["unit"]),
        frame_id=payload["frame_id"], validity=payload["validity"],
        measurements={k: Measurement(value=m["value"], unit=m["unit"]) for k, m in payload["measurements"].items()},
        error_code=payload.get("error_code"),
    )
