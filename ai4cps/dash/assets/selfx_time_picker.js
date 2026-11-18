(function () {
    'use strict';
    let picker = null;
    const pad = value => String(value).padStart(2, '0');

    function close(restoreFocus) {
        if (!picker) return;
        const input = picker.input;
        picker.dialog.remove();
        picker = null;
        if (restoreFocus && input.isConnected) input.focus({preventScroll: true});
    }

    function position() {
        if (!picker) return;
        const {input, dialog} = picker;
        if (!input.isConnected || input.disabled || input.readOnly) return close(false);
        const rect = input.getBoundingClientRect();
        const width = dialog.offsetWidth, height = dialog.offsetHeight;
        dialog.style.left = Math.max(8, Math.min(rect.left, innerWidth - width - 8)) + 'px';
        dialog.style.top = Math.max(8, rect.bottom + height + 8 <= innerHeight
            ? rect.bottom + 4 : rect.top - height - 4) + 'px';
    }

    function open(input) {
        if (input.disabled || input.readOnly) return;
        close(false);
        const seconds = input.value.split(':').length === 3 || Number(input.step || 60) < 60;
        const values = (input.value || '00:00:00').split(':').map(Number);
        while (values.length < 3) values.push(0);
        const dialog = document.createElement('div');
        dialog.className = 'selfx-time-picker';
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-label', 'Choose time');
        const columns = document.createElement('div');
        columns.className = 'selfx-time-columns';
        dialog.appendChild(columns);
        const done = document.createElement('button');
        done.type = 'button';
        done.textContent = 'Done';
        done.className = 'selfx-time-done';
        const state = {input, dialog, values};
        picker = state;
        const candidate = () => values.slice(0, seconds ? 3 : 2).map(pad).join(':');
        function validate() {
            const probe = input.cloneNode();
            probe.value = candidate();
            done.disabled = !probe.validity.valid;
        }
        ['Hours', 'Minutes', 'Seconds'].slice(0, seconds ? 3 : 2).forEach((label, part) => {
            const column = document.createElement('div');
            const heading = document.createElement('div');
            heading.className = 'selfx-time-heading';
            heading.textContent = label;
            const list = document.createElement('div');
            list.className = 'selfx-time-options';
            list.setAttribute('role', 'group');
            list.setAttribute('aria-label', label);
            column.append(heading, list);
            columns.appendChild(column);
            for (let value = 0; value < (part === 0 ? 24 : 60); value++) {
                const option = document.createElement('button');
                option.type = 'button';
                option.textContent = pad(value);
                option.className = 'selfx-time-option';
                option.setAttribute('aria-label', pad(value) + ' ' + label.toLowerCase());
                option.setAttribute('aria-pressed', String(value === values[part]));
                option.addEventListener('click', () => {
                    values[part] = value;
                    for (const item of list.children) item.setAttribute('aria-pressed', String(item === option));
                    validate();
                });
                option.addEventListener('keydown', event => {
                    const delta = event.key === 'ArrowDown' ? 1 : event.key === 'ArrowUp' ? -1 : 0;
                    if (!delta && event.key !== 'Home' && event.key !== 'End') return;
                    event.preventDefault();
                    const next = event.key === 'Home' ? 0 : event.key === 'End' ? list.children.length - 1
                        : (value + delta + list.children.length) % list.children.length;
                    list.children[next].focus();
                    list.children[next].click();
                });
                list.appendChild(option);
            }
        });
        done.addEventListener('click', () => {
            if (picker !== state || input.disabled || input.readOnly || !input.isConnected) return close(false);
            Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, candidate());
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
            close(true);
        });
        dialog.appendChild(done);
        document.body.appendChild(dialog);
        validate();
        position();
        for (const selected of dialog.querySelectorAll('[aria-pressed="true"]')) {
            selected.parentElement.scrollTop = selected.offsetTop - selected.parentElement.offsetTop
                - selected.parentElement.clientHeight / 2 + selected.offsetHeight / 2;
        }
        dialog.querySelector('[aria-pressed="true"]').focus({preventScroll: true});
    }

    function clockInput(event) {
        if (event.button !== 0) return null;
        const input = event.target;
        if (!(input instanceof HTMLInputElement) || input.type !== 'time' || input.disabled || input.readOnly) return null;
        const rect = input.getBoundingClientRect();
        const rtl = getComputedStyle(input).direction === 'rtl';
        return (rtl ? event.clientX <= rect.left + 28 : event.clientX >= rect.right - 28) ? input : null;
    }
    document.addEventListener('pointerdown', event => {
        const input = clockInput(event);
        if (input) {
            event.preventDefault();
            event.stopImmediatePropagation();
            if (picker && picker.input === input) close(true); else open(input);
        } else if (picker && !picker.dialog.contains(event.target)) close(false);
    }, true);
    document.addEventListener('click', event => {
        if (clockInput(event)) {
            event.preventDefault();
            event.stopImmediatePropagation();
        }
    }, true);
    document.addEventListener('keydown', event => {
        if (picker && event.key === 'Escape') { event.preventDefault(); close(true); }
        else if (event.target instanceof HTMLInputElement && event.target.type === 'time'
                 && event.altKey && event.key === 'ArrowDown') {
            event.preventDefault();
            open(event.target);
        }
    });
    document.addEventListener('focusin', event => {
        if (picker && event.target !== picker.input && !picker.dialog.contains(event.target)) close(false);
    });
    window.addEventListener('resize', position);
    window.addEventListener('scroll', position, true);
    new MutationObserver(position).observe(document.documentElement, {childList: true, subtree: true,
        attributes: true, attributeFilter: ['disabled', 'readonly']});
}());
