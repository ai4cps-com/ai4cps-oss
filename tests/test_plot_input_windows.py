import pandas as pd
import pytest

from ai4cps.dash import plotting, theme


def windows():
    return [dict(kind='ad', start='2018-01-14T09:59:50Z', end='2018-01-14T10:00:00Z',
                 groups=['First'], label='AD input (10 s)'),
            dict(kind='dx', start='2018-01-14T09:58:21Z', end='2018-01-14T10:00:00Z', label='DX input (100 samples)'),
            dict(kind='reconfiguration', start='2018-01-14T10:00:00Z', end='2018-01-14T10:00:00Z',
                 label='Reconfiguration (current sample)')]


def test_bands_use_shared_semantic_colors_and_respect_group_scope_and_subplot_domains():
    figure = plotting.score_subplots(['First', 'Second'], {}, input_windows=windows())
    assert len(figure.layout.shapes) == 5
    assert not any(shape.showlegend for shape in figure.layout.shapes)
    labels = [item for item in figure.layout.annotations if (item.name or '').startswith('input-window:')]
    assert len(labels) == 5
    for item in labels:
        style = theme.PROCESSING_WINDOWS[item.name.split(':')[1]]
        assert item.font.color == style.get('label_color', style['color'])
        assert item.y == 1 and item.yanchor == 'bottom' and item.yshift == 3
        shape = next(shape for shape in figure.layout.shapes
                     if shape.name == item.text and shape.xref == item.xref)
        assert item.x == shape.x0 + (shape.x1 - shape.x0) / 2
    assert {shape.layer for shape in figure.layout.shapes} == {'below'}
    ad = next(shape for shape in figure.layout.shapes if shape.name.startswith('AD'))
    assert ad.type == 'rect' and ad.xref == 'x' and ad.yref == 'y domain'
    assert all(shape.line.width == 0 for shape in figure.layout.shapes if shape.type == 'rect')
    assert theme.PROCESSING_WINDOWS['ad']['color'] == theme.SEMANTIC['negative']
    dx = [shape for shape in figure.layout.shapes if shape.name.startswith('DX')]
    assert {shape.yref for shape in dx} == {'y domain', 'y2 domain'}
    rcfg = [shape for shape in figure.layout.shapes if shape.name.startswith('Reconfiguration')]
    assert all(shape.type == 'line' and shape.x0 == shape.x1 for shape in rcfg)
    assert all(shape.line.width > 0 for shape in rcfg)


def test_windows_are_clipped_to_the_viewport_without_changing_axes():
    time_range = tuple(pd.to_datetime(['2018-01-14T09:59:00Z', '2018-01-14T10:00:00Z'], utc=True))
    figure = plotting.score_subplots(['First'], {}, input_windows=windows(), time_range=time_range)
    dx = next(shape for shape in figure.layout.shapes if shape.name.startswith('DX'))
    assert dx.x0 == time_range[0] and dx.x1 == time_range[1]
    assert tuple(figure.layout.xaxis.range) == time_range
    outside = plotting.score_subplots(['First'], {}, input_windows=windows(),
        time_range=tuple(pd.to_datetime(['2018-01-14T11:00Z', '2018-01-14T12:00Z'], utc=True)))
    assert not outside.layout.shapes


def test_telemetry_windows_span_both_rows_and_keep_threshold_and_alarm_shapes():
    times = pd.date_range('2018-01-14T09:58Z', periods=3, freq='min')
    scores = pd.DataFrame({'time': times, 'values': [1., 2., 3.]})
    data = pd.DataFrame({'sensor': [10., 20., 30.]}, index=times)
    figure = plotting.score_signal_subplots('First', scores, data, threshold=1.5,
        input_windows=windows(), intervals=[(times[0], times[1])])
    bands = [shape for shape in figure.layout.shapes if (shape.legendgroup or '').startswith('input-window:')]
    assert len(bands) == 6
    assert not any(shape.showlegend for shape in bands)
    labels = [item for item in figure.layout.annotations if (item.name or '').startswith('input-window:')]
    assert len(labels) == 6
    assert {item.yref for item in labels} == {'y domain', 'y2 domain'}
    assert any(shape.name == 'Threshold' for shape in figure.layout.shapes)
    assert len(figure.layout.shapes) == 9


@pytest.mark.parametrize('groups', [[], ['First']])
def test_no_window_argument_preserves_existing_plots(groups):
    assert not plotting.score_subplots(groups, {}).layout.shapes
