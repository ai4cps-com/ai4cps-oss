import pytest

from ai4cps.backend.features import Feature
from ai4cps.dash.dashboard import Dash4CPS
from ai4cps.dash.routing_utils import construct_url, deprecated_route_redirect


class Overview(Feature):
    def perform(self, start, end):
        return 1

    def layout(self, role, analysis, start, end):
        return "Overview"

    def icon(self):
        return "home"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # the server clears Analysis/Online in the working folder
    app = Dash4CPS()
    app.add_system("Tiny Plant", features=[Overview])
    app._initialize_server()
    return app.app.server.test_client()


def test_links_use_the_ai4cps_path():
    assert construct_url("Tiny Plant", "Default", "Overview", "2026-11-17", "2026-11-17") == \
        "/ai4cps/Tiny Plant/Default/Overview/2026-11-17/2026-11-17"


@pytest.mark.parametrize("old, new", [
    ("/selfx", "/ai4cps/"),
    ("/selfx/", "/ai4cps/"),
    ("/selfx/Tiny%20Plant/Default/Overview/2026-11-17/2026-11-17?story=1&tour=1",
     "/ai4cps/Tiny%20Plant/Default/Overview/2026-11-17/2026-11-17?story=1&tour=1"),
    ("http://demo.example.com/selfx/_dash-layout", "/ai4cps/_dash-layout"),
])
def test_deprecated_links_lead_to_the_same_ai4cps_link(old, new):
    assert deprecated_route_redirect(old) == new


@pytest.mark.parametrize("url", ["/ai4cps/", "/ai4cps/Tiny%20Plant/Default/Overview/2026-11-17/2026-11-17",
                                 "/selfxyz/", "/other/selfx/"])
def test_other_links_are_not_redirected(url):
    assert deprecated_route_redirect(url) is None


def test_old_links_redirect_once_and_keep_their_method(client):
    page = "Tiny%20Plant/Default/Overview/2026-11-17/2026-11-17"
    response = client.get(f"/selfx/{page}?story=1")
    assert (response.status_code, response.headers["Location"]) == (308, f"/ai4cps/{page}?story=1")
    assert client.get(response.headers["Location"]).status_code == 200  # no loop
    assert client.get(f"/ai4cps/{page}").status_code == 200
    # A tab opened before the move still sends Dash requests to the old path.
    response = client.post("/selfx/_dash-update-component", json={})
    assert (response.status_code, response.headers["Location"]) == (308, "/ai4cps/_dash-update-component")
    root = client.get("/selfx")
    assert (root.status_code, root.headers["Location"]) == (308, "/ai4cps/")
    assert client.get("/ai4cps/").headers["Location"].startswith("/ai4cps/Tiny%20Plant/")
