#!/usr/bin/env python3
"""make oracle-fetch: check out the pinned kritva-sense oracle into .cache/kritva-sense. Standard library only.

    python3 scripts/oracle_fetch.py

Needs network access to github.com (a read-only clone) and git. The commit is read from the vendored PROVENANCE.json,
so the oracle always matches the pinned contract. kritva-sense is a TEST-ONLY oracle: the SDK never depends on it.
Exit 0 ready, 1 failure.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROV = ROOT / "src" / "kritva_sdk" / "_schemas" / "sense" / "PROVENANCE.json"
DEST = ROOT / ".cache" / "kritva-sense"


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def main():
    entry = json.loads(PROV.read_text(encoding="utf-8"))["files"][0]
    repo, commit = f"https://github.com/{entry['upstream_repo']}", entry["commit"]
    if not DEST.is_dir():
        DEST.parent.mkdir(parents=True, exist_ok=True)
        r = git("clone", "--quiet", repo, str(DEST))
        if r.returncode != 0:
            print(f"oracle-fetch: clone failed: {r.stderr.strip()}")
            return 1
    git("fetch", "--quiet", "--tags", "origin", cwd=DEST)
    r = git("checkout", "--quiet", "--detach", commit, cwd=DEST)
    if r.returncode != 0:
        print(f"oracle-fetch: cannot check out {commit}: {r.stderr.strip()}")
        return 1
    head = git("rev-parse", "HEAD", cwd=DEST).stdout.strip()
    if head != commit:
        print(f"oracle-fetch: HEAD {head} is not the pinned commit {commit}")
        return 1
    print(f"oracle-fetch: {DEST} at {commit} ({entry['tag']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
