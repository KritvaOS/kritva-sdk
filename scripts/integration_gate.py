#!/usr/bin/env python3
"""Integration gate (make test-integration): scenarios that cross real boundaries of the SDK. Standard library only.

    python3 scripts/integration_gate.py [--full]

INT-01 fresh isolated interpreter imports every module with the network disabled and loads no forbidden module
INT-02 wire path: every vendored valid sample, stream and frame graph fixture goes JSON text -> parse -> to_dict -> JSON text unchanged
INT-03 negative path: every invalid sample, stream and frame graph fixture is rejected with its documented codes, and no secret reaches error text
INT-04 provenance: the drift checker passes on the repository and fails on a tampered copy (separate process)
INT-05 oracle: kritva_sdk.sense, .stream and .frame_graph equal the pinned kritva-sense validator, checker, reference implementation, generator and harness (needs the oracle)
INT-06 packaging: hash-pinned wheel and sdist build, clean-venv install, import, resources (needs network or wheelhouse)
INT-07 schema subset: the SDK never accepts a sample, stream or frame graph the vendored JSON Schema rejects (needs jsonschema)

INT-01..04 always run. INT-05..07 run with --full (CI) and are SKIPPED otherwise. A skipped, failed or missing scenario
is never a pass: exit 0 only when every scenario passed, 1 on a failure, 4 when the run is INCOMPLETE (a skip).
The oracle is a kritva-sense checkout at the pinned commit named by KRITVA_SENSE_ORACLE, or .cache/kritva-sense
(make oracle-fetch). kritva-sense and jsonschema are test-only; the SDK never depends on them.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data" / "sense"
STREAM_DATA = ROOT / "tests" / "data" / "stream"
FRAME_DATA = ROOT / "tests" / "data" / "frame_graph"
VENDOR = ROOT / "src" / "kritva_sdk" / "_schemas" / "sense"
FORBIDDEN = ("rclpy", "ament_index_python", "requests", "urllib3", "httpx", "aiohttp", "jsonschema", "kritva_sense")
SECRET = "s3cr3t-token-0123456789"


class Skip(Exception):
    pass


def run(cmd, **kw):
    env = dict(os.environ, **kw.pop("env", {}))
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env, check=False, **kw)


def fixtures(group):
    return [(p.name, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((DATA / group).glob("*.json"))]


def stream_fixtures(group):
    return [(p.name, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((STREAM_DATA / group).glob("*.json"))]


def frame_fixtures(group):
    return [(p.name, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((FRAME_DATA / group).glob("*.json"))]


def int01():
    code = (
        f"import socket, sys; sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "def _no(*a, **k): raise RuntimeError('network disabled')\n"
        "socket.socket = _no; socket.create_connection = _no; socket.getaddrinfo = _no\n"
        "import kritva_sdk, kritva_sdk.errors, kritva_sdk.compat, kritva_sdk.config, kritva_sdk.sense\n"
        "import kritva_sdk.stream, kritva_sdk.frame_graph\n"
        f"bad = [m for m in {FORBIDDEN!r} if m in sys.modules]\n"
        "print('FORBIDDEN=' + ','.join(bad))\n")
    r = run([sys.executable, "-I", "-c", code])
    assert r.returncode == 0, f"import failed: {r.stderr.strip()[:300]}"
    assert r.stdout.strip() == "FORBIDDEN=", r.stdout.strip()
    return "all modules import offline; no forbidden module loaded"


def int02():
    sys.path.insert(0, str(ROOT / "src"))
    from kritva_sdk.sense import parse_sample
    n = 0
    for name, doc in fixtures("valid"):
        text = json.dumps(doc["sample"], sort_keys=True)
        out = json.dumps(parse_sample(json.loads(text)).to_dict(), sort_keys=True, allow_nan=False)
        assert out == text, f"{name}: wire round trip changed the sample"
        n += 1
    assert n >= 7
    from kritva_sdk.frame_graph import parse_frame_graph
    from kritva_sdk.stream import parse_stream
    s = 0
    for name, doc in stream_fixtures("valid"):
        text = json.dumps(doc, sort_keys=True)
        out = json.dumps(parse_stream(json.loads(text)).to_dict(), sort_keys=True, allow_nan=False)
        assert out == text, f"{name}: wire round trip changed the stream"
        s += 1
    g = 0
    for name, doc in frame_fixtures("valid"):
        text = json.dumps(doc["graph"], sort_keys=True)
        out = json.dumps(parse_frame_graph(json.loads(text)).to_dict(), sort_keys=True, allow_nan=False)
        assert out == text, f"{name}: wire round trip changed the frame graph"
        g += 1
    assert s >= 10 and g >= 8
    return f"{n} sample, {s} stream and {g} frame graph valid fixtures round-trip unchanged"


def int03():
    sys.path.insert(0, str(ROOT / "src"))
    from kritva_sdk.errors import ContractError
    from kritva_sdk.sense import parse_sample
    old = os.environ.get("KRITVA_TOKEN")
    os.environ["KRITVA_TOKEN"] = SECRET
    try:
        n = 0
        for name, doc in fixtures("invalid"):
            try:
                parse_sample(doc["sample"])
            except ContractError as exc:
                codes = {v.code for v in exc.violations}
                if "UNSUPPORTED_CONTRACT_VERSION" not in doc["expected_codes"]:
                    assert codes == set(doc["expected_codes"]), f"{name}: {sorted(codes)}"
                assert SECRET not in str(exc) and SECRET not in repr(exc), f"{name}: secret in error text"
                n += 1
            else:
                raise AssertionError(f"{name}: not rejected")
        from kritva_sdk.frame_graph import parse_frame_graph
        from kritva_sdk.stream import parse_stream
        expected = json.loads((STREAM_DATA / "expected.json").read_text(encoding="utf-8"))
        s = 0
        for name, doc in stream_fixtures("invalid"):
            want = {c for part in expected[name[:-5]].values() for _, c in part}
            try:
                parse_stream(doc)
            except ContractError as exc:
                codes = {v.code for v in exc.violations}
                if "STREAM_UNSUPPORTED_VERSION" not in want:
                    assert codes == want, f"stream {name}: {sorted(codes)} != {sorted(want)}"
                assert SECRET not in str(exc) and SECRET not in repr(exc), f"{name}: secret in error text"
                s += 1
            else:
                raise AssertionError(f"stream {name}: not rejected")
        g = 0
        for name, doc in frame_fixtures("invalid"):
            try:
                parse_frame_graph(doc["graph"])
            except ContractError as exc:
                codes = {v.code for v in exc.violations}
                if "FG_UNSUPPORTED_VERSION" not in doc["expected_codes"]:
                    assert codes == set(doc["expected_codes"]), f"frame graph {name}: {sorted(codes)}"
                assert SECRET not in str(exc) and SECRET not in repr(exc), f"{name}: secret in error text"
                g += 1
            else:
                raise AssertionError(f"frame graph {name}: not rejected")
    finally:
        if old is None:
            del os.environ["KRITVA_TOKEN"]
        else:
            os.environ["KRITVA_TOKEN"] = old
    return (f"{n} sample, {s} stream and {g} frame graph invalid fixtures rejected with documented codes; "
            "no secret in error text")


def int04():
    ok = run([sys.executable, "scripts/check_schema_drift.py"])
    assert ok.returncode == 0, ok.stdout + ok.stderr
    for source, victim in ((VENDOR, "SENSE_CONTRACT.md"), (VENDOR, "STREAM_CONTRACT.md"),
                           (VENDOR, "frame-transform.schema.json"), (STREAM_DATA, "expected.json"),
                           (FRAME_DATA, "valid/single_edge.json")):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "v"
            shutil.copytree(source, copy)
            target = copy / victim
            target.write_bytes(target.read_bytes() + b"\n")
            bad = run([sys.executable, "scripts/check_schema_drift.py", "--vendor-dir", str(copy)])
            assert bad.returncode == 1 and "DRIFT" in bad.stdout, (victim, bad.stdout)
    return "drift check passes on the repository and detects a tampered copy of each vendored kind"


def oracle_dir():
    for cand in (os.environ.get("KRITVA_SENSE_ORACLE", ""), str(ROOT / ".cache" / "kritva-sense")):
        if cand and Path(cand).is_dir():
            return cand
    return None


def int05():
    d = oracle_dir()
    if d is None:
        raise Skip("no kritva-sense oracle (set KRITVA_SENSE_ORACLE or run make oracle-fetch)")
    r = run([sys.executable, "-m", "unittest", "discover", "-s", "tests/conformance"],
            env={"KRITVA_SENSE_ORACLE": d, "KRITVA_REQUIRE_ORACLE": "1"})
    assert r.returncode == 0, (r.stdout + r.stderr)[-600:]
    assert "skipped" not in r.stderr, "oracle tests were skipped"
    return "pinned kritva-sense oracle parity passed (sample, stream, frame graph: fixtures, generator, harness, mutations)"


def int06():
    wheelhouse = os.environ.get("KRITVA_WHEELHOUSE")
    probe = subprocess.run([sys.executable, "-c", "import urllib.request as u; u.urlopen('https://pypi.org/simple/pip/', timeout=10)"],
                           capture_output=True, check=False)
    if not wheelhouse and probe.returncode != 0:
        raise Skip("no network access to PyPI and no KRITVA_WHEELHOUSE")
    r = run([sys.executable, "-m", "unittest", "discover", "-s", "tests/packaging"], env={"KRITVA_PACKAGING_TESTS": "1"})
    assert r.returncode == 0, (r.stdout + r.stderr)[-800:]
    assert "skipped" not in r.stderr, "packaging tests were skipped"
    return "wheel and sdist build reproducibly, install in a clean venv, import and expose vendored resources"


def int07():
    try:
        import jsonschema
    except ImportError:
        raise Skip("jsonschema is not installed (test-only dependency)")
    sys.path.insert(0, str(ROOT / "src"))
    from kritva_sdk.sense import validate_sample
    schema = json.loads((VENDOR / "sense-sample.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    samples = [d["sample"] for g in ("valid", "invalid") for _, d in fixtures(g)]
    n = 0
    for s in samples:
        sdk_ok = not validate_sample(s)
        schema_ok = validator.is_valid(s)
        # the schema is a structural subset: whatever the SDK accepts, the schema must accept
        assert not (sdk_ok and not schema_ok), f"SDK accepts what the schema rejects: {s!r}"
        n += 1
    from kritva_sdk.frame_graph import validate_graph
    from kritva_sdk.stream import check_stream
    from referencing import Registry, Resource
    sample_schema = json.loads((VENDOR / "sense-sample.schema.json").read_text(encoding="utf-8"))
    registry = Registry().with_resource(uri=sample_schema["$id"], resource=Resource.from_contents(sample_schema))
    sdoc = jsonschema.Draft202012Validator(json.loads((VENDOR / "stream.schema.json").read_text(encoding="utf-8")),
                                           registry=registry)
    fdoc = jsonschema.Draft202012Validator(json.loads((VENDOR / "frame-transform.schema.json").read_text(encoding="utf-8")))
    m = 0
    for g in ("valid", "invalid"):
        for _, d in stream_fixtures(g):
            assert not (check_stream(d).conformant and not sdoc.is_valid(d)), f"SDK accepts a stream the schema rejects: {d!r}"
            m += 1
        for _, d in frame_fixtures(g):
            assert not (not validate_graph(d["graph"]) and not fdoc.is_valid(d["graph"])), \
                f"SDK accepts a frame graph the schema rejects: {d['graph']!r}"
            m += 1
    return f"{n} sample fixtures and {m} stream and frame graph fixtures: the SDK never accepts what the vendored JSON Schema rejects"


SCENARIOS = (("INT-01", int01, False), ("INT-02", int02, False), ("INT-03", int03, False), ("INT-04", int04, False),
             ("INT-05", int05, True), ("INT-06", int06, True), ("INT-07", int07, True))


def main(argv):
    if argv not in ([], ["--full"]):
        print(__doc__)
        return 2
    full = bool(argv)
    results = []
    for sid, fn, needs_full in SCENARIOS:
        if needs_full and not full:
            results.append((sid, "SKIP", "runs with --full"))
            continue
        try:
            results.append((sid, "PASS", fn()))
        except Skip as exc:
            results.append((sid, "SKIP", str(exc)))
        except AssertionError as exc:
            results.append((sid, "FAIL", str(exc)))
        except Exception as exc:  # a crash is a failure, never a skip
            results.append((sid, "FAIL", f"{type(exc).__name__}: {exc}"))
    for sid, status, detail in results:
        print(f"{sid} {status} {detail}")
    failed = [r for r in results if r[1] == "FAIL"]
    skipped = [r for r in results if r[1] == "SKIP"]
    print(f"integration gate: {len(results)} scenarios, {len(failed)} failed, {len(skipped)} skipped")
    if failed:
        return 1
    if skipped:
        print("INCOMPLETE: a skipped scenario is not a pass (exit 4)")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
