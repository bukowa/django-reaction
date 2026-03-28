'use strict';
(function () {
    function setup() {
        const form = document.querySelector('#content form:not(#logout-form), #changelist-form');
        if (!form || form.hasAttribute('x-data')) return;

        const state = {};

        form.querySelectorAll('input[name], select[name], textarea[name]').forEach(el => {
            if (el.name === 'csrfmiddlewaretoken') return;

            if (el.type === 'radio') {
                if (!state.hasOwnProperty(el.name)) {
                    state[el.name] = null;
                }
                if (el.checked) {
                    state[el.name] = el.value;
                }

            } else if (el.type === 'checkbox') {
                const isMultiple = form.querySelectorAll(`input[type="checkbox"][name="${el.name}"]`).length > 1;

                if (isMultiple) {
                    if (!state.hasOwnProperty(el.name)) {
                        state[el.name] = [];
                    }
                    if (el.checked) {
                        state[el.name].push(el.value);
                    }
                } else {
                    state[el.name] = el.checked;
                }

            } else if (el.type === 'select-multiple') {
                state[el.name] = Array.from(el.selectedOptions).map(opt => opt.value);

            } else {
                state[el.name] = el.value;
            }
        });

        form.setAttribute('x-data', JSON.stringify(state));
        console.log('Alpine Reaction initialized successfully with state:', state);
    }

    setup();
    document.addEventListener('formset:added', setup);
})();