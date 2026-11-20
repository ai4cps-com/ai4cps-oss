# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Nemanja Hranisavljevic

"""Shared design tokens for CSS, Plotly and other dashboard renderers.

Applications select semantic roles; this module owns their visual definitions.
The CSS endpoint and Python renderers consume the same palette, so changing a
palette entry updates controls, diagrams and plots together.
"""
from __future__ import annotations

from . import colors


FONT = "Poppins, sans-serif"
TEXT = colors.NEUTRAL[0]
MUTED = "#626176"
SURFACE = colors.WHITE
SURFACE_SUBTLE = "#F7F8FF"
BORDER = "#DADAE3"
SIDEBAR = "#242342"
HOVER = "#3A3956"
PLOT_GRID = colors.hex_to_rgba(TEXT, 0.14)
PLOT_AXIS = colors.hex_to_rgba(TEXT, 0.28)
SCHEMATIC_GAP_PT = 10
SCHEMATIC_TITLE_HEIGHT = 32

SEMANTIC = {
    "positive": colors.POSITIVE[0],
    "negative": colors.NEGATIVE[0],
    "error": colors.NEGATIVE[1],
    "warning": colors.NEGATIVE[2],
    "info": colors.OTHER[0],
    "diagnosis": colors.NEGATIVE[1],
    "off": colors.NEGATIVE[1],
    "reconfiguration": colors.POSITIVE[2],
    "neutral": colors.NEUTRAL[2],
    "unchanged": colors.NEUTRAL[5],
    "primary": colors.POSITIVE[0],
    "secondary": colors.NEUTRAL[0],
    "cancel": colors.NEUTRAL[5],
}
CHART_COLORS = [TEXT, colors.POSITIVE[2], colors.NEUTRAL[1], *colors.OTHER,
                colors.POSITIVE[1], colors.NEUTRAL[3], colors.POSITIVE[3]]

# Processing intervals remain subtle beneath telemetry and score traces.
PROCESSING_WINDOWS = {
    'ad_context': {'color': SEMANTIC['negative'], 'opacity': .045, 'dash': 'dot', 'width': 1},
    'ad': {'color': SEMANTIC['negative'], 'label_color': '#A65300', 'opacity': .18, 'dash': 'solid', 'width': 1},
    'dx': {'color': SEMANTIC['diagnosis'], 'opacity': .10, 'dash': 'dash', 'width': 1},
    'reconfiguration': {'color': SEMANTIC['reconfiguration'], 'opacity': .16, 'dash': 'solid', 'width': 2},
}


def readable_text(background: str) -> str:
    """Choose black or white using WCAG relative luminance and contrast ratio."""
    channels = [value / 255 for value in colors.hex_to_rgb(background)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
              for value in channels]
    luminance = sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    return colors.BLACK if (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05) else colors.WHITE


def _hover_color(background: str) -> str:
    if background == TEXT:
        return HOVER
    return colors.rgb_to_hex(tuple(round(channel * 0.88 + ink * 0.12)
                                   for channel, ink in zip(colors.hex_to_rgb(background), colors.hex_to_rgb(TEXT))),
                             with_hash=True).upper()


def css_variables() -> str:
    """Build the framework stylesheet directly from the Python palette."""
    tokens = {"font": FONT, "text": TEXT, "muted": MUTED, "surface": SURFACE,
              "surface-subtle": SURFACE_SUBTLE, "border": BORDER,
              "sidebar": SIDEBAR, "hover": HOVER, **SEMANTIC}
    for family, palette in (("positive", colors.POSITIVE), ("negative", colors.NEGATIVE),
                            ("neutral", colors.NEUTRAL), ("other", colors.OTHER)):
        tokens.update({f"{family}-{index}": color for index, color in enumerate(palette)})
    lines = [":root {"]
    for name, value in tokens.items():
        lines.append(f"  --ai4cps-{name}: {value};")
        if value.startswith("#"):
            lines.append(f"  --ai4cps-{name}-rgb: {', '.join(map(str, colors.hex_to_rgb(value)))};")
    for name, value in SEMANTIC.items():
        lines.append(f"  --ai4cps-on-{name}: {readable_text(value)};")
        hover = _hover_color(value)
        lines.append(f"  --ai4cps-{name}-hover: {hover};")
        lines.append(f"  --ai4cps-on-{name}-hover: {readable_text(hover)};")
    # Bootstrap utility classes and component variants share the same roles.
    for bootstrap, semantic in (("success", "positive"), ("danger", "error"),
                                 ("warning", "warning"), ("info", "info"),
                                 ("primary", "primary"), ("secondary", "secondary"),
                                 ("positive", "positive"), ("negative", "negative"), ("error", "error"),
                                 ("diagnosis", "diagnosis"), ("off", "off"), ("unchanged", "unchanged"),
                                 ("reconfiguration", "reconfiguration")):
        lines.extend((f"  --bs-{bootstrap}: var(--ai4cps-{semantic});",
                      f"  --bs-{bootstrap}-rgb: var(--ai4cps-{semantic}-rgb);"))
    lines.extend((
        "  --bs-body-font-family: var(--ai4cps-font);",
        "  --bs-body-color: var(--ai4cps-text);",
        "  --bs-body-color-rgb: var(--ai4cps-text-rgb);",
        "  --bs-body-bg: var(--ai4cps-surface);",
        "  --bs-secondary-color: var(--ai4cps-muted);",
        "  --bs-tertiary-bg: var(--ai4cps-surface-subtle);",
        "  --bs-border-color: var(--ai4cps-border);",
        "  --bs-link-color: var(--ai4cps-info);",
        "  --bs-link-hover-color: var(--ai4cps-text);",
    ))
    lines.append("}")
    return "\n".join(lines)
