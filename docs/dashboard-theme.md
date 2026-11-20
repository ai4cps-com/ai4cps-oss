# Dashboard theme

`Dash4CPS` loads the framework's CSS and JavaScript assets automatically and serves
`/_ai4cps/theme.css` under its route prefix. Applications use classes and semantic
roles; they do not need their own stylesheet or inline CSS dictionaries.

## Colors

`ai4cps.dash.colors` defines the AI4CPS palettes. `ai4cps.dash.theme` is the single
mapping used by CSS, Plotly, Cytoscape, tables, and raster schematic annotations.

| Role | Palette | Use |
| --- | --- | --- |
| `positive` / `primary` | `POSITIVE[0]` | Positive state, primary action |
| `negative` | `NEGATIVE[0]` | Light orange (`#FFA94D`) anomaly badges, attention |
| `error` | `NEGATIVE[1]` | Fault, destructive action |
| `warning` | `NEGATIVE[2]` | General warnings |
| `info` | `OTHER[0]` | Informational state |
| `diagnosis` | `NEGATIVE[1]` | Red diagnosis and identified root causes |
| `off` | `NEGATIVE[1]` | Red OFF signals |
| `reconfiguration` | `POSITIVE[2]` | Teal ON signals |
| `secondary` | `NEUTRAL[0]` | Secondary action |
| `cancel` | `NEUTRAL[5]` | Light gray Cancel/dismiss action |
| `neutral` | `NEUTRAL[2]` | Inactive state |
| `unchanged` | `NEUTRAL[5]` | Light gray unchanged configuration values |

`NEGATIVE[1]` is red (`#D32F2F`). Changed signals use their ON/OFF color;
unchanged configuration values use light gray (`#E8E8ED`). Arrows and tooltips
also indicate changes.

Use `ai4cps.dash.components.badge` and `progress` with `color="positive"`,
`color="error"`, etc. These adapters also add the shared classes because DBC
does not render every custom color variant. Buttons can use `button-positive`,
`btn-outline-error`, etc. The usual `success` and `danger` aliases resolve to
these same colors. Filled buttons,
badges, and progress bars receive a contrasting foreground automatically.
Tokens are available as `--ai4cps-positive`, `--ai4cps-on-positive`, etc.
Filled buttons use distinct `--ai4cps-<role>-hover` shades and matching
foreground tokens, with a short transition that respects reduced motion.
Change palette mappings in `theme.py`, rather than redefining colors in an app.

## Controls and layout

| Classes | Purpose |
| --- | --- |
| `small-inline-button` | Compact action with a consistent 2rem minimum height and 1px border |
| `icon-button` | Square icon action; combine with `small-inline-button` |
| `copy-button` | Quiet copy action, with copied/error feedback |
| `copy-badge` | Copyable badge with hover and keyboard feedback |
| `badge-action` | Clickable badge with hover and keyboard feedback, retaining its fill color and without a copy icon |
| `accordion-with-action` | Accordion row with a separate action immediately after its title |
| `button-positive`, `button-error`, etc. | Semantic variants for native buttons |
| `button-cancel` / DBC `color="cancel"` | Light gray cancellation action, with dark text and a darker gray hover state |
| `toggle-button toggle-positive` | Subtly tinted positive option with a filled positive selected state |
| `warning-selector`, `negative-selector`, `diagnosis-selector` | Wrapping groups of toggle labels with semantic selected states |
| `configuration-selector` | State toggles; `original-on` / `original-off` distinguish changes |
| `form-editor`, `field-comment`, `time-field`, `field-dropdown` | Consistent editor controls |
| `control-inline` | Label and optional actions beside a dropdown, up to 32rem wide, wrapping on small screens |
| `control-compact` | A 2rem-high dropdown; multiple selected values stay on one horizontally scrolling row |
| `control-inline control-wide` | Inline label and actions with a dropdown that fills the remaining width |
| `control-compact control-wrap` | Compact multiselect that grows in height as selected values wrap onto more rows |
| `tab-container` | Tabs with dark text, a light teal hover fill, and a teal selected indicator |
| `form-editor-wide` | Wide editor dialog, up to 80rem, bounded by viewport margins |
| `tooltip-content tooltip-list` | Dark, readable tooltip; content scrolls above 50vh, with the arrow outside the scroll area |
| `tooltip-content tooltip-negative`, `tooltip-content tooltip-diagnosis` | Light tints of anomaly/diagnosis badge colors (20% semantic color, 80% surface) with dark text |
| `tooltip-label` | Focusable tooltip text with a dotted underline and help cursor |
| `text-subtle` | Light gray supporting text using `NEUTRAL[2]` |
| `schematic-row`, `schematic-panel`, `schematic-stage` | Responsive schematic layout |
| `schematic-overlay`, `schematic-marker`, `warning-blink` | Layered diagrams, marker targets, alarm animation |
| `metric-card`, `data-table`, `metadata-badge`, `tree-*` | Shared data presentation |

Tooltip targets can specify `data-tooltip-group` and
`data-tooltip-id` (the corresponding DBC Tooltip's `id`) to keep one tooltip
visible per group on hover or keyboard focus. Use zero hide delay and disable
fading for adjacent image markers to avoid overlapping closing animations.

Use Bootstrap layout utilities (`d-flex`, `gap-2`, `w-100`, `text-start`, etc.) for
ordinary spacing and alignment. `theme_utilities.css` provides additional shared
typography, tree, graph, and field utilities. Interactive controls retain their
border in normal, focused, and selected states and show a visible keyboard focus
outline. Put icons in accessible buttons with an `aria-label`.

```python
from dash import html
import dash_bootstrap_components as dbc
from ai4cps.dash.components import copy_button

action = dbc.Button("Edit label", color="secondary", outline=True,
                    className="small-inline-button")
copy = copy_button("Copy alternative", "CFA1: ON", status_id="copy-status")
toggle = dbc.Button("Not an anomaly", color="secondary", outline=True,
                    active=True,
                    className="small-inline-button toggle-button toggle-positive")
```

`copy_button` supplies markup and data attributes. Pass `show_label=True` for a
standard button with both a copy icon and visible text. Register a clientside
callback using `ClientsideFunction(namespace="ai4cps", function_name="clipboard")` to
initialize copy handling, with a live status element matching `status_id`.
The shared `alarm` clientside function manages audio and overlay synchronization.

Schematic marker buttons use `schematic-marker` for transparent image targets and
keyboard focus. Shared plot navigation handles buttons with `data-plot-dropdown`
and `data-plot-value`: a click sets the target dropdown value. Optional
`data-plot-tabs` / `data-plot-tab` select a tab; `data-plot-panel` identifies the
panel to wait for before scrolling to `data-plot-target`. Apply
`plot-navigation-target` to that section to keep it clear of fixed dashboard bars.
The delegated handler also covers buttons added by later callbacks and respects
the user's reduced motion preference.

## Third-party renderers

CSS cannot express Plotly layouts, Cytoscape stylesheets, DataTable cell styles,
or data-dependent image coordinates. These definitions also belong in AI4CPS:

- `plotting.apply_theme` applies the `ai4cps` Plotly template and named profiles
  (`timeline`, `timeseries`, `controls`, `forecasts`, `scenario`, `simulation`).
  `Dash4CPS` makes this template the default for new figures.
- `plotting.score_subplots` renders selected groups on shared time axes;
  scores and raw telemetry use UTC timestamps, UTC calendar-day filters, and
  `Time (UTC)` axis labels.
  An optional `time_range=(start, end)` restricts both data and axes to an explicit
  UTC window in `score_subplots` and `score_signal_subplots`.
  its `subplot_height` argument sets each row's plotting area in pixels (default
  130px), with a fixed 20px gap between rows.
  Y-axis group labels wrap to fit the configured row height.
  Score and telemetry plots use individual-point hover (`closest`) and horizontal
  legends beneath the time-axis labels. The shared browser controls measure all
  legend rows and expand the figure and bottom margin to show every signal without
  scrolling. Plotting-area heights remain fixed, including after window resizing.
  Pass a `thresholds` mapping by group to add orange threshold lines and color
  score points strictly below their group's threshold. Set `larger_is_anomalous=True`
  for error scores such as FC, where points strictly above the cutoff are anomalous.
  Missing thresholds are
  left unmarked. Normal lines break at anomalous points, which remain visible
  as separate orange markers.
  `plotting.score_signal_subplots` shows one group's score above its raw signals
  on two shared time axes, without histograms. The score row uses `subplot_height`;
  the signal row is twice that height. It reuses threshold colors and supports
  shaded anomaly intervals and an upper-bound or lower-bound cutoff.
  `anomaly_plots` provides threshold, histogram, interval, and resampling renderers.
  Resampling requires the optional `plotly-resampler` package; raster schematic
  fonts require Pillow.
- `graph_styles` provides component and material-flow graph themes and renderer
  options, using readable text on category backgrounds.
- `styles.table_styles` supplies Dash DataTable properties.
- `styles.visibility` and `styles.schematic_*` bridge data-dependent geometry and
  visibility. They return renderer properties; applications supply data and state.

Add a reusable class or renderer helper here when another app needs a visual
pattern. Keep component names, labels, anomaly groups, and operating bounds in
the application. CSS/JS assets are included in framework wheels by `MANIFEST.in`.
