"""The dashboard must start without the optional MLflow dependency."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class OptionalMLflowTests(unittest.TestCase):
    def test_dashboard_without_mlflow_or_torch(self):
        code = """
import importlib.abc
import sys
sys.path.insert(0, ROOT_PATH)
class WithoutTracking(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"mlflow", "torch"}:
            raise ModuleNotFoundError("Optional package blocked", name=fullname)
sys.meta_path.insert(0, WithoutTracking())
from ai4cps.backend.features import Feature
from ai4cps.dash.dashboard import Dash4CPS
from ai4cps.dash.layouts import machine_learning
from ai4cps.dash.routing_utils import ROUTE_PREFIX
class Example(Feature):
    def perform(self, start, end):
        return 1
    def layout(self, role, analysis, start, end):
        return "ready"
app = Dash4CPS()
app.add_system("Test", features=[Example])
app.register_celery_tasks()
app._initialize_server()
response = app.app.server.test_client().get(ROUTE_PREFIX)
assert response.status_code in (200, 302), response.status_code
assert "mlflow" not in sys.modules
assert "torch" not in sys.modules
try:
    machine_learning()
except ImportError as exc:
    assert "ai4cps[mlflow]" in str(exc)
else:
    raise AssertionError("Model selector must require MLflow")
""".replace("ROOT_PATH", repr(str(ROOT)))
        with tempfile.TemporaryDirectory() as workdir:
            result = subprocess.run(
                [sys.executable, "-B", "-c", code], cwd=workdir,
                text=True, capture_output=True, timeout=120,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == "__main__":
    unittest.main()
