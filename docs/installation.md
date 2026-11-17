# Installation

```bash
pip install ai4cps
```
Install `ai4cps` and import from `ai4cps`, for example `from ai4cps.dash.dashboard import Dash4CPS`.

Legacy `selfx` imports remain supported and resolve to the same modules as
`ai4cps`. The old dashboard class name `SelfXDash` is an alias for `Dash4CPS`.
Use `ai4cps` and `Dash4CPS` in new code.
Dashboards are served under `/ai4cps/`. The deprecated `/selfx/` path keeps old links working: it redirects
to the same `/ai4cps/` address, with its query parameters and fragment.
The deprecated `selfx` distribution provides compatibility for legacy `selfx` imports.
