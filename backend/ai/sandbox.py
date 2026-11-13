# backend/ai/sandbox.py
"""Exécution de tests Python dans un conteneur Docker jetable (pas de réseau, mémoire/CPU/PIDs limités, FS en lecture seule).

SANDBOX_MODE=docker pour activer (défaut : off). Nécessite le binaire `docker` et l'accès au démon.
ATTENTION : si l'API tourne elle-même dans Docker, ne monte PAS /var/run/docker.sock (équivaut à root sur l'hôte) ;
préfère un runner séparé (gVisor/Firecracker) ou lance l'API hors conteneur quand tu actives ce mode.
"""
import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

MODE = os.getenv("SANDBOX_MODE", "off").lower()
TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "10"))
IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.11-slim")

RUNNER = r'''
import contextlib, json, sys, traceback, types

pytest = types.ModuleType("pytest")
@contextlib.contextmanager
def _raises(exc, **kw):
    try:
        yield
    except exc:
        return
    raise AssertionError("DID NOT RAISE")
class _Approx:
    def __init__(self, v, rel=1e-6, abs=1e-12): self.v, self.rel, self.abs = v, rel, abs
    def __eq__(self, o): return abs(o - self.v) <= max(self.rel * abs(self.v), self.abs)
class _Mark:
    def __getattr__(self, name): return lambda *a, **k: (lambda f: f)
pytest.raises, pytest.approx, pytest.mark = _raises, _Approx, _Mark()
sys.modules["pytest"] = pytest

ns = {"__name__": "sandboxed"}
res = {"passed": 0, "failed": 0, "failures": []}
try:
    exec(compile(open("/work/code.py").read(), "code.py", "exec"), ns)
except BaseException:
    print(json.dumps({"passed": 0, "failed": 1, "failures": [traceback.format_exc()[-600:]], "load_error": True}))
    sys.exit(0)
for name, fn in list(ns.items()):
    if name.startswith("test_") and callable(fn):
        try:
            fn(); res["passed"] += 1
        except BaseException:
            res["failed"] += 1; res["failures"].append(name + ": " + traceback.format_exc()[-400:])
print(json.dumps(res))
'''


def sandbox_available() -> bool:
    return MODE == "docker" and shutil.which("docker") is not None


def run_python_tests(source: str) -> dict:
    """Exécute `source` (code + fonctions test_*) et renvoie {passed, failed, failures, ...}."""
    if not sandbox_available():
        return {"status": "skipped", "detail": "Sandbox disabled (set SANDBOX_MODE=docker)"}

    name = f"sbx-{uuid.uuid4().hex[:12]}"
    with tempfile.TemporaryDirectory() as tmp:
        os.chmod(tmp, 0o755)
        (Path(tmp) / "code.py").write_text(source, encoding="utf-8")
        (Path(tmp) / "runner.py").write_text(RUNNER, encoding="utf-8")
        for f in ("code.py", "runner.py"):
            os.chmod(Path(tmp) / f, 0o644)
        cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "0.5",
               "--pids-limit", "64", "--read-only", "--tmpfs", "/tmp", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges", "--user", "65534:65534",
               "-v", f"{tmp}:/work:ro", IMAGE, "python", "-I", "/work/runner.py"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT + 15)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            return {"status": "failed", "passed": 0, "failed": 1, "failures": [f"Timeout after {TIMEOUT}s"]}
        except OSError as exc:
            return {"status": "skipped", "detail": f"docker error: {exc}"}

    last = (proc.stdout.strip().splitlines() or [""])[-1]
    try:
        res = json.loads(last)
    except json.JSONDecodeError:
        return {"status": "failed", "passed": 0, "failed": 1, "failures": [(proc.stderr or proc.stdout)[-500:]]}
    res["status"] = "passed" if res.get("failed", 1) == 0 and res.get("passed", 0) > 0 else "failed"
    return res
