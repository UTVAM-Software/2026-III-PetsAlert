
(function () {
    function leerCookie(nombre) {
        const partes = document.cookie ? document.cookie.split(';') : [];

        for (const parte of partes) {
            const cookie = parte.trim();

            if (cookie.startsWith(nombre + '=')) {
                return decodeURIComponent(cookie.substring(nombre.length + 1));
            }
        }

        return null;
    }

    function escaparHtml(texto) {
        return String(texto ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function mensajeDeError(datos, estado) {
        if (datos && typeof datos === 'object') {
            if (typeof datos.detail === 'string') {
                return datos.detail;
            }

            const mensajes = Object.values(datos)
                .flat()
                .filter(valor => typeof valor === 'string');

            if (mensajes.length > 0) {
                return mensajes.join(' ');
            }
        }

        if (estado === 401 || estado === 403) {
            return 'No tienes permiso para realizar esta acción.';
        }

        return 'Ocurrió un error. Inténtalo de nuevo.';
    }

    async function api(url, { method = 'GET', body = null, formData = null } = {}) {
        const headers = { 'Accept': 'application/json' };
        const opciones = { method, headers, credentials: 'same-origin' };

        if (method !== 'GET' && method !== 'HEAD') {
            headers['X-CSRFToken'] = leerCookie('csrftoken') || '';
        }

        if (formData) {

            opciones.body = formData;
        } else if (body !== null) {
            headers['Content-Type'] = 'application/json';
            opciones.body = JSON.stringify(body);
        }

        const respuesta = await fetch(url, opciones);

        let datos = null;

        if (respuesta.status !== 204) {
            try {
                datos = await respuesta.json();
            } catch (error) {
                datos = null;
            }
        }

        if (!respuesta.ok) {
            const error = new Error(mensajeDeError(datos, respuesta.status));
            error.status = respuesta.status;
            error.datos = datos;
            throw error;
        }

        return datos;
    }

    window.PetsAlert = { api, escaparHtml };
})();
