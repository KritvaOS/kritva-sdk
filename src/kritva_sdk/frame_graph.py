"""Typed Sense frame graph 0.1.0 models, deterministic validation and transform resolution. Standard library only.

The normative source is the vendored, pinned prose contract ``kritva_sdk/_schemas/sense/FRAME_GRAPH_CONTRACT.md``
(KOS-SENSE-FRAME-GRAPH-001, program decision D-085) and, as a structural subset only, ``frame-transform.schema.json``.
This module is a hand-written implementation of that contract. It does not import or depend on kritva-sense or
jsonschema; equivalence with the pinned reference implementation, including the arithmetic, is proven by tests that
use it as an oracle (KOS-SDK-005).

Convention (contract section 5), stated here because every result depends on it:

* Right-handed coordinates. A transform record is the pose of the ``child`` frame expressed in the ``parent`` frame:
  a point in child coordinates ``p_child`` has parent coordinates ``p_parent = R(q) * p_child + t``.
* ``translation`` is ``{x, y, z}`` in metres (``translation_unit`` is always ``m``).
* ``rotation`` is a unit quaternion ``{w, x, y, z}``, Hamilton convention, ``R(q)`` the active rotation; it must be
  of unit length within 1e-9 and is never normalized silently. ``q`` and ``-q`` are both accepted on input.
* ``resolve(graph, source, target)`` returns the transform that maps coordinates in ``source`` to coordinates in
  ``target``. The result is canonical: translation in metres, unit quaternion whose first non-zero component (order
  ``w, x, y, z``, magnitudes below 1e-12 counting as zero) is positive, and no negative zero.

Rules (contract section 6): no repeated ``(parent, child)`` pair, at most one parent per frame, no cycle. Any
violation makes the whole graph non-conformant, and a non-conformant graph never resolves. An unknown frame or an
unconnected pair is an error: no identity or default transform is ever invented. The identity is returned only for
a frame of the graph resolved to itself.

Upstream codes (``FG_`` namespace) are preserved verbatim; the argument checks that the contract defines for
``resolve`` (``FG_INVALID_FRAME_ID``, ``FG_MALFORMED``, ``FG_FRAME_NOT_IN_GRAPH``, ``FG_NO_PATH``) are contract
diagnostics. Misuse of this module outside the contract (a point that is not three finite numbers) raises
:class:`FrameGraphUsageError`, which is not a contract diagnostic. Arithmetic is IEEE 754 double precision; no
accuracy claim is made beyond the tests (absolute tolerance 1e-9 for translations up to 1e3 m).

Validation says nothing about whether a frame, mounting transform or calibration is physically correct. Tested on
synthetic data only; no transport, no time synchronisation and no sensor is involved.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from kritva_sdk.errors import ContractError, SdkError, Violation

__all__ = [
    "FRAME_GRAPH_CONTRACT_VERSION", "FG_ERROR_CODES", "QUAT_TOLERANCE", "SIGN_EPSILON", "TRANSLATION_UNIT",
    "FRAME_ID_PATTERN", "validate_transform", "validate_graph", "resolve", "transform_point", "parse_frame_graph",
    "Translation", "Quaternion", "FrameTransform", "FrameGraph", "ResolvedTransform", "Resolution",
    "FrameGraphUsageError", "FrameGraphContractError", "UnsupportedFrameGraphVersion",
]

FRAME_GRAPH_CONTRACT_VERSION = "0.1.0"

# A unit quaternion is accepted when |norm - 1| <= QUAT_TOLERANCE. Nothing is normalized silently on input.
QUAT_TOLERANCE = 1e-9
# Below this magnitude a quaternion component counts as zero when the sign of a result is chosen.
SIGN_EPSILON = 1e-12

FG_ERROR_CODES: tuple[str, ...] = (
    "FG_MALFORMED", "FG_MISSING_FIELD", "FG_UNKNOWN_FIELD", "FG_UNSUPPORTED_VERSION", "FG_INVALID_FRAME_ID",
    "FG_SELF_LINK", "FG_NON_FINITE", "FG_INVALID_UNIT", "FG_NOT_UNIT_QUATERNION", "FG_DUPLICATE_EDGE",
    "FG_MULTIPLE_PARENTS", "FG_CYCLE", "FG_FRAME_NOT_IN_GRAPH", "FG_NO_PATH",
)

_TRANSFORM_FIELDS = ("parent", "child", "translation", "translation_unit", "rotation")
_TRANSLATION_FIELDS = ("x", "y", "z")
_ROTATION_FIELDS = ("w", "x", "y", "z")
TRANSLATION_UNIT = "m"
_FRAME_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
FRAME_ID_PATTERN = _FRAME_ID_RE.pattern

_Vec = tuple[float, float, float]
_Quat = tuple[float, float, float, float]
_Pose = tuple[_Vec, _Quat]
_IDENTITY: _Pose = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0))


class FrameGraphUsageError(SdkError, ValueError):
    """The caller misused the frame graph API outside the contract (not a contract diagnostic)."""


def _v(code: str, path: str, message: str) -> Violation:
    return Violation(path=path, code=code, message=message)


def _is_num(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _object_numbers(obj: object, fields: tuple[str, ...], path: str, out: list[Violation]) -> tuple[float, ...] | None:
    """Check that ``obj`` is an object holding exactly ``fields``, each a finite number. Return them or None."""
    if not isinstance(obj, dict):
        out.append(_v("FG_MALFORMED", path, "must be an object with %s" % ", ".join(fields)))
        return None
    ok = True
    for f in fields:
        if f not in obj:
            out.append(_v("FG_MISSING_FIELD", "%s.%s" % (path, f), "required component is absent"))
            ok = False
    for f in sorted(k for k in obj if k not in fields):
        out.append(_v("FG_UNKNOWN_FIELD", "%s.%s" % (path, f), "component is not defined by the contract"))
        ok = False
    vals: list[float] = []
    for f in fields:
        if f not in obj:
            continue
        v = obj[f]
        if not _is_num(v):
            out.append(_v("FG_MALFORMED", "%s.%s" % (path, f), "must be a number"))
            ok = False
        elif not math.isfinite(v):
            out.append(_v("FG_NON_FINITE", "%s.%s" % (path, f), "must be finite"))
            ok = False
        else:
            vals.append(float(v))
    return tuple(vals) if ok else None


def _frame_id(value: object, path: str, out: list[Violation]) -> bool:
    if not isinstance(value, str):
        out.append(_v("FG_MALFORMED", path, "frame id must be a string"))
        return False
    if not _FRAME_ID_RE.match(value):
        out.append(_v("FG_INVALID_FRAME_ID", path, "frame id must match %s" % _FRAME_ID_RE.pattern))
        return False
    return True


def validate_transform(record: object, path: str = "$") -> tuple[Violation, ...]:
    """Return the violations of one transform record in (path, code, message) order; ``()`` means conformant."""
    out: list[Violation] = []
    if not isinstance(record, dict):
        return (_v("FG_MALFORMED", path, "transform must be an object"),)
    for f in _TRANSFORM_FIELDS:
        if f not in record:
            out.append(_v("FG_MISSING_FIELD", "%s.%s" % (path, f), "required field is absent"))
    for f in sorted(k for k in record if k not in _TRANSFORM_FIELDS):
        out.append(_v("FG_UNKNOWN_FIELD", "%s.%s" % (path, f),
                      "field is not defined by contract %s" % FRAME_GRAPH_CONTRACT_VERSION))
    parent_ok = child_ok = False
    if "parent" in record:
        parent_ok = _frame_id(record["parent"], path + ".parent", out)
    if "child" in record:
        child_ok = _frame_id(record["child"], path + ".child", out)
    if parent_ok and child_ok and record["parent"] == record["child"]:
        out.append(_v("FG_SELF_LINK", path, "parent and child are the same frame"))
    if "translation" in record:
        _object_numbers(record["translation"], _TRANSLATION_FIELDS, path + ".translation", out)
    if "translation_unit" in record and record["translation_unit"] != TRANSLATION_UNIT:
        out.append(_v("FG_INVALID_UNIT", path + ".translation_unit", "must be %r" % TRANSLATION_UNIT))
    if "rotation" in record:
        q = _object_numbers(record["rotation"], _ROTATION_FIELDS, path + ".rotation", out)
        if q is not None and abs(math.hypot(*q) - 1.0) > QUAT_TOLERANCE:
            out.append(_v("FG_NOT_UNIT_QUATERNION", path + ".rotation", "norm must be 1 within %g" % QUAT_TOLERANCE))
    return tuple(sorted(out))


def _edges(doc: dict[str, Any]) -> list[tuple[int, str, str, dict[str, Any]]]:
    """The well-formed edges of a document, in order, as (index, parent, child, record)."""
    transforms = doc.get("transforms")
    if not isinstance(transforms, list):
        return []
    return [(i, rec["parent"], rec["child"], rec) for i, rec in enumerate(transforms) if not validate_transform(rec)]


def validate_graph(doc: object) -> tuple[Violation, ...]:
    """Return the violations of a frame graph document in (path, code, message) order; ``()`` means conformant."""
    out: list[Violation] = []
    if not isinstance(doc, dict):
        return (_v("FG_MALFORMED", "$", "frame graph must be an object"),)
    for f in ("contract_version", "transforms"):
        if f not in doc:
            out.append(_v("FG_MISSING_FIELD", f, "required field is absent"))
    for f in sorted(k for k in doc if k not in ("contract_version", "transforms")):
        out.append(_v("FG_UNKNOWN_FIELD", f, "field is not defined by contract %s" % FRAME_GRAPH_CONTRACT_VERSION))
    if "contract_version" in doc:
        ver = doc["contract_version"]
        if not isinstance(ver, str):
            out.append(_v("FG_MALFORMED", "contract_version", "must be a string"))
        elif ver != FRAME_GRAPH_CONTRACT_VERSION:
            out.append(_v("FG_UNSUPPORTED_VERSION", "contract_version",
                          "%r is not supported; supported: %s" % (ver, FRAME_GRAPH_CONTRACT_VERSION)))
    transforms = doc.get("transforms")
    if "transforms" in doc and not isinstance(transforms, list):
        out.append(_v("FG_MALFORMED", "transforms", "must be an array"))
        return tuple(sorted(out))
    for i, rec in enumerate(transforms or ()):
        out.extend(validate_transform(rec, "transforms[%d]" % i))

    seen: dict[tuple[str, str], int] = {}        # (parent, child) -> first index
    parent_of: dict[str, tuple[str, int]] = {}   # child -> (parent, first index)
    for i, parent, child, _ in _edges(doc):
        path = "transforms[%d]" % i
        if (parent, child) in seen:
            out.append(_v("FG_DUPLICATE_EDGE", path,
                          "%s -> %s is already defined at transforms[%d]" % (parent, child, seen[(parent, child)])))
            continue
        seen[(parent, child)] = i
        if child in parent_of:
            out.append(_v("FG_MULTIPLE_PARENTS", path,
                          "%s already has parent %s (transforms[%d]); a frame has at most one parent"
                          % (child, parent_of[child][0], parent_of[child][1])))
            continue
        parent_of[child] = (parent, i)
    out.extend(_cycles({c: p for c, (p, _) in parent_of.items()}))
    return tuple(sorted(out))


def _cycles(parent: dict[str, str]) -> list[Violation]:
    """One FG_CYCLE violation per cycle in the child -> parent map."""
    out: list[Violation] = []
    done: set[str] = set()
    reported: set[frozenset[str]] = set()
    for start in sorted(parent):
        if start in done:
            continue
        chain: list[str] = []
        cur = start
        while cur in parent and cur not in done and cur not in chain:
            chain.append(cur)
            cur = parent[cur]
        if cur in chain:
            ring = chain[chain.index(cur):]
            key = frozenset(ring)
            if key not in reported:
                reported.add(key)
                out.append(_v("FG_CYCLE", "transforms", "cycle among frames: %s" % ", ".join(sorted(ring))))
        done.update(chain)
    return out


# ---- pose arithmetic: a pose is (translation (x, y, z), unit quaternion (w, x, y, z)) --------------------------

def _qmul(a: _Quat, b: _Quat) -> _Quat:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def _qconj(q: _Quat) -> _Quat:
    return (q[0], -q[1], -q[2], -q[3])


def _rotate(q: _Quat, v: _Vec) -> _Vec:
    w, ux, uy, uz = q
    vx, vy, vz = v
    cx, cy, cz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx          # u x v
    dx, dy, dz = uy * cz - uz * cy, uz * cx - ux * cz, ux * cy - uy * cx          # u x (u x v)
    return (vx + 2.0 * (w * cx + dx), vy + 2.0 * (w * cy + dy), vz + 2.0 * (w * cz + dz))


def _compose(a: _Pose, b: _Pose) -> _Pose:
    """The pose a o b: apply b, then a. For parent-child poses, compose(T_p_c, T_c_x) = T_p_x."""
    rt = _rotate(a[1], b[0])
    return ((rt[0] + a[0][0], rt[1] + a[0][1], rt[2] + a[0][2]), _qmul(a[1], b[1]))


def _invert(a: _Pose) -> _Pose:
    qc = _qconj(a[1])
    t = _rotate(qc, a[0])
    return ((-t[0], -t[1], -t[2]), qc)


def _canonical_quaternion(q: _Quat) -> _Quat:
    n = math.hypot(*q)
    qs = [c / n for c in q]
    for c in qs:
        if abs(c) > SIGN_EPSILON:
            if c < 0:
                qs = [-k for k in qs]
            break
    return (qs[0] + 0.0, qs[1] + 0.0, qs[2] + 0.0, qs[3] + 0.0)   # + 0.0 turns -0.0 into 0.0


def _pose_of(rec: Mapping[str, Any]) -> _Pose:
    tr, rot = rec["translation"], rec["rotation"]
    return ((float(tr["x"]), float(tr["y"]), float(tr["z"])),
            (float(rot["w"]), float(rot["x"]), float(rot["y"]), float(rot["z"])))


# ---- typed models ----------------------------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Translation:
    """A position in metres, ``x``, ``y``, ``z`` finite numbers exactly as carried on the wire (no conversion)."""

    x: int | float
    y: int | float
    z: int | float

    def __post_init__(self) -> None:
        out: list[Violation] = []
        _object_numbers(self.to_dict(), _TRANSLATION_FIELDS, "translation", out)
        if out:
            raise ContractError(out)

    def to_dict(self) -> dict[str, Any]:
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass(frozen=True, slots=True)
class Quaternion:
    """A unit quaternion ``w, x, y, z`` (Hamilton), unit length within 1e-9, exactly as carried on the wire."""

    w: int | float
    x: int | float
    y: int | float
    z: int | float

    def __post_init__(self) -> None:
        out: list[Violation] = []
        q = _object_numbers(self.to_dict(), _ROTATION_FIELDS, "rotation", out)
        if q is not None and abs(math.hypot(*q) - 1.0) > QUAT_TOLERANCE:
            out.append(_v("FG_NOT_UNIT_QUATERNION", "rotation", "norm must be 1 within %g" % QUAT_TOLERANCE))
        if out:
            raise ContractError(out)

    def to_dict(self) -> dict[str, Any]:
        return {"w": self.w, "x": self.x, "y": self.y, "z": self.z}


@dataclass(frozen=True, slots=True)
class FrameTransform:
    """One transform record: the pose of ``child`` expressed in ``parent``. Construction validates."""

    parent: str
    child: str
    translation: Translation
    rotation: Quaternion
    translation_unit: str = TRANSLATION_UNIT

    def __post_init__(self) -> None:
        violations = validate_transform(self.to_dict())
        if violations:
            raise ContractError(violations)

    def to_dict(self) -> dict[str, Any]:
        tr = self.translation.to_dict() if isinstance(self.translation, Translation) else self.translation
        rot = self.rotation.to_dict() if isinstance(self.rotation, Quaternion) else self.rotation
        return {"parent": self.parent, "child": self.child, "translation": tr,
                "translation_unit": self.translation_unit, "rotation": rot}


@dataclass(frozen=True, slots=True)
class ResolvedTransform:
    """A resolved transform in canonical form: maps coordinates of the source frame to the target frame."""

    translation: tuple[float, float, float]
    rotation: tuple[float, float, float, float]      # (w, x, y, z), unit length, first non-zero component positive
    translation_unit: str = TRANSLATION_UNIT

    def to_dict(self) -> dict[str, Any]:
        """The upstream record: ``{translation: {x, y, z}, translation_unit, rotation: {w, x, y, z}}``."""
        return {"translation": dict(zip(_TRANSLATION_FIELDS, self.translation)),
                "translation_unit": self.translation_unit,
                "rotation": dict(zip(_ROTATION_FIELDS, self.rotation))}

    def apply(self, point: Sequence[int | float]) -> tuple[float, float, float]:
        """Return ``point`` (in the source frame) expressed in the target frame."""
        return transform_point(self, point)


@dataclass(frozen=True, slots=True)
class Resolution:
    """The result of :func:`resolve`: a transform or the reasons there is none, never both and never neither.

    ``transform`` is ``None`` exactly when ``violations`` is not empty, so a caller cannot obtain a partial or
    invalid transform from a graph that did not validate or a pair of frames that does not resolve.
    """

    transform: ResolvedTransform | None
    violations: tuple[Violation, ...] = ()

    def __post_init__(self) -> None:
        if (self.transform is None) == (not self.violations):
            raise ValueError("a Resolution has either a transform or violations")

    @property
    def ok(self) -> bool:
        return self.transform is not None

    def unwrap(self) -> ResolvedTransform:
        """Return the transform, or raise :class:`FrameGraphContractError` carrying the violations."""
        if self.transform is None:
            raise FrameGraphContractError(self.violations)
        return self.transform


@dataclass(frozen=True, slots=True)
class FrameGraph:
    """A conformant frame graph (a forest of poses). Construction validates; a non-conformant graph cannot be
    represented, so it can never be resolved."""

    transforms: tuple[FrameTransform, ...]
    contract_version: str = FRAME_GRAPH_CONTRACT_VERSION

    def __post_init__(self) -> None:
        violations = validate_graph(self.to_dict())
        if violations:
            raise ContractError(violations)
        object.__setattr__(self, "transforms", tuple(self.transforms))

    def to_dict(self) -> dict[str, Any]:
        return {"contract_version": self.contract_version,
                "transforms": [t.to_dict() if isinstance(t, FrameTransform) else t for t in self.transforms]}

    def frames(self) -> tuple[str, ...]:
        """The frame ids that appear in the graph, sorted."""
        return tuple(sorted({f for t in self.transforms for f in (t.parent, t.child)}))

    def resolve(self, source: object, target: object) -> Resolution:
        """Same as :func:`resolve` on this graph."""
        return resolve(self, source, target)


class FrameGraphContractError(ContractError):
    """A frame graph document, or a resolution request, is not conformant; ``violations`` lists every reason."""


class UnsupportedFrameGraphVersion(FrameGraphContractError):
    """``contract_version`` is a string this SDK release does not support (code ``FG_UNSUPPORTED_VERSION``)."""


def parse_frame_graph(doc: object) -> FrameGraph:
    """Validate ``doc`` and build a :class:`FrameGraph`, or raise.

    An unsupported ``contract_version`` string raises :class:`UnsupportedFrameGraphVersion` at once with the upstream
    code ``FG_UNSUPPORTED_VERSION``. Any other defect raises :class:`FrameGraphContractError` with every violation.
    """
    violations = validate_graph(doc)
    for v in violations:
        if v.code == "FG_UNSUPPORTED_VERSION":
            raise UnsupportedFrameGraphVersion((v,))
    if violations:
        raise FrameGraphContractError(violations)
    assert isinstance(doc, dict)
    return FrameGraph(
        transforms=tuple(
            FrameTransform(parent=r["parent"], child=r["child"],
                           translation=Translation(**r["translation"]), rotation=Quaternion(**r["rotation"]),
                           translation_unit=r["translation_unit"])
            for r in doc["transforms"]),
        contract_version=doc["contract_version"])


def resolve(graph: object, source: object, target: object) -> Resolution:
    """Resolve the transform that maps coordinates in frame ``source`` to coordinates in frame ``target``.

    ``graph`` is a document (dict) or a :class:`FrameGraph`. A graph that is not conformant resolves nothing and its
    violations are returned. ``source`` and ``target`` must be frame ids (``FG_INVALID_FRAME_ID``, ``FG_MALFORMED``)
    that appear in some record of the graph (``FG_FRAME_NOT_IN_GRAPH``); frames in different components have no path
    (``FG_NO_PATH``). The path goes up from both frames to their nearest common ancestor and the result is
    ``inverse(T_c_target) o T_c_source``; the reverse lookup is therefore the inverse transform.
    """
    doc = graph.to_dict() if isinstance(graph, FrameGraph) else graph
    graph_violations = validate_graph(doc)
    if graph_violations:
        return Resolution(None, graph_violations)
    assert isinstance(doc, dict)
    out: list[Violation] = []
    parent: dict[str, tuple[str, _Pose]] = {}
    frames: set[str] = set()
    for _, p, c, rec in _edges(doc):
        parent.setdefault(c, (p, _pose_of(rec)))   # validate_graph guarantees one parent per child
        frames.update((p, c))
    for name, label in ((source, "source"), (target, "target")):
        if not _frame_id(name, label, out):
            continue
        if name not in frames:
            out.append(_v("FG_FRAME_NOT_IN_GRAPH", label, "frame %r has no transform in this graph" % name))
    if out:
        return Resolution(None, tuple(sorted(out)))
    assert isinstance(source, str) and isinstance(target, str)

    def ascend(frame: str) -> list[tuple[str, _Pose]]:
        chain, acc, cur = [(frame, _IDENTITY)], _IDENTITY, frame
        while cur in parent:
            p, pose = parent[cur]
            acc = _compose(pose, acc)           # T_p_frame
            cur = p
            chain.append((cur, acc))
        return chain

    up_source, up_target = ascend(source), ascend(target)
    in_target = dict(up_target)
    for frame, t_common_source in up_source:    # nearest common ancestor first
        if frame in in_target:
            t, q = _compose(_invert(in_target[frame]), t_common_source)
            cq = _canonical_quaternion(q)
            return Resolution(ResolvedTransform((t[0] + 0.0, t[1] + 0.0, t[2] + 0.0), cq))
    return Resolution(None, (_v("FG_NO_PATH", "$", "frames %r and %r are not connected" % (source, target)),))


def transform_point(transform: object, point: Sequence[int | float]) -> tuple[float, float, float]:
    """Apply a resolved transform to ``point`` ``(x, y, z)`` and return the point in the target frame.

    ``transform`` is a :class:`ResolvedTransform`, a :class:`FrameTransform` or an upstream transform record (dict).
    A point that is not three finite numbers, or a transform of another type, raises :class:`FrameGraphUsageError`.
    """
    if isinstance(transform, ResolvedTransform):
        t, q = transform.translation, transform.rotation
    elif isinstance(transform, FrameTransform):
        t, q = _pose_of(transform.to_dict())
    elif isinstance(transform, dict) and not validate_transform({"parent": "a", "child": "b", **transform}):
        t, q = _pose_of(transform)
    else:
        raise FrameGraphUsageError("transform must be a ResolvedTransform, a FrameTransform or a transform record")
    if (isinstance(point, (str, bytes)) or not isinstance(point, Sequence) or len(point) != 3
            or not all(_is_num(c) and math.isfinite(c) for c in point)):
        raise FrameGraphUsageError("point must be three finite numbers (x, y, z)")
    r = _rotate(q, (float(point[0]), float(point[1]), float(point[2])))
    return (r[0] + t[0], r[1] + t[1], r[2] + t[2])
