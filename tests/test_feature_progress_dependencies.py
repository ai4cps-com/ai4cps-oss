from types import SimpleNamespace

import pandas as pd
import pytest

from ai4cps.backend import perform, results
from ai4cps.dash.dashboard import Dash4CPS


DATE = '2018-01-14'
INTERVAL = '2018-01-14_00_00_00'
CHAIN = ['AD', 'DX', 'RCFG', 'Pipeline']


@pytest.fixture
def dashboard(monkeypatch, tmp_path):
    monkeypatch.setattr(results, 'DEFAULT_RESULTS_DIR', tmp_path / 'Analysis')
    app = Dash4CPS()
    app._feature_obj['System'] = {
        'AD': SimpleNamespace(required_features=()),
        'DX': SimpleNamespace(required_features=('AD',)),
        'RCFG': SimpleNamespace(required_features=('DX',)),
        'Pipeline': SimpleNamespace(required_features=('RCFG',)),
        'UnusedBackground': SimpleNamespace(required_features=()),
    }
    return app


def test_progress_includes_the_same_transitive_dependencies_as_the_scheduler(dashboard):
    registry = dashboard._feature_obj['System']
    assert perform.get_required_features('Pipeline', registry) == CHAIN
    for name in CHAIN:
        progress = dashboard.exist_requested_features('Pipeline', 'System', DATE, DATE)
        assert progress.columns.tolist() == [f'System#{stage}' for stage in CHAIN]
        assert progress.loc[INTERVAL, f'System#{name}'] == 0.
        results.store_result(pd.Timestamp(DATE), f'System#{name}', {'completed': True})
        updated = dashboard.exist_requested_features('Pipeline', 'System', DATE, DATE)
        assert updated.loc[INTERVAL, f'System#{name}'] == 1.
        pd.testing.assert_frame_equal(updated, perform.exist_requested_features(dashboard, 'Pipeline', 'System', DATE, DATE))
    assert updated.eq(1.).all().all()
    assert registry['Pipeline'].required_features == ('RCFG',)


def test_shared_nested_dependency_appears_only_once(dashboard):
    dashboard._feature_obj['System']['Pipeline'].required_features = ('AD', 'RCFG')
    progress = dashboard.exist_requested_features('Pipeline', 'System', DATE, DATE)
    assert progress.columns.tolist() == [f'System#{stage}' for stage in CHAIN]
