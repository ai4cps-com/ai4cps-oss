from urllib.parse import unquote

import pytest

from ai4cps.backend import results
from ai4cps.backend.features import Feature
from ai4cps.dash import dashboard as dashboard_module
from ai4cps.dash.dashboard import Dash4CPS
from ai4cps.dash.routing_utils import ROUTE_PREFIX


class DataFetching(Feature):
    pass


class Pipeline(Feature):
    pass


@pytest.mark.parametrize('initial_date,expected', [('2018-01-14', '2018-01-14'), (None, '2026-11-17')])
@pytest.mark.parametrize('path', ['/', ROUTE_PREFIX.rstrip('/'), ROUTE_PREFIX])
def test_root_redirect_uses_the_initial_date_and_a_visible_feature(
        monkeypatch, tmp_path, initial_date, expected, path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(results, 'DEFAULT_RESULTS_DIR', tmp_path / 'Analysis')
    monkeypatch.setattr(dashboard_module, 'get_today', lambda: '2026-11-17')
    dashboard = Dash4CPS(initial_date=initial_date, users=['Background'])
    dashboard.add_system('Plant', {'Background': [DataFetching], 'Live Data Access': [Pipeline]})
    dashboard._initialize_server()
    client = dashboard.app.server.test_client()
    response = client.get(path)
    assert response.status_code == 302
    assert unquote(response.headers['Location']) == (
        f'{ROUTE_PREFIX}Plant/Live Data Access/Pipeline/{expected}/{expected}')
    explicit = client.get(f'{ROUTE_PREFIX}Plant/Live%20Data%20Access/Pipeline/2023-05-06/2023-05-06')
    assert explicit.status_code == 200
    assert 'Location' not in explicit.headers
