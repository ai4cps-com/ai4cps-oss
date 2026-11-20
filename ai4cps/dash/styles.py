# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Nemanja Hranisavljevic

"""Renderer adapters for visual properties that cannot be expressed as classes.

Use the CSS classes for normal layout and controls. These helpers only bridge
data-driven geometry, visibility and third-party renderer APIs.
"""
from . import theme


def visibility(visible, display="block"):
    return {"display": display if visible else "none"}


def schematic_marker(left, top, right, bottom, width, height):
    return {"left": f"{100 * left / width}%", "top": f"{100 * top / height}%",
            "width": f"{100 * (right - left) / width}%", "height": f"{100 * (bottom - top) / height}%"}


def schematic_aspect(width, height):
    return {"maxWidth": f"calc(var(--diagram-max-height, 100000px) * {width} / {height})"}


def schematic_panel(titled=True):
    return {} if titled else {"flex": "0 0 100%"}


def schematic_view(view):
    panels, row = [{}, {}], {}
    visible = set(view or []) & {"left", "right"}
    if not visible:
        return [visibility(False), visibility(False)], visibility(False)
    if visible != {"left", "right"}:
        index = 0 if visible == {"left"} else 1
        panels[index] = {"flex": "0 0 100%", "maxHeight": "calc(200vh / 3)",
                         "--diagram-max-height": "calc(200vh / 3 - 2rem)"}
        panels[1 - index] = visibility(False)
    return panels, row


def table_styles(font_size=13, column_count=0, fixed=False, scroll_height="70vh", column_width=None):
    cell = {"fontSize": f"{font_size}px", "textAlign": "left", "padding": "8px",
            "whiteSpace": "normal", "overflowWrap": "anywhere", "height": "auto",
            "color": theme.TEXT, "backgroundColor": theme.SURFACE}
    if fixed and column_count:
        cell.update(minWidth=0, width=f"{100 / column_count}%", maxWidth=f"{100 / column_count}%")
    if column_width:
        cell.update(minWidth=f"{column_width}px", width=f"{column_width}px", maxWidth=f"{column_width}px")
    result = {
        "style_as_list_view": True,
        "style_table": {"overflowX": "auto", "overflowY": "auto", "maxHeight": scroll_height, "width": "100%"},
        "style_cell": cell,
        "style_header": {"backgroundColor": theme.SURFACE, "fontWeight": "bold", "color": theme.TEXT, "border": "0px"},
        "style_data_conditional": [{"if": {"state": "active"}, "backgroundColor": theme.SURFACE_SUBTLE}],
    }
    if fixed:
        result["style_table"]["overflowX"] = "hidden"
        result["css"] = [{"selector": "table", "rule": "table-layout: fixed; width: 100%;"}]
    return result


def indexed_button(index):
    background = theme.CHART_COLORS[index % len(theme.CHART_COLORS)]
    return {"--bs-btn-bg": background, "--bs-btn-color": theme.readable_text(background),
            "--bs-btn-border-color": background}


def schematic_font(role="label"):
    """Font sizes for captions embedded in raster schematics."""
    from PIL import ImageFont

    return ImageFont.load_default(size=18 if role == "title" else 14)
