# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Nemanja Hranisavljevic

"""Reusable graph-renderer styles using the AI4CPS palette."""
from __future__ import annotations

from typing import Any

from . import colors, theme


def css_token(value):
    return ''.join(character if character.isalnum() or character in '-_' else '-' for character in str(value))


def transport_styles(roles):
    return {name: {'line-color': theme.SEMANTIC[role], 'target-arrow-color': theme.SEMANTIC[role],
                   'line-style': 'solid'} for name, role in roles.items()}


def material_flow_stylesheet(component_types=(), transported_roles=None) -> list[dict[str, Any]]:
    stylesheet = [
        {
            "selector": "node",
            "style": {
                "background-color": theme.MUTED,
                "color": theme.readable_text(theme.MUTED),
                "font-size": 12,
                "height": 30,
                "label": "data(id)",
                "shape": "round-rectangle",
                "text-halign": "center",
                "text-max-width": 70,
                "text-valign": "center",
                "text-wrap": "wrap",
                "width": 74,
            },
        },
        {
            "selector": "edge",
            "style": {
                "curve-style": "bezier",
                "line-color": theme.BORDER,
                "opacity": 0.65,
                "target-arrow-color": theme.BORDER,
                "target-arrow-shape": "triangle",
                "width": 0.8,
            },
        },
        {
            "selector": "node:selected",
            "style": {
                "border-width": 0,
            },
        },
        {
            "selector": "edge:selected",
            "style": {
                "opacity": 1,
                "width": 2,
            },
        },
        {
            "selector": ".area-order-edge",
            "style": {
                "line-color": colors.BLACK,
                "opacity": 0,
                "target-arrow-shape": "none",
                "width": 1,
            },
        },
        {
            "selector": ".area-group",
            "style": {
                "background-color": theme.SURFACE_SUBTLE,
                "background-opacity": 0.22,
                "border-width": 0,
                "color": theme.TEXT,
                "font-size": 14,
                "font-weight": 700,
                "label": "data(label)",
                "padding": "24px",
                "shape": "round-rectangle",
                "text-halign": "center",
                "text-valign": "top",
            },
        },
        {
            "selector": ".boundary-marker",
            "style": {
                "background-opacity": 0,
                "border-width": 0,
                "height": 1,
                "label": "",
                "opacity": 0,
                "width": 1,
            },
        },
        {
            "selector": ".boundary-arrow",
            "style": {
                "control-point-step-size": 18,
                "curve-style": "bezier",
                "line-color": theme.TEXT,
                "line-style": "solid",
                "opacity": 0.85,
                "target-arrow-color": theme.TEXT,
                "target-arrow-shape": "triangle",
                "width": 1.4,
            },
        },
        {
            "selector": ".shared-with-edge",
            "style": {
                "curve-style": "straight",
                "line-color": theme.MUTED,
                "line-style": "dashed",
                "opacity": 0.75,
                "target-arrow-shape": "none",
                "width": 1.2,
            },
        },
    ]

    for transported_item, style in transport_styles(transported_roles or {}).items():
        stylesheet.append(
            {
                "selector": f".transported-{transported_item}",
                "style": style,
            }
        )
    for index, component_type in enumerate(component_types):
        color = theme.CHART_COLORS[index % len(theme.CHART_COLORS)]
        stylesheet.append(
            {
                "selector": f".component-type-{css_token(component_type)}",
                "style": {
                    "background-color": color,
                    "color": theme.readable_text(color),
                },
            }
        )
    return stylesheet


def component_graph_options():
    """Typography and stroke options for ml4cps state/transition graphs."""
    return {"font_size": 12, "edge_font_size": 10, "color": theme.TEXT}


def system_graph_options():
    return {"height": "500px"}


def apply_component_graph_theme(graph):
    """Preserve graph semantics and data colors while normalizing renderer defaults."""
    graph.stylesheet = [*graph.stylesheet, {
        "selector": "node", "style": {
            "font-family": theme.FONT, "font-style": "normal", "color": theme.TEXT,
            "border-color": theme.TEXT,
        },
    }, {
        "selector": "edge", "style": {
            "font-family": theme.FONT, "font-style": "normal",
            "background-color": theme.SURFACE, "text-background-color": theme.SURFACE,
        },
    }]
    return graph



def component_graph_stylesheet():
    return [
        {"selector": "node", "style": {
            "label": "data(label)", "background-color": theme.SEMANTIC["info"],
            "color": theme.TEXT, "font-family": theme.FONT, "font-size": 13,
            "text-valign": "bottom", "text-margin-y": 6, "width": 32, "height": 32,
        }},
        {"selector": ".component", "style": {
            "background-color": theme.SURFACE_SUBTLE, "background-opacity": 0.45,
            "border-color": theme.BORDER, "border-width": 1, "shape": "round-rectangle",
            "padding": "30px", "font-size": 16, "font-weight": "bold", "text-valign": "top",
        }},
        {"selector": "edge", "style": {
            "label": "data(label)", "curve-style": "bezier", "target-arrow-shape": "triangle",
            "line-color": theme.MUTED, "target-arrow-color": theme.MUTED,
            "width": 2, "font-family": theme.FONT, "font-size": 11,
            "text-background-color": theme.SURFACE_SUBTLE,
            "text-background-opacity": 0.9, "text-background-padding": "3px",
        }},
    ]


def material_flow_layout():
    return {
        "name": "klay", "animate": False, "fit": True,
        "nodeDimensionsIncludeLabels": True, "padding": 40,
        "klay": {
            "borderSpacing": 12, "aspectRatio": 2.6, "compactComponents": True,
            "crossingMinimization": "LAYER_SWEEP", "cycleBreaking": "GREEDY",
            "direction": "RIGHT", "edgeRouting": "ORTHOGONAL", "edgeSpacingFactor": 0.35,
            "inLayerSpacingFactor": 0.75, "layoutHierarchy": True,
            "nodeLayering": "NETWORK_SIMPLEX", "nodePlacement": "LINEAR_SEGMENTS",
            "separateConnectedComponents": True, "spacing": 16, "thoroughness": 7,
        },
    }


def component_graph_layout():
    return {"name": "cose", "animate": False, "padding": 40,
            "nodeRepulsion": 12000, "idealEdgeLength": 100, "componentSpacing": 100}
