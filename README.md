# AI4CPS OSS

[![GitHub](https://img.shields.io/github/license/ai4cps-com/ai4cps-oss.svg?color=dark-green)](https://github.com/ai4cps-com/ai4cps-oss/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/ai4cps.svg)](https://pypi.org/project/ai4cps/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ai4cps.svg)](https://pypi.org/project/ai4cps/)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/ai4cps-com/ai4cps-oss.svg)](https://github.com/ai4cps-com/ai4cps-oss/graphs/contributors)
[![Sponsor](https://img.shields.io/badge/Sponsor-❤-ff69b4)](https://github.com/sponsors/ai4cps-com)

 *SelfX is a Python framework for building ML & AI apps in the domain of Cyber-Physical Systems (CPSs)*.

<div align="center">
  <a href="https://www.ai4cps.com">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="ai4cps/dash/assets/Logo%20dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="ai4cps/dash/assets/Logo%20light.svg">
      <img src="ai4cps/dash/assets/Logo%20light.svg" width="400px" alt="Maintained by AI4CPS">
    </picture>
  </a>
</div>


Built on top of [Dash](https://dash.plotly.com/), SelfX allows simple implementation of AI tools for CPSs.
Read [our tutorial](https://selfx.ai4cps.com/getting-started). 

This software is developed at [Helmut Schmidt University / University of Federal Armed Forces Hamburg](www.hsu-hh.de)
at the [Professorship of Computer Science in Mechanical Engineering](https://www.hsu.hamburg/imb/en/)
at the Institute of Automation Technology.


### SelfX App Examples

To be added.

### Styling Overrides

SelfX loads override stylesheets after its default dashboard assets. Apps can
append project CSS with `css_overrides` when creating `SelfXDash`:

```python
selfx = dashboard.SelfXDash(
    css_overrides=["assets/selfx_overrides.css"],
)
```

Local CSS files are served by SelfX, and external CSS URLs can also be passed.
For small changes, pass raw CSS directly:

```python
selfx = dashboard.SelfXDash(
    css_overrides=[":root { --selfx-sidebar-width: 19rem; }"],
)
```

### AI4CPS OSS & SelfX Enterprise

| Category                      | Feature                          | SelfX OOS (Open Source) | SelfX Enterprise         |
|-------------------------------|----------------------------------| ----------------------- | ------------------------ |
| **Core Platform**             | Core SelfX Platform              | ✅                       | ✅                        |
|                               | Workflow Engine                  | ✅                       | ✅                        |
|                               | API Access                       | Basic                   | Extended                 |
|                               | Plugin / Extension Support       | Limited                 | Full                     |
|                               | LLM Integration                  | Limited                 | Full                     |
| **AI Capabilities**           | Basic AI tools                   | ✅                       | ✅                        |
|                               | Dayly and Monthly Reports        | ❌                       | ✅                        |
| **Security & Access Control** | User Authentication              | Basic                   | Advanced                 |
|                               | Role-Based Access Control (RBAC) | Limited                 | ✅                        |
|                               | Single Sign-On (SSO)             | ❌                       | ✅                        |
| **Scalability & Reliability** | Horizontal Scaling               | ❌                       | ✅                        |
|                               | High Availability / Clustering   | ❌                       | ✅                        |
|                               | Multi-Tenant Support             | ❌                       | ✅                        |
| **Integrations**              | Standard Integrations            | Limited                 | Extended                 |
|                               | Enterprise Integrations          | ❌                       | ✅                        |
|                               | Custom Connectors                | Limited                 | ✅                        |
| **Observability**             | Basic Logging                    | ✅                       | ✅                        |
|                               | Metrics & Monitoring             | Basic                   | Advanced                 |
|                               | Alerting                         | ❌                       | ✅                        |
| **Operations**                | Deployment                       | Self-hosted             | Self-hosted / Enterprise |
|                               | Backup & Recovery Tools          | ❌                       | ✅                        |
|                               | Performance Optimization         | ❌                       | ✅                        |
| **Support & Licensing**       | License                          | Open Source             | Commercial               |
|                               | Documentation                    | ✅                       | ✅                        |
|                               | Support                          | Community               | Priority / SLA           |
|                               | Professional Services            | ❌                       | Available                |

LLMs can be used to easily create features

See [https://ai4cps.com](https://ai4cps.com) to get in touch.


Install `ai4cps` and import from `ai4cps`, for example `from ai4cps.dash.dashboard import SelfXDash`.
The deprecated `selfx` distribution provides compatibility for legacy `selfx` imports.
