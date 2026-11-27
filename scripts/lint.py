#!/usr/bin/env python3
"""lint: static checks for the repository's Python files (make lint). Standard library only.

    python3 scripts/lint.py [PATH ...]      default: src scripts tests (tests/data is skipped)

Rules (a line may opt out of L002 with a trailing `# noqa`):
  L001 syntax error            L002 unused import            L003 wildcard import
  L004 bare except             L005 mutable default argument  L006 tab or trailing whitespace
  L007 missing final newline   L008 print() in the library   L009 forbidden runtime import in the library
Exit 0 clean, 1 findings, 2 usage error. The library (src/) must stay standard-library only with no network, ROS 2,
simulator, hardware or kritva-sense dependency (KOS-SDK-003 AC-006, AC-007, AC-008).
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IN_LIBRARY = {"requests", "urllib3", "httpx", "aiohttp", "socket", "http", "urllib", "ssl", "jsonschema",
                        "kritva_sense", "rclpy", "ament_index_python", "pybullet", "mujoco", "serial"}


def python_files(paths):
    for base in paths:
        p = Path(base)
        files = [p] if p.is_file() else sorted(p.rglob("*.py"))
        for f in files:
            rel = f.resolve().relative_to(ROOT).parts
            if rel[:2] == ("tests", "data") or "__pycache__" in rel or "build" in rel[:1]:
                continue
            yield f


def check_file(path, root=ROOT):
    rel = path.resolve().relative_to(root)
    text = path.read_text(encoding="utf-8")
    out = []
    in_library = rel.parts[:1] == ("src",)
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        if "\t" in line or line != line.rstrip():
            out.append((i, "L006", "tab or trailing whitespace"))
    if text and not text.endswith("\n"):
        out.append((len(lines), "L007", "missing final newline"))
    try:
        tree = ast.parse(text, filename=str(rel))
    except SyntaxError as exc:
        return [(exc.lineno or 1, "L001", f"syntax error: {exc.msg}")] + out
    imported = {}
    used = set()
    exported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                name = (a.asname or a.name).split(".")[0]
                imported.setdefault(name, node.lineno)
                if in_library and a.name.split(".")[0] in FORBIDDEN_IN_LIBRARY:
                    out.append((node.lineno, "L009", f"forbidden import in the library: {a.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            if in_library and (node.module or "").split(".")[0] in FORBIDDEN_IN_LIBRARY:
                out.append((node.lineno, "L009", f"forbidden import in the library: {node.module}"))
            for a in node.names:
                if a.name == "*":
                    out.append((node.lineno, "L003", f"wildcard import from {node.module}"))
                else:
                    imported.setdefault(a.asname or a.name, node.lineno)
        elif isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            pass
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            out.append((node.lineno, "L004", "bare except"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for d in list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    out.append((d.lineno, "L005", "mutable default argument"))
        elif isinstance(node, ast.Call) and in_library and isinstance(node.func, ast.Name) and node.func.id == "print":
            out.append((node.lineno, "L008", "print() in the library"))
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                    exported |= {e.value for e in node.value.elts if isinstance(e, ast.Constant)}
    # names used in string annotations or attribute chains rooted at a Name are covered by ast.Name above
    for name, lineno in sorted(imported.items(), key=lambda kv: kv[1]):
        if name not in used and name not in exported and "# noqa" not in lines[lineno - 1]:
            out.append((lineno, "L002", f"unused import {name}"))
    return out


def main(argv):
    paths = argv or ["src", "scripts", "tests"]
    for p in paths:
        if not Path(p).exists():
            print(f"lint: no such path {p}", file=sys.stderr)
            return 2
    findings = 0
    count = 0
    for f in python_files(paths):
        count += 1
        for lineno, code, msg in check_file(f):
            findings += 1
            print(f"{f.resolve().relative_to(ROOT)}:{lineno}: {code} {msg}")
    if count == 0:
        print("lint: no Python files found (this is not a pass)")
        return 1
    print(f"lint: {count} files, {findings} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
