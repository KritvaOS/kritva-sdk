"""Packaging tests (KOS-SDK-002, AC-001..006). Builds the wheel and sdist in a hash-pinned environment, installs each
into a clean virtual environment, imports it, checks metadata, and checks that two builds are byte-identical.

Runs only when KRITVA_PACKAGING_TESTS=1 (CI sets it); outside CI it is skipped explicitly, and inside CI a skip is
a failure of the workflow's own check. Needs network access to PyPI for the pinned build tools, or a local wheelhouse
named by KRITVA_WHEELHOUSE. Prints one PACKAGING-EVIDENCE line per artifact for the release record.
"""
import hashlib
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
import venv
import zipfile
from email.parser import Parser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EPOCH = "1700000000"
ENABLED = os.environ.get("KRITVA_PACKAGING_TESTS") == "1"


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def make_venv(path):
    venv.EnvBuilder(with_pip=True, clear=True).create(path)
    return Path(path) / "bin" / "python"


def pip_args():
    wh = os.environ.get("KRITVA_WHEELHOUSE")
    return ["--no-index", "--find-links", wh] if wh else []


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@unittest.skipUnless(ENABLED, "set KRITVA_PACKAGING_TESTS=1 to run packaging tests")
class PackagingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        t = Path(cls.tmp.name)
        py = make_venv(t / "build-env")
        run([str(py), "-m", "pip", "install", "--require-hashes", "-r",
             str(ROOT / "release" / "build-requirements.txt"), *pip_args()])
        cls.builds = []
        for n in (1, 2):
            out = t / f"dist{n}"
            env = dict(os.environ, SOURCE_DATE_EPOCH=EPOCH)
            run([str(py), "-m", "build", "--no-isolation", "--outdir", str(out), str(ROOT)], env=env)
            sd = next(out.glob("*.tar.gz"))
            run([sys.executable, str(ROOT / "release" / "normalise_sdist.py"), str(sd)], env=env)
            cls.builds.append(out)
        cls.wheel = next(cls.builds[0].glob("*.whl"))
        cls.sdist = next(cls.builds[0].glob("*.tar.gz"))
        for a in (cls.wheel, cls.sdist):
            print(f"PACKAGING-EVIDENCE {a.name} sha256={sha256(a)}")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _install_and_import(self, artifact):
        py = make_venv(Path(self.tmp.name) / f"clean-{artifact.suffix.lstrip('.')}")
        run([str(py), "-m", "pip", "install", "--no-deps", str(artifact)])
        out = run([str(py), "-I", "-c",
                   "import sys, kritva_sdk; print(kritva_sdk.__version__);"
                   "print(any(m in sys.modules for m in ('rclpy','requests','httpx')))"]).stdout.split()
        self.assertEqual(out[1], "False")
        freeze = run([str(py), "-m", "pip", "freeze"]).stdout.split()
        self.assertEqual([f for f in freeze if f.startswith("kritva")][0].split("=")[0].replace("_", "-"), "kritva-sdk")
        return out[0]

    def test_wheel_installs_and_imports(self):
        self.assertRegex(self._install_and_import(self.wheel), r"^\d+\.\d+\.\d+")

    def test_sdist_installs_and_imports(self):
        # builds from the sdist inside the clean venv; needs the pinned setuptools reachable (index or wheelhouse)
        self.assertRegex(self._install_and_import(self.sdist), r"^\d+\.\d+\.\d+")

    def test_wheel_metadata_and_contents(self):
        with zipfile.ZipFile(self.wheel) as z:
            names = z.namelist()
            meta = Parser().parsestr(z.read(next(n for n in names if n.endswith("METADATA"))).decode())
        self.assertEqual(meta["Name"], "kritva-sdk")
        self.assertEqual(meta["Requires-Python"], ">=3.12")
        self.assertIsNone(meta["Requires-Dist"])
        self.assertIn("kritva_sdk/py.typed", names)
        self.assertFalse([n for n in names if n.startswith(("tests/", "planning/", "release/"))])

    VENDORED = ("sense-sample.schema.json", "SENSE_CONTRACT.md", "stream.schema.json", "STREAM_CONTRACT.md",
                "frame-transform.schema.json", "FRAME_GRAPH_CONTRACT.md", "PROVENANCE.json")

    def test_wheel_and_sdist_contain_vendored_contract_files(self):
        with zipfile.ZipFile(self.wheel) as z:
            wnames = set(z.namelist())
        with tarfile.open(self.sdist) as t:
            snames = set(t.getnames())
        for f in self.VENDORED:
            self.assertIn(f"kritva_sdk/_schemas/sense/{f}", wnames)
            self.assertTrue(any(n.endswith(f"src/kritva_sdk/_schemas/sense/{f}") for n in snames), f)

    def test_installed_wheel_reads_vendored_files_as_resources(self):
        py = make_venv(Path(self.tmp.name) / "clean-resources")
        run([str(py), "-m", "pip", "install", "--no-deps", str(self.wheel)])
        code = ("import hashlib, json; from importlib.resources import files; "
                "d = files('kritva_sdk') / '_schemas' / 'sense'; "
                "prov = json.loads((d / 'PROVENANCE.json').read_text(encoding='utf-8')); "
                "print(all(hashlib.sha256((d / e['file']).read_bytes()).hexdigest() == e['sha256'] for e in prov['files']))")
        self.assertEqual(run([str(py), "-I", "-c", code]).stdout.strip(), "True")

    def test_two_builds_are_byte_identical(self):
        for pattern in ("*.whl", "*.tar.gz"):
            a, b = (next(d.glob(pattern)) for d in self.builds)
            self.assertEqual(sha256(a), sha256(b), pattern)


if __name__ == "__main__":
    unittest.main()
