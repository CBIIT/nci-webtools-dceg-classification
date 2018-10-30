(function() {
    window.dataLayer = window.dataLayer || [];
    var GA_TRACKING_ID = 'UA-62346354-5';
    function gtag() { dataLayer.push(arguments); }

    gtag('js', new Date());
    gtag('config', GA_TRACKING_ID);

    function registerAnalytics() {
        // adobe DAP snippet
        _satellite.pageBottom();

        // register bootstrap tabs as separate pages
        $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
            var page = e.target.id
            gtag('config', GA_TRACKING_ID, {
                'page_title' : page,
                'page_path': '/#' + e.target
            });
        }
    }

    document.addEventListener('DOMContentLoaded', registerAnalytics);
});
