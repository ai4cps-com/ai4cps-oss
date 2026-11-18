# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Nemanja Hranisavljevic

"""Consistent Plotly themes and renderer profiles for AI4CPS dashboards."""
from html import escape
from hashlib import sha256
from math import isfinite
from textwrap import wrap

import pandas as pd
from plotly import graph_objects as go
from plotly import io as pio
from plotly.subplots import make_subplots

from . import colors, theme
from .components import normalize_selection as selected_groups


SCORE_TRACES = (("values", "Score", theme.TEXT),)
DEFAULT_SCORE_SUBPLOT_HEIGHT = 130
SCORE_SUBPLOT_GAP = 20
SCORE_AXIS_TITLE_SIZE = 12


def _input_window_spacing(groups, windows):
    count = max((sum(window.get('groups') is None or group in window['groups']
                     for window in windows) for group in groups), default=0)
    return max(SCORE_SUBPLOT_GAP, 14 * count + 6)


def register_template(make_default=False):
    pio.templates["ai4cps"] = go.layout.Template(layout={
        "paper_bgcolor": theme.SURFACE, "plot_bgcolor": theme.SURFACE_SUBTLE,
        "font": {"family": theme.FONT, "color": theme.TEXT},
        "colorway": theme.CHART_COLORS,
        "xaxis": {"gridcolor": theme.PLOT_GRID, "linecolor": theme.PLOT_AXIS,
                  "zerolinecolor": theme.PLOT_GRID, "automargin": True},
        "yaxis": {"gridcolor": theme.PLOT_GRID, "linecolor": theme.PLOT_AXIS,
                  "zerolinecolor": theme.PLOT_GRID, "automargin": True},
    })
    if make_default:
        pio.templates.default = "ai4cps"


def apply_theme(figure, profile="default", rows=1):
    figure.update_layout(template="ai4cps", paper_bgcolor=theme.SURFACE,
                         plot_bgcolor=theme.SURFACE_SUBTLE,
                         font={"family": theme.FONT, "color": theme.TEXT}, colorway=theme.CHART_COLORS)
    if profile == "timeline":
        figure.update_layout(height=max(360, 30 * rows + 120),
                             margin={"l": 20, "r": 20, "t": 40, "b": 50}, legend={"orientation": "h", "y": 1.05})
    elif profile in ("controls", "forecasts"):
        figure.update_layout(height=rows * (115 if profile == "controls" else 230),
                             margin={"l": 55, "r": 25, "t": 90, "b": 45},
                             legend={"orientation": "h", "y": 1.06})
        figure.update_annotations(font_size=11)
        if profile == "controls":
            figure.update_yaxes(tickmode="array", tickvals=[0, 1], range=[-0.1, 1.1])
    elif profile == "scenario":
        figure.update_layout(height=max(760, min(1200, 680 + rows * 18)),
                             hovermode="closest", hoverlabel={"align": "left"},
                             legend={"orientation": "h", "y": -0.18},
                             margin={"b": 112, "l": 96, "r": 24, "t": 72})
    elif profile == "timeseries":
        figure.update_layout(height=500, legend={"title": "", "orientation": "h",
                             "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1})
    elif profile in ("simulation", "compact", "anomaly-overview", "anomaly-context"):
        height = {"simulation": 1200, "compact": 500,
                  "anomaly-overview": max(300, rows * 100),
                  "anomaly-context": max(320, rows * 200)}[profile]
        figure.update_layout(height=height, margin={"l": 10, "r": 10, "t": 10, "b": 10})
        if profile.startswith("anomaly-"):
            figure.update_layout(showlegend=False)
    elif profile == "histogram":
        figure.update_layout(margin={"l": 40, "r": 40, "t": 40, "b": 40}, showlegend=False)
    elif profile == "stateflow":
        figure.update_layout(margin={"b": 20, "t": 50})
    return figure


def score_signal_subplots(group, score_frame, telemetry, date=None, *, threshold=None,
                           subplot_height=DEFAULT_SCORE_SUBPLOT_HEIGHT, larger_is_anomalous=False, intervals=(), time_range=None,
                           input_windows=()):
    """One group's score and raw signals on UTC time axes and UTC calendar days."""
    if not group:
        return message_figure('Select an anomaly detection group to inspect its signals.')
    score = score_subplots([group], {group: score_frame}, date, subplot_height=subplot_height,
                          thresholds={group: threshold}, larger_is_anomalous=larger_is_anomalous, time_range=time_range)
    gap = _input_window_spacing([group], input_windows)
    plot_height = 3 * float(subplot_height) + gap
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[1, 2],
                           vertical_spacing=gap / plot_height)
    for trace in score.data:
        figure.add_trace(trace, row=1, col=1)
    if not score.data:
        # Plotly omits unused axes, which would also hide the missing-score
        # annotation for components that only have raw telemetry.
        figure.add_trace(go.Scattergl(x=[], y=[], showlegend=False, hoverinfo='skip'), row=1, col=1)
    for shape in score.layout.shapes:
        figure.add_shape(shape)
    for annotation in score.layout.annotations:
        figure.add_annotation(annotation)

    data = telemetry.copy() if isinstance(telemetry, pd.DataFrame) else pd.DataFrame()
    start = pd.Timestamp(str(date).split('T')[0]).tz_localize('UTC') if date else None
    end = start + pd.DateOffset(days=1) if start is not None else None
    plotted, unavailable = False, []
    if not data.empty:
        data.index = pd.to_datetime(data.index, utc=True, errors='coerce')
        data = data.loc[data.index.notna() & ~data.index.duplicated(keep='last')].sort_index()
        if start is not None:
            data = data.loc[(data.index >= start) & (data.index < end)]
        if time_range is not None:
            data = data.loc[(data.index >= time_range[0]) & (data.index <= time_range[1])]
    for index, column in enumerate(data.columns):
        values = pd.to_numeric(data[column], errors='coerce').replace([float('inf'), float('-inf')], float('nan'))
        if not values.notna().any():
            unavailable.append(str(column))
            continue
        color = theme.CHART_COLORS[index % len(theme.CHART_COLORS)]
        figure.add_trace(go.Scattergl(x=data.index, y=values, mode='lines+markers', name=str(column),
            legendgroup=f'signal:{column}', legendrank=10 + index, showlegend=True, connectgaps=False,
            line={'color': color}, marker={'color': color, 'size': 5, 'line': {'width': 0}},
            hovertemplate=f'<b>{escape(str(column))}</b><br>Time: %{{x}}<br>Value: %{{y:.2f}}<extra></extra>'), row=2, col=1)
        plotted = True
    if not plotted or unavailable:
        figure.add_annotation(
            text=(f'{len(unavailable)} signal(s) unavailable.' if plotted else
                  'No numeric telemetry available for this group on the selected date.'),
            hovertext='<br>'.join(escape(name) for name in unavailable),
            x=1 if plotted else .5, y=1 if plotted else .5, xref='x2 domain', yref='y2 domain',
            xanchor='right' if plotted else 'center', yanchor='top' if plotted else 'middle',
            showarrow=False, font={'color': theme.MUTED})
    for begin, finish in intervals:
        for row in (1, 2):
            figure.add_vrect(x0=begin, x1=finish, row=row, col=1, exclude_empty_subplots=False,
                             fillcolor=theme.SEMANTIC['negative'], opacity=.12, line_width=0, layer='below')
    margin = {'l': 70, 'r': 30, 't': gap, 'b': 160, 'autoexpand': False}
    figure.update_layout(template='ai4cps', font={'family': theme.FONT, 'color': theme.TEXT},
        height=plot_height + margin['t'] + margin['b'], margin=margin, hovermode='closest',
        legend={'orientation': 'h', 'yref': 'container', 'y': 0, 'yanchor': 'bottom', 'x': 0, 'xanchor': 'left', 'maxheight': 1},
        meta={'ai4cps_legend': {'plot_height': plot_height, 'minimum_bottom': margin['b'], 'axis_gap': 70}},
        uirevision=f'{date}:{group}:signals:{time_range}')
    figure.update_yaxes(title={**score.layout.yaxis.title.to_plotly_json(), 'text': 'Anomaly Score'}, row=1, col=1)
    figure.update_yaxes(title={'text': 'Signals', 'font': {'size': SCORE_AXIS_TITLE_SIZE}}, row=2, col=1)
    figure.update_yaxes(automargin='width', tickformat='.1f')
    figure.update_yaxes(tickformat='.2f', hoverformat='.2f', row=2, col=1)
    figure.update_xaxes(automargin='width', type='date')
    figure.update_xaxes(title_text='Time (UTC)', row=2, col=1)
    if time_range is not None:
        figure.update_xaxes(range=list(time_range), autorange=False)
    return add_input_windows(figure, input_windows, rows=[(1, group), (2, group)], time_range=time_range)


def add_input_windows(figure, windows, *, rows, time_range=None):
    """Render borderless bands with matching colored labels above each interval."""
    for window in windows:
        kind = window['kind']
        style = theme.PROCESSING_WINDOWS[kind]
        start, end = pd.to_datetime([window['start'], window['end']], utc=True)
        if pd.isna(start) or pd.isna(end) or end < start:
            continue
        if time_range is not None:
            if end < time_range[0] or start > time_range[1]:
                continue
            start, end = max(start, time_range[0]), min(end, time_range[1])
        label = window['label']
        for row, group in rows:
            if window.get('groups') is not None and group not in window['groups']:
                continue
            suffix = str(row) if row > 1 else ''
            figure.add_shape(type='line' if start == end else 'rect',
                x0=start, x1=end, y0=0, y1=1, xref=f'x{suffix}', yref=f'y{suffix} domain',
                layer='below', fillcolor=colors.hex_to_rgba(style['color'], style['opacity']),
                line={'color': colors.hex_to_rgba(style['color'], .85),
                      'width': style['width'] if start == end else 0, 'dash': style['dash']},
                name=label, legendgroup=f'input-window:{kind}', legendrank=100,
                showlegend=False)
            figure.add_annotation(
                text=escape(label), name=f'input-window:{kind}',
                x=start + (end - start) / 2, y=1, xref=f'x{suffix}', yref=f'y{suffix} domain',
                xanchor='right', yanchor='bottom', yshift=3,
                showarrow=False, font={'color': style.get('label_color', style['color']), 'size': 11})
    return figure


def line_style(role="measured", index=0, shape="linear"):
    color = theme.TEXT if role == "measured" else theme.CHART_COLORS[(index + 1) % len(theme.CHART_COLORS)]
    return {"color": color, "shape": shape}


def split_line():
    return {"line_width": 2, "line_dash": "dash", "line_color": theme.TEXT}


def event_marker():
    return {"color": colors.NEUTRAL[1], "line": {"color": colors.NEUTRAL[3], "width": 1},
            "size": 9, "symbol": "diamond"}


def categorical_palette(labels):
    """Keep categorical colors stable when a caller filters a complete catalog."""
    return {label: theme.CHART_COLORS[index % len(theme.CHART_COLORS)]
            for index, label in enumerate(labels)}


def label_palette(labels, roles=None):
    """Semantic labels plus stable categorical colors independent of filtering."""
    roles = roles or {}
    return {label: theme.SEMANTIC[roles[label.casefold()]] if label.casefold() in roles
            else theme.CHART_COLORS[int.from_bytes(sha256(label.encode("utf-8")).digest()[:4], "big")
                                    % len(theme.CHART_COLORS)]
            for label in labels}


def message_figure(message):
    figure = apply_theme(go.Figure())
    figure.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    figure.update_layout(height=520, margin={"b": 48, "l": 56, "r": 24, "t": 40})
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure


def subplot_grid(titles, columns=1, shared_xaxes=False):
    return make_subplots(rows=(len(titles) + columns - 1) // columns, cols=columns,
                         shared_xaxes=shared_xaxes, subplot_titles=titles, vertical_spacing=0.045)


def scenario_subplots(data_title):
    return make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.055,
                         row_heights=[0.26, 0.12, 0.62],
                         subplot_titles=["Scenario stateflow", "PalletCreator events", data_title])


def acceptance_bands(figure, lower, upper):
    """Shade valid operating ranges; callers supply only domain bounds."""
    for row, (minimum, maximum) in enumerate(zip(lower, upper), 1):
        figure.add_shape(type="rect", xref="paper", yref=f"y{row}",
                         x0=0, x1=1, y0=minimum, y1=maximum, line={"width": 0},
                         fillcolor=theme.SEMANTIC["positive"], opacity=0.1, layer="below")
    return figure


def threshold(figure, value, axis="y", row=1):
    shape = {"type": "line", "line": {"width": 3, "color": theme.SEMANTIC["negative"]},
             "opacity": 0.5, "layer": "above"}
    if axis == "x":
        shape.update(xref=f"x{row}", yref="paper", x0=value, x1=value, y0=0, y1=1)
    else:
        shape.update(xref="paper", yref=f"y{row}", x0=0, x1=1, y0=value, y1=value)
    figure.add_shape(**shape)
    return figure


def notice(figure, text, role="negative"):
    figure.add_annotation(text=text, x=0.5, y=0.5, xref="paper", yref="paper",
                          showarrow=False, font={"size": 14, "color": theme.SEMANTIC[role]})
    return figure


def movement_controls(figure, annotations, hide_label, show_label):
    figure.update_layout(updatemenus=[{
        "type": "buttons", "direction": "left", "buttons": [
            {"args": ["annotations", None], "label": hide_label, "method": "relayout"},
            {"args": ["annotations", annotations], "label": show_label, "method": "relayout"},
        ], "pad": {"r": 10, "t": 10}, "showactive": True,
        "x": 0.11, "xanchor": "left", "y": 1, "yanchor": "bottom",
    }])
    return apply_theme(figure, "stateflow")


register_template()


def score_subplots(groups, frames, date=None, *, subplot_height=DEFAULT_SCORE_SUBPLOT_HEIGHT, thresholds=None,
                   larger_is_anomalous=False, time_range=None, input_windows=()):
    """Render score groups on UTC calendar days with fixed gaps and configurable row heights."""
    subplot_height = float(subplot_height)
    if not isfinite(subplot_height) or subplot_height <= 0:
        raise ValueError("Subplot height must be a finite positive number of pixels.")
    groups = selected_groups(groups)
    thresholds = {str(group).casefold(): value for group, value in (thresholds or {}).items()}
    threshold_color = theme.SEMANTIC["negative"]
    rows = max(1, len(groups))
    gap = _input_window_spacing(groups, input_windows)
    plot_height = rows * subplot_height + (rows - 1) * gap
    margin = {"l": 70, "r": 30, "t": gap, "b": 110, "autoexpand": False}
    if not groups:
        figure = go.Figure()
        figure.add_annotation(text="Select anomaly detection groups to display their scores.",
                              x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
    else:
        figure = make_subplots(rows=len(groups), cols=1, shared_xaxes=True,
                               vertical_spacing=gap / plot_height if rows > 1 else 0)
        seen = set()
        normal_lines = []
        threshold_seen = False
        start = pd.Timestamp(str(date).split("T")[0]).tz_localize("UTC") if date else None
        end = start + pd.DateOffset(days=1) if start is not None else None
        for row, group in enumerate(groups, start=1):
            try:
                threshold = float(thresholds[group.casefold()])
                if not isfinite(threshold):
                    threshold = None
            except (KeyError, TypeError, ValueError):
                threshold = None
            frame = frames.get(group)
            plotted = False
            if isinstance(frame, pd.DataFrame) and "time" in frame:
                frame = frame.copy()
                frame["time"] = pd.to_datetime(frame["time"], utc=True, errors="coerce", format="mixed")
                frame = frame.dropna(subset=["time"]).drop_duplicates("time", keep="last").sort_values("time")
                times = frame["time"]
                mask = times.notna()
                if start is not None:
                    mask &= (times >= start) & (times < end)
                if time_range is not None:
                    mask &= (times >= time_range[0]) & (times <= time_range[1])
                for trace_index, (field, label, color) in enumerate(SCORE_TRACES):
                    if field not in frame:
                        continue
                    values = pd.to_numeric(frame[field], errors="coerce")
                    if not values.loc[mask].notna().any():
                        continue
                    anomalous = ((values.loc[mask].gt(threshold) if larger_is_anomalous else values.loc[mask].lt(threshold))
                                 if threshold is not None else None)
                    markers = ({"color": [threshold_color if flagged else color
                                           for flagged in anomalous],
                                "size": 6, "line": {"width": 0}} if threshold is not None else None)
                    has_anomalies = threshold is not None and anomalous.any()
                    line_has_legend = False
                    if has_anomalies:
                        normal = values.loc[mask].mask(anomalous)
                        if normal.notna().any():
                            line_has_legend = field not in seen
                            normal_lines.append((go.Scattergl(
                                x=times.loc[mask], y=normal, mode="lines", name=label,
                                legendgroup=field, legendrank=trace_index, showlegend=line_has_legend, connectgaps=False,
                                line={"color": color}, hoverinfo="skip",
                            ), row))
                    figure.add_trace(go.Scattergl(
                        x=times.loc[mask], y=values.loc[mask],
                        mode="markers" if has_anomalies else "lines+markers" if markers else "lines", name=label,
                        legendgroup=field, legendrank=trace_index,
                        showlegend=field not in seen and not line_has_legend, connectgaps=False,
                        line={"color": color}, marker=markers,
                    ), row=row, col=1)
                    seen.add(field)
                    plotted = True
            if threshold is not None:
                figure.add_hline(y=threshold, row=row, col=1, exclude_empty_subplots=False,
                                 line={"color": threshold_color, "dash": "dash", "width": 1.5},
                                 name="Threshold", legendgroup="threshold", showlegend=not threshold_seen)
                threshold_seen = True
            if not plotted:
                suffix = str(row) if row > 1 else ""
                figure.add_annotation(
                    text="No score data available for this group on the selected date.",
                    x=0.5, y=0.5, xref=f"x{suffix} domain", yref=f"y{suffix} domain", showarrow=False,
                )
            # Rotated titles run along the row's height, so wrap before they
            # extend into neighbouring subplots. Allow room above and below.
            title_width = max(1, int((subplot_height - 16) / SCORE_AXIS_TITLE_SIZE))
            title = "<br>".join(escape(line) for line in wrap(group, width=title_width,
                                                           break_on_hyphens=False))
            figure.update_yaxes(title={"text": title, "font": {"size": SCORE_AXIS_TITLE_SIZE}},
                                tickformat=".1f", row=row, col=1)
        for trace, row in normal_lines:
            figure.add_trace(trace, row=row, col=1)
        figure.update_xaxes(title_text="Time (UTC)", row=len(groups), col=1)
    # Keep each row's height exact while allowing wide tick labels more room.
    figure.update_xaxes(automargin="width", type="date")
    figure.update_yaxes(automargin="width")
    figure.update_layout(
        template="ai4cps", height=plot_height + margin["t"] + margin["b"],
        font={"family": theme.FONT, "color": theme.TEXT},
        margin=margin, hovermode="closest",
        legend={"title": "", "orientation": "h", "yanchor": "bottom", "yref": "container", "y": 0,
                "xanchor": "left", "x": 0, "maxheight": 1},
        meta={'ai4cps_legend': {'plot_height': plot_height, 'minimum_bottom': margin['b'], 'axis_gap': 70}},
        uirevision=f"{date}:{','.join(groups)}:{time_range}",
    )
    if time_range is not None:
        figure.update_xaxes(range=list(time_range), autorange=False)
    return add_input_windows(figure, input_windows, rows=list(enumerate(groups, start=1)), time_range=time_range)
