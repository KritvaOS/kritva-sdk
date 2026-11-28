"""Typed Sense telemetry stream 0.1.0 models and an incremental, deterministic checker. Standard library only.

The normative source is the vendored, pinned prose contract ``kritva_sdk/_schemas/sense/STREAM_CONTRACT.md``
(KOS-SENSE-STREAM-001, program decision D-088) and, as a structural subset only, ``stream.schema.json``. This module
is a hand-written implementation of that contract. It does not import or depend on kritva-sense or jsonschema;
equivalence with the pinned reference checker is proven by tests that use it as an oracle (KOS-SDK-005).

A stream document is ``{stream_version, records}`` with exactly three record kinds: one ``open``, any number of
``sample`` and one ``close``. Every embedded sample is validated by the unchanged Sense 0.1.0 validator
(:func:`kritva_sdk.sense.validate_sample`). The checker reports two kept-apart lists, both sorted by
``(position, code, path, message)`` where position is the 0-based record position (-1 for the document as a whole):

* stream diagnostics, with the ``STREAM_`` codes of the stream contract, and
* sample violations, with the unchanged Sense 0.1.0 codes.

Upstream codes are preserved verbatim and never remapped. ``STREAM_SEQUENCE_*`` diagnostics are stream diagnostics,
not sample validation. Argument mistakes made by the caller of this module (a record batch that is not a list,
feeding a finished checker) raise :class:`StreamUsageError`, which is not a contract diagnostic.

A conformant stream says only that its records are well formed and consistent under these rules. It says nothing
about sensor freshness, calibration, clock synchronisation, physical correctness or safety, and no transport,
buffering, loss recovery, stream merging or real-time property is defined or implemented here.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from kritva_sdk.compat import supported_contracts
from kritva_sdk.errors import ContractError, SdkError, Violation
from kritva_sdk.sense import CLOCKS, KINDS, TIMESTAMP_UNIT, SenseSample, parse_sample, validate_sample
from kritva_sdk.sense import _SENSOR_ID as _SENSOR_ID_RE

__all__ = [
    "STREAM_CONTRACT_VERSION", "STREAM_ERROR_CODES", "RECORD_KINDS", "StreamDiagnostic", "SampleViolation",
    "StreamResult", "StreamChecker", "check_stream", "StreamOpen", "StreamSample", "StreamClose", "Stream",
    "parse_stream", "StreamUsageError", "StreamContractError", "UnsupportedStreamVersion",
]

STREAM_CONTRACT_VERSION = "0.1.0"

STREAM_ERROR_CODES: tuple[str, ...] = (
    "STREAM_MALFORMED", "STREAM_MISSING_FIELD", "STREAM_UNKNOWN_FIELD", "STREAM_UNSUPPORTED_VERSION",
    "STREAM_UNKNOWN_RECORD", "STREAM_INDEX_MISMATCH", "STREAM_OPEN_MISSING", "STREAM_OPEN_NOT_FIRST",
    "STREAM_OPEN_REPEATED", "STREAM_SAMPLE_BEFORE_OPEN", "STREAM_SAMPLE_AFTER_CLOSE", "STREAM_CLOSE_BEFORE_OPEN",
    "STREAM_CLOSE_REPEATED", "STREAM_UNTERMINATED", "STREAM_SEQUENCE_DUPLICATE", "STREAM_SEQUENCE_REGRESSION",
    "STREAM_SEQUENCE_GAP", "STREAM_FIRST_SEQUENCE_UNMET", "STREAM_LAST_SEQUENCE_UNMET",
    "STREAM_TIMESTAMP_REGRESSION", "STREAM_CLOCK_MISMATCH", "STREAM_SENSOR_CHANGE", "STREAM_KIND_CHANGE",
)

RECORD_KINDS: tuple[str, ...] = ("open", "sample", "close")
_DOCUMENT_FIELDS = ("stream_version", "records")
# record kind -> (required fields, optional fields); ``record`` and ``index`` are required for every kind
_RECORD_FIELDS: Mapping[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "open": (("record", "index", "stream_id", "sensor_id", "kind", "clock"), ("first_sequence",)),
    "sample": (("record", "index", "sample"), ()),
    "close": (("record", "index"), ("last_sequence",)),
}


class StreamUsageError(SdkError, ValueError):
    """The caller misused the stream API (not a contract diagnostic): a bad argument or a finished checker."""


@dataclass(frozen=True, slots=True, order=True)
class StreamDiagnostic:
    """One stream diagnostic: a ``STREAM_`` code at a record position (-1: the document) and a path."""

    position: int
    code: str
    path: str
    message: str


@dataclass(frozen=True, slots=True, order=True)
class SampleViolation:
    """One violation of the Sense 0.1.0 contract inside a ``sample`` record, with its code unchanged."""

    position: int
    code: str
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class StreamResult:
    """Stream diagnostics and sample violations, kept apart and each sorted by (position, code, path, message)."""

    stream: tuple[StreamDiagnostic, ...] = ()
    samples: tuple[SampleViolation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "stream", tuple(sorted(self.stream)))
        object.__setattr__(self, "samples", tuple(sorted(self.samples)))

    @property
    def conformant(self) -> bool:
        """True only when there is no stream diagnostic and no sample violation."""
        return not self.stream and not self.samples

    def as_tuples(self) -> tuple[tuple[tuple[int, str, str, str], ...], tuple[tuple[int, str, str, str], ...]]:
        """Return ``(stream, samples)`` as plain (position, code, path, message) tuples."""
        return (tuple((d.position, d.code, d.path, d.message) for d in self.stream),
                tuple((v.position, v.code, v.path, v.message) for v in self.samples))


def _is_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_seq(v: object) -> bool:
    return _is_int(v) and v >= 0  # type: ignore[operator]


class StreamChecker:
    """Incremental checker. :meth:`feed` takes the next records in order, in batches of any size, and
    :meth:`finish` ends the stream. The same ordered records give the same result for every split into batches
    (including empty batches). A new checker treats its first record as position 0, so a batch checked alone is a
    complete stream of its own. Records are never dropped, reordered or repaired; an unterminated stream is reported
    and not closed on the producer's behalf. Each :meth:`feed` and :meth:`finish` returns only the entries that call
    added; :meth:`result` returns everything so far.
    """

    def __init__(self) -> None:
        self._position = 0
        self._finished = False
        self._state = "NONE"          # NONE (no open yet), OPEN, CLOSED
        self._have_open = False
        self._ident: dict[str, str] = {}   # valid identity fields fixed by the first open record
        self._first_bound: int | None = None
        self._open_samples = 0        # sample records seen while the stream was open
        self._last_open_seq: int | None = None
        self._prev_seq: int | None = None
        self._prev_ts: tuple[str, int] | None = None
        self._stream: list[StreamDiagnostic] = []
        self._samples: list[SampleViolation] = []

    # -- public -------------------------------------------------------------------------------------------------
    @property
    def finished(self) -> bool:
        return self._finished

    def feed(self, records: Iterable[Any]) -> StreamResult:
        """Check the next records. Each is a JSON-style dict, or a :class:`StreamOpen`, :class:`StreamSample` or
        :class:`StreamClose`. Raises :class:`StreamUsageError` when ``records`` is not a list or tuple, or after
        :meth:`finish`; in both cases nothing is consumed."""
        if self._finished:
            raise StreamUsageError("the stream is finished; no more records can be fed")
        if not isinstance(records, (list, tuple)):
            raise StreamUsageError("records must be a list or a tuple")
        before = (len(self._stream), len(self._samples))
        for rec in records:
            self._record(rec.to_dict() if isinstance(rec, (StreamOpen, StreamSample, StreamClose)) else rec)
        return StreamResult(tuple(self._stream[before[0]:]), tuple(self._samples[before[1]:]))

    def finish(self) -> StreamResult:
        """End the stream and report the end-of-stream diagnostics. Raises :class:`StreamUsageError` if already done."""
        if self._finished:
            raise StreamUsageError("the stream is already finished")
        before = (len(self._stream), len(self._samples))
        self._finished = True
        if not self._have_open:
            self._add(-1, "STREAM_OPEN_MISSING", "records", "the stream has no open record")
        elif self._state != "CLOSED":
            self._add(-1, "STREAM_UNTERMINATED", "records", "the stream has no close record; it is not repaired")
            if self._first_bound is not None and self._open_samples == 0:
                self._add(-1, "STREAM_FIRST_SEQUENCE_UNMET", "records",
                          "first_sequence %d was stated but no sample followed the open record" % self._first_bound)
        return StreamResult(tuple(self._stream[before[0]:]), tuple(self._samples[before[1]:]))

    def result(self) -> StreamResult:
        """Everything reported so far, sorted."""
        return StreamResult(tuple(self._stream), tuple(self._samples))

    # -- internals ----------------------------------------------------------------------------------------------
    def _add(self, position: int, code: str, path: str, message: str) -> None:
        self._stream.append(StreamDiagnostic(position, code, path, message))

    def _record(self, rec: object) -> None:
        pos = self._position
        self._position += 1
        path = "records[%d]" % pos
        if not isinstance(rec, dict):
            self._add(pos, "STREAM_MALFORMED", path, "a record must be an object")
            return
        kind = None
        if "record" not in rec:
            self._add(pos, "STREAM_MISSING_FIELD", path + ".record", "required field is absent")
        elif not isinstance(rec["record"], str) or rec["record"] not in RECORD_KINDS:
            self._add(pos, "STREAM_UNKNOWN_RECORD", path + ".record", "must be one of %s" % ", ".join(RECORD_KINDS))
        else:
            kind = rec["record"]
        # index: required for every record kind, and equal to the 0-based position
        if "index" not in rec:
            self._add(pos, "STREAM_MISSING_FIELD", path + ".index", "required field is absent")
        elif not _is_seq(rec["index"]):
            self._add(pos, "STREAM_MALFORMED", path + ".index", "must be an integer >= 0")
        elif rec["index"] != pos:
            self._add(pos, "STREAM_INDEX_MISMATCH", path + ".index", "index %d at position %d" % (rec["index"], pos))
        if kind is None:
            return                       # no lifecycle effect; fields cannot be judged without a kind
        required, optional = _RECORD_FIELDS[kind]
        for f in required:
            if f not in rec and f not in ("record", "index"):
                self._add(pos, "STREAM_MISSING_FIELD", "%s.%s" % (path, f), "required field is absent")
        for f in rec:
            if f not in required and f not in optional:
                self._add(pos, "STREAM_UNKNOWN_FIELD", "%s.%s" % (path, f), "field is not defined by the contract")
        if kind == "open":
            self._open(pos, path, rec)
        elif kind == "sample":
            self._sample(pos, path, rec)
        else:
            self._close(pos, path, rec)

    def _open(self, pos: int, path: str, rec: dict[str, Any]) -> None:
        ident: dict[str, str] = {}
        if "stream_id" in rec:
            if isinstance(rec["stream_id"], str) and _SENSOR_ID_RE.match(rec["stream_id"]):
                ident["stream_id"] = rec["stream_id"]
            else:
                self._add(pos, "STREAM_MALFORMED", path + ".stream_id", "must match the identity pattern")
        if "sensor_id" in rec:
            if isinstance(rec["sensor_id"], str) and _SENSOR_ID_RE.match(rec["sensor_id"]):
                ident["sensor_id"] = rec["sensor_id"]
            else:
                self._add(pos, "STREAM_MALFORMED", path + ".sensor_id", "must match the sensor identity pattern")
        if "kind" in rec:
            if isinstance(rec["kind"], str) and rec["kind"] in KINDS:
                ident["kind"] = rec["kind"]
            else:
                self._add(pos, "STREAM_MALFORMED", path + ".kind", "must be one of %s" % ", ".join(KINDS))
        if "clock" in rec:
            if isinstance(rec["clock"], str) and rec["clock"] in CLOCKS:
                ident["clock"] = rec["clock"]
            else:
                self._add(pos, "STREAM_MALFORMED", path + ".clock", "must be one of %s" % ", ".join(CLOCKS))
        first = None
        if "first_sequence" in rec:
            if _is_seq(rec["first_sequence"]):
                first = rec["first_sequence"]
            else:
                self._add(pos, "STREAM_MALFORMED", path + ".first_sequence", "must be an integer >= 0")
        if self._state == "NONE":
            if pos != 0:
                self._add(pos, "STREAM_OPEN_NOT_FIRST", path, "the open record must be the first record")
            self._state = "OPEN"
            self._have_open = True
            self._ident = ident
            self._first_bound = first
        else:
            self._add(pos, "STREAM_OPEN_REPEATED", path, "the stream is already open; this record changes nothing")

    def _sample(self, pos: int, path: str, rec: dict[str, Any]) -> None:
        if self._state == "NONE":
            self._add(pos, "STREAM_SAMPLE_BEFORE_OPEN", path, "no open record precedes this sample")
        elif self._state == "CLOSED":
            self._add(pos, "STREAM_SAMPLE_AFTER_CLOSE", path, "the stream is closed")
        if "sample" not in rec:
            return
        s = rec["sample"]
        # every embedded value goes to the unchanged Sense 0.1.0 validator, objects or not
        for v in validate_sample(s):
            self._samples.append(SampleViolation(pos, v.code, v.path, v.message))
        if not isinstance(s, dict):
            self._add(pos, "STREAM_MALFORMED", path + ".sample", "must be an object")
            return
        seq = s.get("sequence") if _is_seq(s.get("sequence")) else None
        ts = s.get("timestamp")
        # a recognised clock is enough to compare with the stream clock; a usable timestamp (for the regression
        # check) also needs the unit ns and an integer value >= 0, as the sample contract requires
        clock_ok = isinstance(ts, dict) and isinstance(ts.get("clock"), str) and ts["clock"] in CLOCKS
        ts_ok = clock_ok and ts.get("unit") == TIMESTAMP_UNIT and _is_seq(ts.get("value"))
        # identity and clock, against the values fixed by the open record
        if "sensor_id" in self._ident and isinstance(s.get("sensor_id"), str) \
                and s["sensor_id"] != self._ident["sensor_id"]:
            self._add(pos, "STREAM_SENSOR_CHANGE", path + ".sample.sensor_id",
                      "%r differs from the stream sensor %r" % (s["sensor_id"], self._ident["sensor_id"]))
        if "kind" in self._ident and isinstance(s.get("kind"), str) and s["kind"] != self._ident["kind"]:
            self._add(pos, "STREAM_KIND_CHANGE", path + ".sample.kind",
                      "%r differs from the stream kind %r" % (s["kind"], self._ident["kind"]))
        if "clock" in self._ident and clock_ok and ts["clock"] != self._ident["clock"]:
            self._add(pos, "STREAM_CLOCK_MISMATCH", path + ".sample.timestamp.clock",
                      "%s differs from the stream clock %s" % (ts["clock"], self._ident["clock"]))
        # sequence continuity against the previous sample record with a usable sequence
        if seq is not None:
            if self._prev_seq is not None:
                p = self._prev_seq
                if seq == p:
                    self._add(pos, "STREAM_SEQUENCE_DUPLICATE", path + ".sample.sequence",
                              "%d equals the previous sequence" % seq)
                elif seq < p:
                    self._add(pos, "STREAM_SEQUENCE_REGRESSION", path + ".sample.sequence",
                              "%d is lower than the previous sequence %d" % (seq, p))
                elif seq > p + 1:
                    self._add(pos, "STREAM_SEQUENCE_GAP", path + ".sample.sequence",
                              "sequence %d to %d missing (previous %d, this %d)" % (p + 1, seq - 1, p, seq))
            self._prev_seq = seq
        # timestamps: comparable only on the same clock
        if ts_ok:
            if self._prev_ts is not None and self._prev_ts[0] == ts["clock"] and ts["value"] < self._prev_ts[1]:
                self._add(pos, "STREAM_TIMESTAMP_REGRESSION", path + ".sample.timestamp.value",
                          "%d is lower than the previous timestamp %d" % (ts["value"], self._prev_ts[1]))
            self._prev_ts = (ts["clock"], ts["value"])
        if self._state == "OPEN":
            self._open_samples += 1
            if self._open_samples == 1 and self._first_bound is not None and seq is not None \
                    and seq != self._first_bound:
                self._add(pos, "STREAM_FIRST_SEQUENCE_UNMET", path + ".sample.sequence",
                          "first sample has sequence %d, the open record states first_sequence %d"
                          % (seq, self._first_bound))
            self._last_open_seq = seq

    def _close(self, pos: int, path: str, rec: dict[str, Any]) -> None:
        last = None
        if "last_sequence" in rec:
            if _is_seq(rec["last_sequence"]):
                last = rec["last_sequence"]
            else:
                self._add(pos, "STREAM_MALFORMED", path + ".last_sequence", "must be an integer >= 0")
        if self._state == "NONE":
            self._add(pos, "STREAM_CLOSE_BEFORE_OPEN", path, "no open record precedes this close")
        elif self._state == "CLOSED":
            self._add(pos, "STREAM_CLOSE_REPEATED", path, "the stream is already closed")
        else:
            self._state = "CLOSED"
            if self._open_samples == 0:
                if self._first_bound is not None:
                    self._add(pos, "STREAM_FIRST_SEQUENCE_UNMET", path,
                              "first_sequence %d was stated but no sample followed the open record"
                              % self._first_bound)
                if last is not None:
                    self._add(pos, "STREAM_LAST_SEQUENCE_UNMET", path,
                              "last_sequence %d was stated but no sample followed the open record" % last)
            elif last is not None and self._last_open_seq is not None and self._last_open_seq != last:
                self._add(pos, "STREAM_LAST_SEQUENCE_UNMET", path + ".last_sequence",
                          "last sample has sequence %d, the close record states last_sequence %d"
                          % (self._last_open_seq, last))


def check_stream(doc: object) -> StreamResult:
    """Check a stream document (``{stream_version, records}``) as one complete stream and return its result.

    Never raises for a bad document; every defect is a diagnostic. An unsupported ``stream_version`` string is
    reported as ``STREAM_UNSUPPORTED_VERSION`` and the records are still checked.
    """
    if not isinstance(doc, dict):
        return StreamResult((StreamDiagnostic(-1, "STREAM_MALFORMED", "$", "the document must be an object"),), ())
    checker = StreamChecker()
    for f in _DOCUMENT_FIELDS:
        if f not in doc:
            checker._add(-1, "STREAM_MISSING_FIELD", f, "required field is absent")
    for f in doc:
        if f not in _DOCUMENT_FIELDS:
            checker._add(-1, "STREAM_UNKNOWN_FIELD", f,
                         "field is not defined by stream contract %s" % STREAM_CONTRACT_VERSION)
    if "stream_version" in doc:
        ver = doc["stream_version"]
        supported = supported_contracts()["stream"]
        if not isinstance(ver, str):
            checker._add(-1, "STREAM_MALFORMED", "stream_version", "must be a string")
        elif ver not in supported:
            checker._add(-1, "STREAM_UNSUPPORTED_VERSION", "stream_version",
                         "%s is not supported (supported: %s)" % (ver, ", ".join(supported)))
    if "records" in doc:
        if not isinstance(doc["records"], list):
            checker._add(-1, "STREAM_MALFORMED", "records", "must be an array")
        else:
            checker.feed(doc["records"])
            checker.finish()
    return checker.result()


# -- typed models ----------------------------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class StreamOpen:
    """The ``open`` record: the identity of the stream, fixed for its lifetime."""

    index: int
    stream_id: str
    sensor_id: str
    kind: str
    clock: str
    first_sequence: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"record": "open", "index": self.index, "stream_id": self.stream_id,
                               "sensor_id": self.sensor_id, "kind": self.kind, "clock": self.clock}
        if self.first_sequence is not None:
            out["first_sequence"] = self.first_sequence
        return out


@dataclass(frozen=True, slots=True)
class StreamSample:
    """A ``sample`` record carrying one conformant Sense 0.1.0 sample."""

    index: int
    sample: SenseSample

    def to_dict(self) -> dict[str, Any]:
        return {"record": "sample", "index": self.index, "sample": self.sample.to_dict()}


@dataclass(frozen=True, slots=True)
class StreamClose:
    """The ``close`` record."""

    index: int
    last_sequence: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"record": "close", "index": self.index}
        if self.last_sequence is not None:
            out["last_sequence"] = self.last_sequence
        return out


@dataclass(frozen=True, slots=True)
class Stream:
    """A complete, conformant stream: one open, zero or more samples, one close, in order. Obtain one only through
    :func:`parse_stream`; a non-conformant stream cannot be represented."""

    stream_version: str
    records: tuple[StreamOpen | StreamSample | StreamClose, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-compatible document, with no omitted field and no conversion."""
        return {"stream_version": self.stream_version, "records": [r.to_dict() for r in self.records]}


class StreamContractError(ContractError):
    """A stream document is not conformant. ``result`` holds the full :class:`StreamResult`; ``violations`` holds
    the same entries as (path, code, message) violations, sample violations under ``records[i].sample``."""

    def __init__(self, result: StreamResult, violations: tuple[Violation, ...] | None = None) -> None:
        self.result = result
        super().__init__(violations if violations is not None else _violations_of(result))


class UnsupportedStreamVersion(StreamContractError):
    """``stream_version`` is a string this SDK release does not support (code ``STREAM_UNSUPPORTED_VERSION``)."""


def _violations_of(result: StreamResult) -> tuple[Violation, ...]:
    out = [Violation(path=d.path, code=d.code, message=d.message) for d in result.stream]
    for v in result.samples:
        sub = "" if v.path in ("", "$") else "." + v.path
        out.append(Violation(path="records[%d].sample%s" % (v.position, sub), code=v.code, message=v.message))
    return tuple(out)


def parse_stream(doc: object) -> Stream:
    """Check ``doc`` and build a :class:`Stream`, or raise.

    An unsupported ``stream_version`` string raises :class:`UnsupportedStreamVersion` at once with the upstream code
    ``STREAM_UNSUPPORTED_VERSION``. Any other defect raises :class:`StreamContractError`. Nothing partial is returned.
    """
    result = check_stream(doc)
    for d in result.stream:
        if d.code == "STREAM_UNSUPPORTED_VERSION":
            raise UnsupportedStreamVersion(result, (Violation(path=d.path, code=d.code, message=d.message),))
    if not result.conformant:
        raise StreamContractError(result)
    assert isinstance(doc, dict)
    records: list[StreamOpen | StreamSample | StreamClose] = []
    for rec in doc["records"]:
        if rec["record"] == "open":
            records.append(StreamOpen(rec["index"], rec["stream_id"], rec["sensor_id"], rec["kind"], rec["clock"],
                                      rec.get("first_sequence")))
        elif rec["record"] == "sample":
            records.append(StreamSample(rec["index"], parse_sample(rec["sample"])))
        else:
            records.append(StreamClose(rec["index"], rec.get("last_sequence")))
    return Stream(stream_version=doc["stream_version"], records=tuple(records))
