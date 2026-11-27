#!/usr/bin/env python3
"""Regression gate (make test-regression): compares the SDK's observable behaviour with golden data. Stdlib only.

    python3 scripts/regression_gate.py            compare; exit 0 only if every case REG-nn passes
    python3 scripts/regression_gate.py --write    rewrite the golden data (only after a change was decided)

The cases are listed in tests/regression/REGRESSION_INVENTORY.md. A case that fails, is missing from the run, has no
golden data, or a run with zero cases is a failure, never a pass. Changing a golden file means changing a public
interface or a guaranteed behaviour: that needs a MAJOR version once 1.0 is released, a changelog entry and an
approved decision (kritva-program ACCEPTANCE_STANDARD section 3). Exit 0 pass, 1 failure, 2 usage error.
"""
import hashlib
import importlib
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
GOLDEN = ROOT / "tests" / "regression" / "golden"
DATA = ROOT / "tests" / "data" / "sense"
VENDOR = ROOT / "src" / "kritva_sdk" / "_schemas" / "sense"
MODULES = ("kritva_sdk", "kritva_sdk.errors", "kritva_sdk.compat", "kritva_sdk.config", "kritva_sdk.sense")


def _sig(obj):
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None


def reg01_public_api():
    api = {}
    for name in MODULES:
        mod = importlib.import_module(name)
        entry = {"__all__": sorted(getattr(mod, "__all__", []))}
        members = {}
        for n in entry["__all__"]:
            obj = getattr(mod, n, None)
            if inspect.isclass(obj):
                members[n] = {"kind": "class", "signature": _sig(obj),
                              "bases": [b.__name__ for b in obj.__mro__[1:-1]],
                              "methods": sorted(m for m in vars(obj) if not m.startswith("_") and callable(getattr(obj, m)))}
            elif callable(obj):
                members[n] = {"kind": "function", "signature": _sig(obj)}
            else:
                members[n] = {"kind": "value", "type": type(obj).__name__}
        entry["members"] = members
        api[name] = entry
    return api


def reg02_supported_contracts():
    from kritva_sdk import supported_contracts
    return {k: list(v) for k, v in supported_contracts().items()}


def reg03_contract_constants():
    from kritva_sdk import sense
    return {"version": sense.SENSE_CONTRACT_VERSION, "error_codes": list(sense.ERROR_CODES), "frames": list(sense.FRAMES),
            "clocks": list(sense.CLOCKS), "timestamp_unit": sense.TIMESTAMP_UNIT,
            "validity_states": list(sense.VALIDITY_STATES), "kinds": {k: dict(v) for k, v in sense.KINDS.items()}}


def reg04_fixture_violations():
    from kritva_sdk.sense import validate_sample
    out = {}
    for group in ("valid", "invalid"):
        for p in sorted((DATA / group).glob("*.json")):
            sample = json.loads(p.read_text(encoding="utf-8"))["sample"]
            out[f"{group}/{p.name}"] = [list(v.as_tuple()) for v in validate_sample(sample)]
    return out


def reg05_error_behaviour():
    from kritva_sdk.errors import ContractError, UnsupportedContractVersion
    from kritva_sdk.sense import parse_sample
    base = json.loads((DATA / "valid" / "range_valid.json").read_text(encoding="utf-8"))["sample"]
    out = {}
    multi = dict(base, frame_id="map", sequence=-1, extra=1)
    try:
        parse_sample(multi)
    except ContractError as exc:
        out["multiple"] = {"class": type(exc).__name__, "code": exc.code, "path": exc.path,
                           "violations": [list(v.as_tuple()) for v in exc.violations], "text": str(exc)}
    early = dict(base, contract_version="9.9.9", frame_id="map")
    try:
        parse_sample(early)
    except UnsupportedContractVersion as exc:
        out["unsupported_version_is_early"] = {"class": type(exc).__name__, "violations": [list(v.as_tuple()) for v in exc.violations]}
    return out


def reg06_config():
    import dataclasses
    from kritva_sdk import SdkConfig
    from kritva_sdk.errors import ContractError
    out = {"fields": [[f.name, str(f.type), f.default] for f in dataclasses.fields(SdkConfig)],
           "default": SdkConfig().sense_contract_version, "frozen": SdkConfig.__dataclass_params__.frozen}
    for label, value in (("unsupported", "0.2.0"), ("wrong_type", 1)):
        try:
            SdkConfig(sense_contract_version=value)
        except ContractError as exc:
            out[label] = [type(exc).__name__, exc.code, exc.path]
    return out


def reg07_vendored_and_version():
    from kritva_sdk import __version__
    prov = json.loads((VENDOR / "PROVENANCE.json").read_text(encoding="utf-8"))
    return {"version": __version__,
            "vendored": {e["file"]: [hashlib.sha256((VENDOR / e["file"]).read_bytes()).hexdigest(), e["tag"], e["commit"]]
                         for e in prov["files"]}}


CASES = {
    "REG-01": ("public_api.json", reg01_public_api),
    "REG-02": ("supported_contracts.json", reg02_supported_contracts),
    "REG-03": ("contract_constants.json", reg03_contract_constants),
    "REG-04": ("fixture_violations.json", reg04_fixture_violations),
    "REG-05": ("error_behaviour.json", reg05_error_behaviour),
    "REG-06": ("config.json", reg06_config),
    "REG-07": ("vendored_and_version.json", reg07_vendored_and_version),
}


def dumps(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main(argv):
    if argv not in ([], ["--write"]):
        print(__doc__)
        return 2
    write = bool(argv)
    failed = 0
    ran = 0
    for cid, (fname, fn) in sorted(CASES.items()):
        current = dumps(fn())
        path = GOLDEN / fname
        if write:
            GOLDEN.mkdir(parents=True, exist_ok=True)
            path.write_text(current, encoding="utf-8")
            print(f"{cid} WRITTEN {fname}")
            ran += 1
            continue
        if not path.is_file():
            print(f"{cid} FAIL no golden data {fname}")
            failed += 1
            continue
        ran += 1
        if path.read_text(encoding="utf-8") != current:
            print(f"{cid} FAIL {fname} differs from the current behaviour (run with --write only if the change was decided)")
            failed += 1
        else:
            print(f"{cid} PASS {fname}")
    if write:
        return 0
    inventory = (ROOT / "tests" / "regression" / "REGRESSION_INVENTORY.md").read_text(encoding="utf-8")
    missing = [c for c in CASES if c not in inventory]
    if missing:
        print(f"FAIL cases not listed in the inventory: {', '.join(missing)}")
        failed += 1
    if ran == 0:
        print("FAIL zero cases ran (this is not a pass)")
        return 1
    print(f"regression gate: {ran} cases, {failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
