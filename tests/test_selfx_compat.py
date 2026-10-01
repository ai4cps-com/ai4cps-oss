"""Check legacy imports in fresh interpreters to cover both import orders."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize("first", ["selfx", "ai4cps"])
def test_legacy_namespace_shares_modules(first):
    subprocess.run(
        [sys.executable, "-c", f"""
import importlib
import sys

first = importlib.import_module({first!r})
assert 'ai4cps.dash.dashboard' not in sys.modules
other = importlib.import_module('ai4cps' if {first!r} == 'selfx' else 'selfx')
assert first is other

for suffix in ('version', 'backend', 'backend.features', 'dash', 'dash.dashboard', 'dash.routing_utils'):
    initial = importlib.import_module({first!r} + '.' + suffix)
    legacy = importlib.import_module('selfx.' + suffix)
    canonical = importlib.import_module('ai4cps.' + suffix)
    assert initial is legacy is canonical, suffix
    assert canonical.__name__ == 'ai4cps.' + suffix
    assert canonical.__spec__.name == canonical.__name__

from selfx.backend import features
from ai4cps.backend.features import Feature
from selfx.dash.dashboard import SelfXDash
from ai4cps.dash.dashboard import Dash4CPS
assert features.Feature is Feature
assert SelfXDash is Dash4CPS

try:
    importlib.import_module('selfx.dash.nonexistent_module')
except ModuleNotFoundError as exc:
    assert exc.name == 'selfx.dash.nonexistent_module'
else:
    raise AssertionError('Missing modules must fail to import')
"""],
        check=True,
        capture_output=True,
        text=True,
    )
