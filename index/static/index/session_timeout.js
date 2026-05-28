(function() {
    if (!window.IS_AUTHENTICATED) return;

    let timeout;
    const idleTime = (window.SESSION_TIMEOUT || 3600) * 1000;

    function logout() {
        console.log("Sesión expirada por inactividad. Redirigiendo...");
        window.location.href = `${window.APP_URL_PREFIX}/logout`;
    }

    function resetTimer() {
        clearTimeout(timeout);
        timeout = setTimeout(logout, idleTime);
    }

    // Eventos que reinician el contador de inactividad
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    
    events.forEach(name => {
        document.addEventListener(name, resetTimer, true);
    });

    // Inicializar el temporizador
    resetTimer();
})();
