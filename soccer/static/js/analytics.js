(function() {
    window.dataLayer = window.dataLayer || [];
    var GA_TRACKING_ID = 'UA-62346354-5';
    function gtag() { dataLayer.push(arguments); }

    gtag('js', new Date());
    gtag('config', GA_TRACKING_ID);

    // adobe DAP snippet
    document.addEventListener('DOMContentLoaded', function() {
        _satellite.pageBottom();
    });
});
