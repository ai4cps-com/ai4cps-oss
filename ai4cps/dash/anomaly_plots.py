# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Nemanja Hranisavljevic

"""Reusable anomaly-score plots, thresholds and resampling for dashboards."""
import numpy as np
import pandas as pd
from dash import Patch, no_update
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from . import colors as selfx_colors, theme

AI4CPS_PAPER_BG = theme.SURFACE
AI4CPS_PLOT_BG = theme.SURFACE_SUBTLE
AI4CPS_TEXT = theme.TEXT
AI4CPS_MUTED_TEXT = theme.SIDEBAR
AI4CPS_GRID = theme.PLOT_GRID
AI4CPS_AXIS = theme.PLOT_AXIS
SELFX_FONT = theme.FONT
AI4CPS_THRESHOLD = theme.SEMANTIC['negative']
AI4CPS_HIGHLIGHT = selfx_colors.hex_to_rgba(theme.SEMANTIC['negative'], 0.22)
SELFX_SCORE_COLOR = theme.TEXT
SELFX_COLORWAY = theme.CHART_COLORS
AD_TIMESERIES_TOTAL_VERTICAL_GAP = 0.07
AD_COMPONENT_VERTICAL_SPACING = 0.06
AD_MAX_DISPLAYED_SAMPLES = 2000

def resample_figure(fig):
    from plotly_resampler import FigureResampler
    # Convert after threshold styling so marker colors/sizes are resampled with y.
    # Bar traces retain the histogram counts computed from the full dataset.
    return FigureResampler(
        fig, default_n_shown_samples=AD_MAX_DISPLAYED_SAMPLES,
        resampled_trace_prefix_suffix=("", ""), show_mean_aggregation_size=False,
        convert_traces_kwargs={"limit_to_views": True},
    )


def selected_time_range(relayout_data):
    """Read the shared time axes (odd columns); ignore histogram count axes."""
    for key, value in relayout_data.items():
        axis, _, prop = key.partition(".")
        if not axis.startswith("xaxis"):
            continue
        suffix = axis[5:]
        if suffix and not suffix.isdigit():
            continue
        if int(suffix or 1) % 2 == 0:
            continue
        if prop == "autorange" and value:
            return (None, None)
        if prop == "range" and isinstance(value, (list, tuple)) and len(value) == 2:
            return tuple(value)
        if prop == "range[0]" and f"{axis}.range[1]" in relayout_data:
            return value, relayout_data[f"{axis}.range[1]"]
    return None


def resample_selected_range(result, component, bounds, variables=()):
    """Patch only time traces, passing the selected samples to the resampler."""
    scores = result.get("score")
    if not isinstance(scores, pd.DataFrame) or scores.empty:
        return no_update
    if component != "All" and component not in scores.columns:
        return no_update

    def select(series):
        start, end = bounds
        # Plotly sends timezone-free date strings even for timezone-aware data.
        def timestamp(value):
            if value is None:
                return None
            value = pd.Timestamp(value)
            if series.index.tz is not None and value.tzinfo is None:
                value = value.tz_localize(series.index.tz)
            elif series.index.tz is None and value.tzinfo is not None:
                value = value.tz_convert("UTC").tz_localize(None)
            return value
        return series.loc[timestamp(start):timestamp(end)]

    thresholds = result.get("thresholds") or {}
    series = [(scores[column], thresholds.get(column), True) for column in scores.columns]
    if component != "All":
        series = [(scores[component], thresholds.get(component), True)]
        data = result.get("data")
        if isinstance(data, pd.DataFrame) and not data.empty and all(v in data.columns for v in variables):
            series.extend((data[v], None, False) for v in variables)

    fig = go.Figure()
    for source, threshold, is_score in series:
        plotted = select(source)
        marker = {}
        if is_score:
            below = np.asarray(plotted, dtype=float) < threshold if threshold is not None else np.zeros(len(plotted), dtype=bool)
            marker["size"] = 4 if component == "All" else np.where(below, 4, 0)
            if threshold is not None:
                marker["color"] = np.where(below, AI4CPS_THRESHOLD, SELFX_SCORE_COLOR)
        fig.add_trace(go.Scattergl(x=plotted.index, y=plotted, marker=marker))
    sampled = resample_figure(fig)
    patch = Patch()
    for index, trace in enumerate(sampled.data):
        # Every time trace is followed by its histogram in the displayed figure.
        patch["data"][2 * index]["x"] = trace.x
        patch["data"][2 * index]["y"] = trace.y
        marker = trace.marker.to_plotly_json()
        if marker:
            patch["data"][2 * index]["marker"] = marker
    return patch


def anomaly_context_series(series, intervals, context_seconds):
    """Keep full anomaly windows, inserting NaN separators across omitted regions."""
    seconds = float(context_seconds)
    if not np.isfinite(seconds) or seconds < 0:
        raise ValueError("Anomaly context must be a finite, nonnegative duration")
    if series.empty or not intervals:
        return series.iloc[:0]
    context = pd.Timedelta(seconds=seconds)
    starts = series.index.searchsorted([start - context for start, _ in intervals], side="left")
    stops = series.index.searchsorted([end + context for _, end in intervals], side="right")
    coverage = np.zeros(len(series) + 1, dtype=int)
    np.add.at(coverage, starts, 1)
    np.add.at(coverage, stops, -1)
    keep = np.cumsum(coverage[:-1]) > 0
    positions = np.flatnonzero(keep)
    if not len(positions):
        return series.iloc[:0]
    # A missing value prevents Plotly from connecting separate context windows.
    gaps = np.flatnonzero(keep[:-1] & ~keep[1:]) + 1
    gaps = gaps[gaps < positions[-1]]
    positions = np.union1d(positions, gaps)
    plotted = series.iloc[positions].copy()
    plotted.iloc[np.flatnonzero(~keep[positions])] = np.nan
    return plotted


def filter_short_faults(flags, min_faulty_seconds):
    """Keep runs longer than the threshold, using the plotted midpoint boundaries."""
    seconds = float(min_faulty_seconds)
    if not np.isfinite(seconds) or seconds < 0:
        raise ValueError("Minimum faulty duration must be a finite, nonnegative number")
    filtered = flags.copy()
    if seconds == 0 or flags.empty:
        return filtered
    times = pd.DatetimeIndex(flags.index)
    window = pd.Timedelta(seconds=seconds)
    for column in flags.columns:
        faulty = flags[column].to_numpy(dtype=bool)
        starts = np.flatnonzero(faulty & ~np.r_[False, faulty[:-1]])
        stops = np.flatnonzero(faulty & ~np.r_[faulty[1:], False]) + 1
        for start, stop in zip(starts, stops):
            left = times[start] if start == 0 else times[start - 1] + (times[start] - times[start - 1]) / 2
            right = times[stop - 1] if stop == len(times) else times[stop - 1] + (times[stop] - times[stop - 1]) / 2
            if right - left <= window:
                filtered.iloc[start:stop, filtered.columns.get_loc(column)] = False
    return filtered


def anomaly_flags(scores, thresholds, min_nonfaulty_seconds, min_faulty_seconds=0):
    # Unknown samples must not be treated as short recoveries and filled in.
    flags = scores.lt(thresholds).astype("boolean").mask(scores.isna()).fillna(False).astype(bool)
    return filter_short_faults(flags, min_faulty_seconds)


def anomaly_intervals(score, threshold, min_nonfaulty_seconds=0, min_faulty_seconds=0):
    if threshold is None or score.empty:
        return []

    mask = anomaly_flags(score.to_frame(), threshold, min_nonfaulty_seconds, min_faulty_seconds).iloc[:, 0]
    return intervals_from_flags(mask)


def intervals_from_flags(mask):
    """Extract midpoint boundaries from flags already filtered during analysis."""
    if mask.empty:
        return []

    x = mask.index
    edges = np.diff(mask.astype(int))
    starts_idx = np.where(edges == 1)[0]
    ends_idx = np.where(edges == -1)[0]

    if mask.iloc[0]:
        starts_idx = np.r_[-1, starts_idx]
    if mask.iloc[-1]:
        ends_idx = np.r_[ends_idx, len(mask) - 1]

    def midpoint(i):
        if i < 0:
            return x[0]
        return x[i] + (x[i + 1] - x[i]) / 2 if i < len(x) - 1 else x[i]

    starts_x = [midpoint(i) for i in starts_idx]
    ends_x = [midpoint(i) for i in ends_idx]
    return list(zip(starts_x, ends_x))


def result_component_intervals(result):
    """Read persisted intervals, supporting results saved before they were added."""
    if "component_intervals" in result:
        return result["component_intervals"]
    flags = result.get("anomaly")
    if isinstance(flags, pd.DataFrame):
        return {column: intervals_from_flags(flags[column]) for column in flags.columns}
    scores = result.get("score")
    thresholds = result.get("thresholds") or {}
    if not isinstance(scores, pd.DataFrame):
        return {}
    return {
        column: anomaly_intervals(
            scores[column], thresholds.get(column),
            result.get("min_nonfaulty_seconds", 0), result.get("min_faulty_seconds", 0),
        )
        for column in scores.columns
    }


def highlight_intervals(fig, intervals, row=None, color=AI4CPS_HIGHLIGHT, opacity=1.0):
    subplot = fig.get_subplot(row or 1, 1)
    xref = subplot.xaxis.plotly_name.replace("axis", "")
    if row is None:
        yref = "paper"
    else:
        yref = subplot.yaxis.plotly_name.replace("axis", "") + " domain"

    shapes = [
        dict(
            type="rect",
            xref=xref,
            yref=yref,
            x0=start,
            x1=end,
            y0=0,
            y1=1,
            fillcolor=color,
            opacity=opacity,
            line_width=0,
            layer="above",
        )
        for start, end in intervals
    ]
    fig.layout.shapes = tuple(fig.layout.shapes) + tuple(shapes)
    annotations = []
    for start, end in intervals:
        seconds = (end - start).total_seconds()
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        duration = " ".join(
            f"{value:g} {unit}"
            for value, unit in ((days, "d"), (hours, "h"), (minutes, "min"), (seconds, "s"))
            if value
        ) or "0 s"
        annotations.append(dict(
            text=duration,
            x=start + (end - start) / 2, xref=xref,
            y=1, yref=yref,
            showarrow=False, xanchor="center", yanchor="top", yshift=-3,
            font=dict(family=SELFX_FONT, size=10, color=AI4CPS_TEXT),
            bgcolor=theme.SEMANTIC['negative'], borderpad=2,
        ))
    fig.layout.annotations = tuple(fig.layout.annotations) + tuple(annotations)


def apply_selfx_plot_style(fig, showlegend=False, legend_control=True):
    updatemenus = []
    if fig.data and legend_control:
        updatemenus.append(dict(
            type="buttons",
            direction="right",
            showactive=True,
            active=-1,
            x=0.005,
            y=0.995,
            xanchor="left",
            yanchor="top",
            bgcolor=selfx_colors.hex_to_rgba(theme.SURFACE, 0.88),
            bordercolor=selfx_colors.hex_to_rgba(theme.TEXT, 0.16),
            borderwidth=1,
            font=dict(family=SELFX_FONT, size=10, color=AI4CPS_TEXT),
            pad=dict(l=3, r=3, t=2, b=2),
            buttons=[dict(
                label="Legend",
                method="relayout",
                args=[{"showlegend": True}],
                args2=[{"showlegend": False}],
            )],
        ))

    fig.update_layout(
        paper_bgcolor=AI4CPS_PAPER_BG,
        plot_bgcolor=AI4CPS_PLOT_BG,
        font=dict(family=SELFX_FONT, color=AI4CPS_TEXT),
        title_font=dict(family=SELFX_FONT, color=AI4CPS_TEXT),
        colorway=SELFX_COLORWAY,
        legend=dict(
            bgcolor=selfx_colors.hex_to_rgba(theme.SURFACE, 0.88),
            bordercolor=selfx_colors.hex_to_rgba(theme.TEXT, 0.16),
            borderwidth=1,
            font=dict(family=SELFX_FONT, color=AI4CPS_TEXT),
            orientation="h",
            yanchor="top",
            y=0.91,
            xanchor="right",
            x=0.99,
        ),
        updatemenus=updatemenus,
        hoverlabel=dict(
            font=dict(family=SELFX_FONT, color="white"),
            namelength=-1,
        ),
        showlegend=showlegend,
    )
    fig.update_xaxes(
        color=AI4CPS_MUTED_TEXT,
        gridcolor=AI4CPS_GRID,
        linecolor=AI4CPS_AXIS,
        zerolinecolor=AI4CPS_GRID,
        title_font=dict(family=SELFX_FONT, color=AI4CPS_MUTED_TEXT),
        tickfont=dict(family=SELFX_FONT, color=AI4CPS_MUTED_TEXT),
    )
    fig.update_yaxes(
        color=AI4CPS_MUTED_TEXT,
        gridcolor=AI4CPS_GRID,
        linecolor=AI4CPS_AXIS,
        zerolinecolor=AI4CPS_GRID,
        title_font=dict(family=SELFX_FONT, color=AI4CPS_MUTED_TEXT),
        tickfont=dict(family=SELFX_FONT, color=AI4CPS_MUTED_TEXT),
    )
    for annotation in fig.layout.annotations:
        if not annotation.font.color:
            annotation.font = dict(family=SELFX_FONT, color=AI4CPS_TEXT)
    return fig


def add_subplot_labels(fig, labels):
    for index, label in enumerate(labels, start=1):
        fig.update_yaxes(
            title_text=label,
            title_font=dict(family=SELFX_FONT, size=11, color=AI4CPS_TEXT),
            automargin=True,
            row=index,
            col=1,
        )
    return fig


def empty_figure(message):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        align="center",
        font=dict(family=SELFX_FONT, size=14, color=selfx_colors.NEGATIVE[1]),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
    return apply_selfx_plot_style(fig)


def add_value_histogram(fig, series, row, color, threshold=None):
    """Bin the full series on the server; send only counts and value bins."""
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    values = values[np.isfinite(values)]
    edges = np.histogram_bin_edges(values, bins=40)
    if threshold is not None:
        if edges[0] < threshold < edges[-1]:
            edges = np.unique(np.append(edges, threshold))
        elif threshold == edges[-1]:
            # The last bin includes its right edge. Add a normal bin so values
            # equal to the threshold are kept separate from faulty values.
            edges = np.append(edges, edges[-1] + (edges[-1] - edges[-2]))
    counts, edges = np.histogram(values, bins=edges)
    colors = np.where(edges[1:] <= threshold, AI4CPS_THRESHOLD, color) if threshold is not None else color
    fig.add_trace(go.Bar(
        x=counts, y=(edges[:-1] + edges[1:]) / 2, width=np.diff(edges),
        orientation="h", marker_color=colors, marker_line_width=0, opacity=0.6,
        name=series.name, legendgroup=str(series.name), showlegend=False,
        customdata=np.column_stack([edges[:-1], edges[1:]]),
        hovertemplate=(f"<b>{series.name}</b><br># Samples: %{{x}}<br>"
                       "Values: %{customdata[0]:.4g} – %{customdata[1]:.4g}<extra></extra>"),
    ), row=row, col=2)
    fig.update_layout(bargap=0, bargroupgap=0)
    fig.update_xaxes(title_text=None, type="linear", matches=None, showticklabels=True, rangemode="tozero",
                     row=row, col=2)
    fig.update_yaxes(showticklabels=True, side="right", automargin=True, row=row, col=2)
    return edges


def timeseries_figure(data, showlegend=False, component_intervals=None, context_seconds=None, thresholds=None):
    is_all = context_seconds is not None
    fig = make_subplots(
        rows=len(data.columns), cols=2, shared_xaxes=True, shared_yaxes=True,
        column_widths=[0.8, 0.2], horizontal_spacing=0.035,
        vertical_spacing=min(0.12, 0.22 / max(1, len(data.columns) - 1)),
    )
    for row, column in enumerate(data.columns, start=1):
        plotted = data[column]
        color = SELFX_SCORE_COLOR
        fig.add_trace(go.Scattergl(
            x=plotted.index,
            y=plotted,
            mode="markers" if is_all else "lines",
            marker=dict(size=4), connectgaps=False,
            showlegend=False if is_all else True,
            name=column, legendgroup=str(column), line=dict(color=color),
            hovertemplate=f"<b>{column}</b><br>Time: %{{x}}<br>Value: %{{y}}<extra></extra>",
        ),
                      row=row, col=1)
        edges = add_value_histogram(fig, data[column], row, color, (thresholds or {}).get(column))
        # Start with the full histogram extent.
        # add_threshold_line also includes the threshold in this initial range.
        padding = (edges[-1] - edges[0]) * 0.05
        fig.update_yaxes(range=[edges[0] - padding, edges[-1] + padding], autorange=False,
                         row=row)
    add_subplot_labels(fig, [str(column) for column in data.columns])
    fig.update_layout(height=max(280, len(data.columns) * 180), barmode="overlay",
                      margin=dict(l=60, r=30, t=25, b=35))
    if not data.empty:
        start, end = data.index.min(), data.index.max()
        if start == end:
            start, end = start - pd.Timedelta(seconds=1), end + pd.Timedelta(seconds=1)
        # Empty anomaly traces cannot infer a date axis. Give every time subplot
        # the same date range and visible ticks; histograms retain count axes.
        fig.update_xaxes(type="date", range=[start, end], autorange=False,
                         showticklabels=True, col=1)
    return apply_selfx_plot_style(fig, showlegend=False if is_all else showlegend,
                                  legend_control=not is_all)


def component_anomaly_figure(data, score, showlegend=False, component=None, threshold=None):
    base_plot_height = max(380, min(620, 320 + len(data.columns) * 24)) - 60
    spacing = max(0.12, AD_COMPONENT_VERTICAL_SPACING)
    gap_height = base_plot_height * spacing
    score_height = base_plot_height * (1 - spacing) * 0.2
    variables_height = base_plot_height * (1 - spacing) * 0.8 * 2
    plot_height = score_height + gap_height + variables_height
    fig = make_subplots(
        rows=2,
        cols=2,
        shared_xaxes=True, shared_yaxes=True,
        column_widths=[0.8, 0.2], horizontal_spacing=0.035,
        vertical_spacing=gap_height / plot_height,
        row_heights=[score_height, variables_height],
    )
    fig.add_trace(
        go.Scattergl(
            x=score.index,
            y=score,
            mode="lines",
            name="Anomaly score",
            line=dict(color=SELFX_SCORE_COLOR, width=2.5),
            hovertemplate="<b>Anomaly score</b><br>Time: %{x}<br>Score: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    add_value_histogram(fig, score.rename(component or "Anomaly score"), 1, SELFX_SCORE_COLOR, threshold)
    for index, column in enumerate(data.columns, start=1):
        fig.add_trace(
            go.Scattergl(
                x=data.index,
                y=data[column],
                mode="lines",
                name=column, legendgroup=str(column),
                line=dict(color=SELFX_COLORWAY[(index - 1) % len(SELFX_COLORWAY)]),
                hovertemplate=f"<b>{column}</b><br>Time: %{{x}}<br>Value: %{{y}}<extra></extra>",
            ),
            row=2,
            col=1,
        )
        add_value_histogram(fig, data[column], 2, SELFX_COLORWAY[(index - 1) % len(SELFX_COLORWAY)])
    add_subplot_labels(fig, ["Anomaly Score", "Signals"])
    fig.update_layout(
        height=plot_height + 60,
        barmode="overlay",
        margin=dict(l=60, r=30, t=25, b=35),
    )
    return apply_selfx_plot_style(fig, showlegend=showlegend)


def add_threshold_line(fig, threshold, row=1, interval_count=None):
    if threshold is None:
        return
    for trace in fig.select_traces(row=row, col=1):
        if trace.type not in ("scatter", "scattergl"):
            continue
        below_threshold = np.asarray(trace.y, dtype=float) < threshold
        trace.marker.color = np.where(below_threshold, AI4CPS_THRESHOLD, SELFX_SCORE_COLOR)
        if trace.mode == "lines":
            trace.mode = "lines+markers"
            trace.marker.size = np.where(below_threshold, 4, 0)
    axis_range = fig.get_subplot(row, 1).yaxis.range
    if axis_range is not None:
        lower, upper = axis_range
        padding = (max(upper, threshold) - min(lower, threshold)) * 0.05
        fig.update_yaxes(range=[min(lower, threshold - padding),
                                max(upper, threshold + padding)], row=row)
    for col in (1, 2):
        annotation = dict(
            annotation_text=f"Threshold: {threshold:g}",
            annotation_position="top right",
            annotation_font=dict(family=SELFX_FONT, color=AI4CPS_THRESHOLD, size=11),
        ) if col == 2 else {}
        fig.add_hline(
            y=threshold, row=row, col=col,
            line=dict(width=3, color=AI4CPS_THRESHOLD),
            opacity=0.5, layer="below", **annotation,
        )
    if interval_count is not None:
        subplot = fig.get_subplot(row, 2)
        fig.add_annotation(
            text=f"<b>{interval_count} faulty intervals</b>",
            x=1, y=threshold,
            xref=subplot.xaxis.plotly_name.replace("axis", "") + " domain",
            yref=subplot.yaxis.plotly_name.replace("axis", ""),
            xanchor="right", yanchor="top", yshift=-3,
            showarrow=False,
            font=dict(family=SELFX_FONT, color=AI4CPS_TEXT, size=11),
        )
