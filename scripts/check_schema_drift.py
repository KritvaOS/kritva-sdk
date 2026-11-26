"""Checks the vendored Sense contract files against their recorded provenance (KOS-SDK-003, AC-004). Stdlib only.

    python3 scripts/check_schema_drift.py                  offline: every vendored file matches its recorded SHA-256
    python3 scripts/check_schema_drift.py --upstream DIR   also: DIR is a kritva-sense checkout at exactly the recorded
                                                           commit and holds byte-identical files

Exit 0 when clean, 1 on drift or a provenance defect, 2 on a usage error. The offline check needs no network and no
upstream checkout; a hand edit of a vendored file fails it.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "src" / "kritva_sdk" / "_schemas" / "sense"
REQUIRED = ("file", "upstream_repo", "upstream_path", "contract", "contract_version", "tag", "commit", "sha256",
            "license", "approval_status", "decision_ref", "role")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load(vendor):
    return json.loads((vendor / "PROVENANCE.json").read_text(encoding="utf-8"))


def check_offline(vendor):
    problems = []
    try:
        prov = load(vendor)
    except (OSError, ValueError) as exc:
        return [f"PROVENANCE.json unreadable: {exc}"], None
    entries = prov.get("files")
    if not isinstance(entries, list) or not entries:
        return ["PROVENANCE.json has no files list"], None
    listed = set()
    for e in entries:
        name = e.get("file", "?")
        for key in REQUIRED:
            if not isinstance(e.get(key), str) or not e[key]:
                problems.append(f"{name}: provenance field {key!r} missing or empty")
        if isinstance(e.get("commit"), str) and not SHA40.match(e["commit"]):
            problems.append(f"{name}: commit is not a 40-hex SHA")
        if isinstance(e.get("sha256"), str) and not SHA64.match(e["sha256"]):
            problems.append(f"{name}: sha256 is not 64-hex")
        listed.add(name)
        path = vendor / name
        if not path.is_file():
            problems.append(f"{name}: vendored file missing")
        elif sha256(path.read_bytes()) != e.get("sha256"):
            problems.append(f"{name}: DRIFT, content does not match the recorded sha256")
    for p in sorted(vendor.iterdir()):
        if p.name != "PROVENANCE.json" and p.name not in listed and not p.name.startswith(("__", ".")):
            problems.append(f"{p.name}: vendored file has no provenance entry")
    if len({(e.get("commit"), e.get("tag")) for e in entries}) > 1:
        problems.append("files record different tags or commits")
    return problems, prov


def git(upstream, *args):
    return subprocess.run(["git", "-C", str(upstream), *args], capture_output=True, check=False)


def check_upstream(vendor, prov, upstream):
    problems = []
    head = git(upstream, "rev-parse", "HEAD")
    if head.returncode != 0:
        return [f"{upstream}: not a git checkout"]
    head_sha = head.stdout.decode().strip()
    for e in prov["files"]:
        name = e["file"]
        if head_sha != e["commit"]:
            problems.append(f"{name}: upstream HEAD {head_sha} is not the recorded commit {e['commit']}")
            continue
        blob = git(upstream, "show", f"{e['commit']}:{e['upstream_path']}")
        if blob.returncode != 0:
            problems.append(f"{name}: {e['upstream_path']} not found at the recorded commit")
        elif sha256(blob.stdout) != e["sha256"]:
            problems.append(f"{name}: DRIFT, upstream content at the recorded commit differs from the recorded sha256")
        elif (vendor / name).read_bytes() != blob.stdout:
            problems.append(f"{name}: DRIFT, vendored file differs from upstream at the recorded commit")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--upstream", metavar="DIR", help="kritva-sense checkout at the recorded commit")
    ap.add_argument("--vendor-dir", metavar="DIR", default=str(VENDOR), help=argparse.SUPPRESS)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    vendor = Path(args.vendor_dir)
    problems, prov = check_offline(vendor)
    if prov is not None and args.upstream:
        problems += check_upstream(vendor, prov, Path(args.upstream))
    for p in problems:
        print(f"schema-drift: {p}")
    if problems:
        return 1
    print("schema-drift: OK" + (" (offline + upstream)" if args.upstream else " (offline)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
