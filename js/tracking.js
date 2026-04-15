(function () {
    const measurementId = window.GA_MEASUREMENT_ID;

    window.tracking = {
        enabled: Boolean(measurementId),
        track(eventName, params = {}) {
            if (!measurementId || typeof window.gtag !== 'function') {
                return;
            }

            window.gtag('event', eventName, params);
        }
    };

    if (!measurementId) {
        return;
    }

    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
        window.dataLayer.push(arguments);
    };

    window.gtag('js', new Date());
    window.gtag('config', measurementId, {
        send_page_view: true
    });
})();
