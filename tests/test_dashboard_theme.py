"""Check the shared theme contract across renderers and packaged assets."""
from pathlib import Path

import pytest
from plotly import graph_objects as go
import pandas as pd

from ai4cps.dash import colors, components, graph_styles, plotting, styles, theme
from ai4cps.dash.dashboard import Dash4CPS
from ai4cps.dash.routing_utils import ROUTE_PREFIX


@pytest.mark.parametrize("role,palette", [
    ("positive", colors.POSITIVE), ("negative", colors.NEGATIVE),
    ("error", colors.NEGATIVE), ("warning", colors.NEGATIVE),
    ("secondary", colors.NEUTRAL), ("info", colors.OTHER),
    ("diagnosis", colors.NEGATIVE),
    ("off", colors.NEGATIVE),
    ("unchanged", colors.NEUTRAL),
    ("reconfiguration", colors.POSITIVE),
])
def test_semantic_roles_use_ai4cps_palette_with_readable_foregrounds(role, palette):
    background = theme.SEMANTIC[role]
    assert background in palette
    foreground = theme.readable_text(background)

    def luminance(value):
        channels = [channel / 255 for channel in colors.hex_to_rgb(value)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + .055) / 1.055) ** 2.4
                  for channel in channels]
        return sum(channel * weight for channel, weight in zip(linear, (.2126, .7152, .0722)))

    high, low = sorted([luminance(background), luminance(foreground)], reverse=True)
    assert (high + .05) / (low + .05) >= 4.5
    css = theme.css_variables()
    assert f"--ai4cps-{role}: {background};" in css
    assert f"--ai4cps-on-{role}: {foreground};" in css


def test_dashboard_serves_theme_and_shared_controls_without_app_styles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dashboard = Dash4CPS()
    from dash import html

    dashboard.app.layout = html.Div("Shared theme")
    client = dashboard.app.server.test_client()
    prefix = ROUTE_PREFIX.rstrip("/")
    response = client.get(f"{prefix}/_ai4cps/theme.css")
    assert response.status_code == 200
    assert response.mimetype == "text/css"
    assert theme.SEMANTIC["positive"] in response.get_data(as_text=True)
    index = client.get(f"{prefix}/").get_data(as_text=True)
    for filename in ("theme_components.css", "theme_utilities.css", "selfx_style.css", "ai4cps_controls.js"):
        assert filename in index
        asset = client.get(f"{prefix}/assets/{filename}")
        assert asset.status_code == 200
    assert go.Figure().layout.template.layout.colorway == tuple(theme.CHART_COLORS)


def test_chart_graph_and_table_renderers_share_the_theme():
    figure = plotting.apply_theme(go.Figure(), "controls", rows=2)
    assert figure.layout.font.family == theme.FONT
    assert figure.layout.plot_bgcolor == theme.SURFACE_SUBTLE
    assert figure.layout.colorway == tuple(theme.CHART_COLORS)
    options = styles.table_styles(column_count=3, fixed=True)
    assert options["style_cell"]["color"] == theme.TEXT
    assert options["style_header"]["backgroundColor"] == theme.SURFACE
    sheet = graph_styles.material_flow_stylesheet(["Machine"])
    category = next(item["style"] for item in sheet if item["selector"] == ".component-type-Machine")
    assert category["color"] == theme.readable_text(category["background-color"])


def test_semantic_adapters_preserve_custom_roles_for_dbc_rendering():
    assert "text-bg-error" in components.badge("Fault", color="error").className.split()
    assert "progress-negative" in components.progress(value=40, color="negative").className.split()


@pytest.mark.parametrize("rows", [1, 2, 4, 31])
@pytest.mark.parametrize("height", [130, 200])
def test_score_subplot_height_and_gap_are_stable_across_group_counts(rows, height):
    figure = plotting.score_subplots([f"Group {index}" for index in range(rows)], {}, subplot_height=height)
    area = figure.layout.height - figure.layout.margin.t - figure.layout.margin.b
    axes = [figure.layout["yaxis" + (str(index) if index > 1 else "")] for index in range(1, rows + 1)]
    for axis in axes:
        assert area * (axis.domain[1] - axis.domain[0]) == pytest.approx(height)
    for upper, lower in zip(axes, axes[1:]):
        assert area * (upper.domain[0] - lower.domain[1]) == pytest.approx(20)


@pytest.mark.parametrize("height", [0, -1, float("inf"), float("nan")])
def test_score_subplots_reject_invalid_height(height):
    with pytest.raises(ValueError, match="Subplot height"):
        plotting.score_subplots(["Group"], {}, subplot_height=height)


def test_group_detail_uses_two_time_rows_without_histograms_and_respects_the_selected_day():
    times = pd.date_range('2018-01-13T23:00:00Z', periods=4, freq='h')
    frame = pd.DataFrame({'time': times, 'values': [1., 2., 3., 4.]})
    telemetry = pd.DataFrame({'Voltage': [10., 11., 12., 13.], 'Current': [2., 3., 4., 5.]}, index=times)
    figure = plotting.score_signal_subplots('CFA1', frame, telemetry, '2018-01-14', threshold=2.)
    assert all(trace.type == 'scattergl' for trace in figure.data)
    assert set(trace.yaxis for trace in figure.data) == {'y', 'y2'}
    assert figure.layout.xaxis.matches == 'x2'
    assert figure.layout.yaxis2.title.text == 'Signals'
    raw = next(trace for trace in figure.data if trace.name == 'Voltage')
    assert list(raw.y) == [11., 12., 13.]
    assert raw.mode == 'lines+markers'
    assert raw.marker.color == raw.line.color
    assert '%{y:.2f}' in raw.hovertemplate
    assert figure.layout.yaxis2.tickformat == '.2f'
    assert figure.layout.yaxis2.hoverformat == '.2f'
    score = next(trace for trace in figure.data if trace.name == 'Score')
    assert list(score.y) == [2., 3., 4.]
    assert figure.layout.xaxis2.title.text == 'Time (UTC)'
    assert figure.layout.shapes[0].y0 == 2.
    assert figure.layout.shapes[0].yref == 'y'
    area = figure.layout.height - figure.layout.margin.t - figure.layout.margin.b
    assert area * (figure.layout.yaxis.domain[1] - figure.layout.yaxis.domain[0]) == pytest.approx(130.)
    assert area * (figure.layout.yaxis2.domain[1] - figure.layout.yaxis2.domain[0]) == pytest.approx(260.)


def test_group_detail_marks_unavailable_signals_without_dropping_available_data():
    times = pd.date_range('2018-01-14T12:00Z', periods=3, freq='s')
    telemetry = pd.DataFrame({'Voltage': [1., 2., 3.], 'Missing': [None, None, None]}, index=times)
    figure = plotting.score_signal_subplots('CFA1', None, telemetry)
    assert any(trace.name == 'Voltage' for trace in figure.data)
    assert any(trace.yaxis == 'y' for trace in figure.data)
    assert figure.layout.yaxis.title.text == 'Anomaly Score'
    assert any(annotation.text == '1 signal(s) unavailable.' and annotation.hovertext == 'Missing'
               for annotation in figure.layout.annotations)


def test_score_subplots_use_orange_thresholds_and_mark_only_strictly_lower_points():
    times = pd.date_range('2018-01-14T10:00:00Z', periods=4, freq='s')
    first = pd.DataFrame({'time': times, 'values': [1., 2., 3., float('nan')],
                          'smooth': [2., 1., 4., float('nan')]})
    second = pd.DataFrame({'time': times, 'values': [-2., -1., 0., 1.]})
    figure = plotting.score_subplots(['First', 'Second'], {'First': first, 'Second': second},
                                    thresholds={'first': 2., 'second': -1.})
    orange = theme.SEMANTIC['negative']
    assert [shape.y0 for shape in figure.layout.shapes] == [2., -1.]
    assert [shape.y1 for shape in figure.layout.shapes] == [2., -1.]
    assert [shape.showlegend for shape in figure.layout.shapes] == [True, False]
    assert all(shape.line.color == orange for shape in figure.layout.shapes)
    assert list(figure.data[0].marker.color) == [orange, theme.TEXT, theme.TEXT, theme.TEXT]
    assert list(figure.data[1].marker.color) == [orange, theme.TEXT, theme.TEXT, theme.TEXT]
    assert all(trace.legendgroup != 'smooth' for trace in figure.data)
    assert len(first) == 4 and pd.isna(first['values'].iloc[-1])


def test_score_lines_break_at_anomalies_without_losing_the_orange_points():
    times = pd.date_range('2018-01-14T10:00:00Z', periods=4, freq='s')
    frame = pd.DataFrame({'time': times, 'values': [3., 1., 3., 4.]})
    figure = plotting.score_subplots(['Group'], {'Group': frame}, thresholds={'Group': 2.})
    points, line = figure.data
    assert points.mode == 'markers'
    assert list(points.y) == [3., 1., 3., 4.]
    assert points.marker.color[1] == theme.SEMANTIC['negative']
    assert line.mode == 'lines' and line.line.color == theme.TEXT
    assert pd.isna(line.y[1]) and list(line.y[2:]) == [3., 4.]
    assert line.connectgaps is False
    assert line.legendgroup == points.legendgroup
    assert sum(bool(trace.showlegend) for trace in figure.data) == 1


@pytest.mark.parametrize('threshold', [None, float('nan'), float('inf'), 'invalid'])
def test_missing_or_invalid_threshold_does_not_invent_a_line(threshold):
    frame = pd.DataFrame({'time': [pd.Timestamp('2018-01-14', tz='UTC')], 'values': [1.]})
    figure = plotting.score_subplots(['Group'], {'Group': frame}, thresholds={'Group': threshold})
    assert not figure.layout.shapes
    assert figure.data[0].mode == 'lines'


def test_shared_component_styles_cover_focus_selection_and_copy_layout():
    assets = Path(theme.__file__).with_name("assets")
    css = (assets / "theme_components.css").read_text(encoding="utf-8")
    for selector in (".small-inline-button", ".warning-selector", ".toggle-positive",
                     ".accordion-with-action", ".tooltip-content", ".schematic-row"):
        assert selector in css
    assert ":focus-visible" in css
    script = (assets / "ai4cps_controls.js").read_text(encoding="utf-8")
    assert "clipboard: function" in script and "alarm: async function" in script
    assert "field.style" not in script
