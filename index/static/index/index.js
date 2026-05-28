document.addEventListener("DOMContentLoaded", () => {
    const bindClick = (selector, handler) => {
        try {
            const element = document.querySelector(selector);
            if (!element) return;
            element.addEventListener("click", handler);
        } catch (error) {
            console.error(`Error inicializando ${selector}:`, error);
        }
    };

    bindClick("#create-blank-form", () => {
        const csrf = Cookies.get('csrftoken');
        fetch(`${window.APP_URL_PREFIX}/form/create`, {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({
                title: "Formulario en Blanco"
            })
        })
            .then(response => response.json())
            .then(result => {
                window.location = `${window.APP_URL_PREFIX}/form/${result.code}/edit`
            })
    });

    bindClick("#create-contact-form", () => {
        const csrf = Cookies.get('csrftoken');
        fetch(`${window.APP_URL_PREFIX}/form/create/contact`, {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({})
        })
            .then(response => response.json())
            .then(result => {
                window.location = `${window.APP_URL_PREFIX}/form/${result.code}/edit`
            })
    });

    bindClick("#create-customer-feedback", () => {
        const csrf = Cookies.get('csrftoken');
        fetch(`${window.APP_URL_PREFIX}/form/create/feedback`, {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({})
        })
            .then(response => response.json())
            .then(result => {
                window.location = `${window.APP_URL_PREFIX}/form/${result.code}/edit`
            })
    });

    bindClick("#create-event-registration", () => {
        const csrf = Cookies.get('csrftoken');
        fetch(`${window.APP_URL_PREFIX}/form/create/event`, {
            method: "POST",
            headers: {'X-CSRFToken': csrf},
            body: JSON.stringify({})
        })
            .then(response => response.json())
            .then(result => {
                window.location = `${window.APP_URL_PREFIX}/form/${result.code}/edit`
            })
    });
});