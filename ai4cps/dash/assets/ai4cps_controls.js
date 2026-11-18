// A focus-retained tooltip must close when another target in its group is entered.
if (!window.__ai4cpsExclusiveTooltips) {
    window.__ai4cpsExclusiveTooltips = true;
    const active = new Map();
    const activate = function(event) {
        const target = event.target.closest?.('[data-tooltip-group][data-tooltip-id]');
        if (!target || !window.dash_clientside?.set_props) return;
        const group = target.dataset.tooltipGroup;
        const tooltip = target.dataset.tooltipId;
        const previous = active.get(group);
        if (previous && previous.tooltip !== tooltip && document.getElementById(previous.target)) {
            dash_clientside.set_props(previous.tooltip, {is_open: false});
        }
        active.set(group, {tooltip: tooltip, target: target.id});
    };
    document.addEventListener('mouseover', activate);
    document.addEventListener('focusin', activate);
}

// Fit bottom legends to their rendered rows without shrinking the plotting area.
if (!window.__ai4cpsLegendSizing) {
    window.__ai4cpsLegendSizing = true;
    const plots = new Map();
    let scheduled = false;
    const schedule = function() {
        if (scheduled) return;
        scheduled = true;
        requestAnimationFrame(function() {
            scheduled = false;
            plots.forEach(function(binding, plot) {
                if (!plot.isConnected) {
                    binding.observer.disconnect();
                    plot.removeListener?.('plotly_afterplot', schedule);
                    plots.delete(plot);
                }
            });
            document.querySelectorAll('.js-plotly-plot').forEach(function(plot) {
                const sizing = plot.layout?.meta?.ai4cps_legend;
                if (!sizing || typeof plot.on !== 'function') return;
                if (!plots.has(plot)) {
                    const observer = new ResizeObserver(schedule);
                    observer.observe(plot);
                    plot.on('plotly_afterplot', schedule);
                    plots.set(plot, {observer: observer, fitting: false});
                }
                const binding = plots.get(plot);
                if (binding.fitting || !plot._fullLayout || !plot.clientWidth || !plot.clientHeight || !window.Plotly) return;
                const content = plot.querySelector('.legend .scrollbox');
                const legendHeight = content ? Math.ceil(content.getBBox().height) + 12 : 0;
                const bottom = Math.max(sizing.minimum_bottom, legendHeight + sizing.axis_gap);
                const height = sizing.plot_height + (plot.layout.margin?.t || 0) + bottom;
                const width = plot.clientWidth;
                if (Math.abs((plot.layout.margin?.b || 0) - bottom) < 1 &&
                    Math.abs(plot.layout.height - height) < 1 &&
                    Math.abs(plot._fullLayout.width - width) < 1) return;
                binding.fitting = true;
                Promise.resolve(Plotly.relayout(plot, {'margin.b': bottom, height: height, width: width}))
                    .finally(function() { binding.fitting = false; schedule(); });
            });
        });
    };
    const observer = new MutationObserver(schedule);
    observer.observe(document.documentElement, {childList: true, subtree: true});
    window.addEventListener('resize', schedule);
    schedule();
}

// Declarative plot links also work for controls inserted by later Dash callbacks.
if (!window.__ai4cpsPlotNavigationListener) {
    window.__ai4cpsPlotNavigationListener = function(event) {
        const button = event.target.closest('button[data-plot-dropdown][data-plot-value]');
        if (!button || button.disabled || !window.dash_clientside?.set_props) return;
        const dropdown = document.getElementById(button.dataset.plotDropdown);
        if (!dropdown) return;
        const target = document.getElementById(button.dataset.plotTarget);
        const panel = document.getElementById(button.dataset.plotPanel);
        const scroll = function() {
            if (panel?.hidden) return;
            requestAnimationFrame(function() {
                target?.scrollIntoView({block: 'start', behavior:
                    window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
            });
        };
        if (target) {
            target.__plotNavigationCleanup?.();
            const sizeObserver = new ResizeObserver(scroll);
            const visibilityObserver = new MutationObserver(scroll);
            sizeObserver.observe(target);
            if (panel) visibilityObserver.observe(panel, {attributes: true, attributeFilter: ['hidden']});
            const timer = setTimeout(function() { target.__plotNavigationCleanup(); }, 5000);
            target.__plotNavigationCleanup = function() {
                sizeObserver.disconnect();
                visibilityObserver.disconnect();
                clearTimeout(timer);
            };
            scroll();
        }
        dash_clientside.set_props(button.dataset.plotDropdown, {value: button.dataset.plotValue});
        if (button.dataset.plotTabs && document.getElementById(button.dataset.plotTabs)) {
            dash_clientside.set_props(button.dataset.plotTabs, {value: button.dataset.plotTab});
        }
    };
    document.addEventListener('click', window.__ai4cpsPlotNavigationListener);
}

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    ai4cps: Object.assign({}, window.dash_clientside && window.dash_clientside.ai4cps, {
        clipboard: function() {
            if (!window.__ai4cpsClipboardListener) {
                window.__ai4cpsClipboardListener = async function(event) {
                    const button = event.target.closest('button[data-copy-content][data-copy-status]');
                    if (!button) return;

                    const text = button.getAttribute('data-copy-content');
                    const statusId = button.getAttribute('data-copy-status');
                    let copied = false;
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        try {
                            await navigator.clipboard.writeText(text);
                            copied = true;
                        } catch (_) {
                            // Try the selection-based clipboard API if permission is denied.
                        }
                    }
                    if (!copied) {
                        const focused = document.activeElement;
                        const field = document.createElement('textarea');
                        field.value = text;
                        field.readOnly = true;
                        field.className = 'clipboard-buffer';
                        document.body.appendChild(field);
                        try {
                            field.focus({preventScroll: true});
                            field.select();
                            copied = document.execCommand('copy');
                        } catch (_) {
                            copied = false;
                        } finally {
                            field.remove();
                            if (focused && focused.isConnected) focused.focus({preventScroll: true});
                        }
                    }
                    const message = copied ? 'Copied to clipboard.' : 'Could not copy to clipboard.';
                    dash_clientside.set_props(statusId, {children: message});
                    button.removeAttribute('title');
                    button.classList.toggle('is-copied', copied);
                    button.classList.toggle('is-copy-failed', !copied);
                    clearTimeout(button.__copyResetTimer);
                    button.__copyResetTimer = setTimeout(function() {
                        if (button.isConnected) button.classList.remove('is-copied', 'is-copy-failed');
                    }, 1500);
                };
                document.addEventListener('click', window.__ai4cpsClipboardListener);
            }
            return '';
        },
        alarm: async function(nClicks, config) {
            const unchanged = Array(4).fill(dash_clientside.no_update);
            const buttonState = (enabled, label) => [
                enabled ? "fa-solid fa-volume-high" : "fa-solid fa-volume-xmark",
                enabled ? "true" : "false", label, label
            ];
            if (!config || !document.getElementById(config.buttonId)) {
                return unchanged;
            }

            const alarms = window.__ai4cpsAlarms ||= new Map();
            let alarm = alarms.get(config.buttonId);
            if (!alarm) {
                alarm = {
                    enabled: false, active: false, context: null, overlay: null,
                    buttonId: config.buttonId, overlayId: config.overlayId, voices: new Set()
                };
                alarm.stopTones = function() {
                    for (const voice of alarm.voices) {
                        voice.stop();
                    }
                    alarm.voices.clear();
                };
                alarm.beep = function(event) {
                    if (event.animationName !== "fa-fade" || event.target !== alarm.overlay ||
                        !alarm.enabled || !alarm.active || document.hidden ||
                        !alarm.overlay.isConnected || !document.getElementById(alarm.buttonId) ||
                        !alarm.context || alarm.context.state !== "running") {
                        return;
                    }
                    const now = alarm.context.currentTime;
                    const oscillator = alarm.context.createOscillator();
                    const gain = alarm.context.createGain();
                    oscillator.type = "sine";
                    oscillator.frequency.setValueAtTime(520, now);
                    gain.gain.setValueAtTime(0, now);
                    gain.gain.linearRampToValueAtTime(0.035, now + 0.03);
                    gain.gain.linearRampToValueAtTime(0, now + 0.18);
                    oscillator.connect(gain);
                    gain.connect(alarm.context.destination);
                    alarm.voices.add(oscillator);
                    oscillator.onended = function() {
                        alarm.voices.delete(oscillator);
                        oscillator.disconnect();
                        gain.disconnect();
                    };
                    oscillator.start(now);
                    oscillator.stop(now + 0.19);
                };
                alarm.cleanup = function() {
                    alarm.enabled = false;
                    alarm.stopTones();
                    if (alarm.overlay) {
                        alarm.overlay.removeEventListener("animationiteration", alarm.beep);
                    }
                    alarm.observer.disconnect();
                    if (alarm.context && alarm.context.state !== "closed") {
                        alarm.context.close().catch(function() {});
                    }
                    alarms.delete(alarm.buttonId);
                };
                alarm.bindOverlay = function() {
                    if (!document.getElementById(alarm.buttonId)) {
                        alarm.cleanup();
                        return;
                    }
                    const overlay = document.getElementById(alarm.overlayId);
                    if (overlay !== alarm.overlay) {
                        alarm.stopTones();
                        if (alarm.overlay) {
                            alarm.overlay.removeEventListener("animationiteration", alarm.beep);
                        }
                        alarm.overlay = overlay;
                        if (overlay) {
                            // CSS animation events keep the tone in phase with the warning marks.
                            overlay.addEventListener("animationiteration", alarm.beep);
                        }
                    }
                };
                alarm.observer = new MutationObserver(alarm.bindOverlay);
                alarm.observer.observe(document.body, {childList: true, subtree: true});
                alarms.set(config.buttonId, alarm);
            }

            alarm.active = Boolean(config.active);
            alarm.overlayId = config.overlayId;
            alarm.bindOverlay();
            if (!alarm.active) {
                alarm.stopTones();
            }
            const clicked = (dash_clientside.callback_context.triggered || []).some(
                item => item.prop_id === config.buttonId + ".n_clicks"
            );
            if (clicked && nClicks > 0) {
                alarm.enabled = !alarm.enabled;
                if (alarm.enabled) {
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (!AudioContext) {
                        alarm.enabled = false;
                        return buttonState(false, "Sound unavailable");
                    }
                    try {
                        alarm.context ||= new AudioContext();
                        await alarm.context.resume();
                        if (alarm.context.state !== "running") {
                            alarm.enabled = false;
                        }
                    } catch (error) {
                        alarm.enabled = false;
                    }
                } else {
                    alarm.stopTones();
                }
            }
            if (alarms.get(config.buttonId) !== alarm) {
                return unchanged;
            }
            return buttonState(alarm.enabled, alarm.enabled ? "Mute alarm sound" : "Unmute alarm sound");
        }
    })
});
