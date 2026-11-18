# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Nemanja Hranisavljevic

"""Small, reusable dashboard controls backed by the framework's CSS classes."""
from dash import html
import dash_bootstrap_components as dbc


def loading_status(message):
    """Show a persistent inline spinner while the next dashboard view is prepared."""
    return html.Div([
        html.Span(dbc.Spinner(size='sm', color='secondary', display='show'),
                  **{'aria-hidden': 'true'}),
        html.Span(message),
    ], className='d-flex align-items-center justify-content-end gap-2 py-3 w-100 text-end',
        role='status', **{'aria-live': 'polite'})


def badge(children, color="neutral", className="", **props):
    """Support AI4CPS semantic roles even when DBC only recognizes Bootstrap colors."""
    return dbc.Badge(children, color=color, className=f"{className} text-bg-{color}".strip(), **props)


def progress(*, value, color="positive", className="", **props):
    """Set the bar theme on its container so custom semantic roles reach the bar."""
    return dbc.Progress(value=value, color=color, className=f"{className} progress-{color}".strip(), **props)


def copy_button(label, content, status_id, *, show_label=False):
    icon = html.I(className="fa-regular fa-copy", **{"aria-hidden": "true"})
    return html.Button(
        [icon, html.Span(label)] if show_label else icon,
        type="button", title=label,
        className=("small-inline-button button-secondary clipboard-action" if show_label else
                   "small-inline-button icon-button copy-button ms-2"),
        **{"aria-label": label, "data-copy-content": content, "data-copy-status": status_id},
    )


def normalize_selection(value):
    values = [value] if isinstance(value, str) else value or []
    names = {}
    for name in values:
        if isinstance(name, str) and name.strip():
            names.setdefault(name.strip().casefold(), name.strip())
    return list(names.values())
