/**
 * @file Registers jQuery plugins
 * @namespace plugins
 */

(function registerPlugins ($) {

    /**
     * Creates a bootstrap alert in the specified container
     * @param {string} className - The type of alert (given by bootstrap class)
     * @param {(any[] | string | Element | JQuery)} html - The alert's contents
     * @returns {jQuery} The created alert
     * @memberof plugins
     * @example $('#container').alert('alert-success', 'Success!');
     */
    $.fn.alert = function (className, html) {
        return $('<div class="alert" role="alert"/>')
            .addClass(className)
            .html(html)
            .appendTo(this);
    }

    /**
     * Disables a jQuery collection using the (aria)-disabled attributes
     * @returns {jQuery} The original jQuery collection
     * @memberof plugins
     * @example $('#element').disable();
     */
    $.fn.disable = function () {
        return $(this)
            .prop('disabled', true)
            .attr('aria-disabled', true);
    }

    /**
     * Enables a jQuery collection using the (aria)-disabled attributes
     * @returns {jQuery} The original jQuery collection
     * @memberof plugins
     * @example $('#element').enable();
     */
    $.fn.enable = function () {
        return $(this)
            .prop('disabled', false)
            .attr('aria-disabled', false);
    }

    /**
     * Creates a FormData object from a form (includes disabled elements)
     * @returns {FormData} The FormData object
     * @memberof plugins
     * @example $('form').formData(); // FormData
     */
    $.fn.formData = function () {
        var formData = new FormData();
        $(this).find('input, textarea, select').each(function (index, el) {
            if (el.files) formData.append(el.name, el.files[0]);
            else formData.append(el.name, el.value);
        });
        return formData;
    }

    /**
     * Sets a bootstrap progress indicator's text, aria-value, and width
     * @param {number} value The numeric value of the indicator (0-100)
     * @returns {jQuery} The bootstrap progress indicator
     * @memberof plugins
     * @example $('#progress').progress(100);
     */
    $.fn.progress = function (value) {
        return $(this)
            .text(value + '%')
            .attr('aria-valuenow', value)
            .css('width', value + '%');
    }

    /** Enables bootstrap popovers */
    $('[data-toggle="popover"]').popover();

    /** Enables us to show tabs by clicking on [data-tab] links */
    $('[data-tab]').click(function (e) {
        e.preventDefault();
        var tabSelector = $(this).attr('data-tab');
        $(tabSelector).tab('show');
    });

    /** Updates descriptions for .custom-file elements on changes */
    $('.custom-file input[type="file"]').change(function (e) {
        var $label = $('[for="' + this.id + '"]');

        $label.text('Choose file');
        if (!this.files.length) return;

        var file = this.files[0];
        $label.text(
            file.name +
            ' (' + humanReadableBytes(file.size) + ')'
        );
    });

    /**
      * Converts a number of bytes to a human-readable string
      * @param {number} bytes
      * @example humanReadableBytes(2048) // "2 KiB"
      * @memberof plugins
      */
    function humanReadableBytes(bytes) {
        var base = 1024; // use 1000 for metric units
        var exponent = Math.floor(Math.log(+bytes) / Math.log(base));
        var result = +(bytes / Math.pow(base, exponent)).toFixed(2);
        var units = ['B', 'KiB', 'MiB', 'GiB'];
        return result + ' ' + units[exponent];
    }

})(window.jQuery);