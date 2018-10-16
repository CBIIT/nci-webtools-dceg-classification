// disables an element and updates its aria-disabled attribute
$.fn.disable = function() {
    $(this).prop('disabled', true).attr('aria-disabled', true);
}

// enables an element and updates its aria-disabled attribute
$.fn.enable = function() {
    $(this).prop('disabled', false).attr('aria-disabled', false);
}

$(function () {

    reset();
    // Resets the application (does not clear file input or model version)
    function reset() {
        $('#loading').hide();
        $('#submit').enable();
        $('#upload').enable();
        $('#cancel').enable();
        $('#alerts').html('');
        $('#secondary-alerts').html('');
        $('#email').val('');
        $('#file-id').val('');
        $('#email-container').hide();
        $('#email').prop('required', false);
        $('#submit-container').hide();
        $('#results-container').hide();
        $('#upload-progress').parent().hide();
        setProgress(0, '#upload-progress');
        return false;
    }

    // check if we have results
    var query = parseQueryString(location.search);
    if (query.id) {
        showResults(query.id);
        $('#soccer-tab').tab('show');
    };

    // Resets the form when the user clicks the cancel button
    $('#cancel').click(function() {
        $('#input-file').val('').change();
        reset();
    });

    // Updates the input file's description when a new file is selected
    $('#input-file').change(function (e) {
        reset();
        $('#input-file-description').text('');
        if (!this.files || !this.files.length) return;

        var file = this.files[0];
        var description = [
            'File Name: ' + file.name,
            'File Size: ' + humanReadableBytes(file.size)
        ].join('; ');

        $('#input-file-description').text(description);
    });

    // resets the application if the model version changes
    $('#model-version').change(reset);


    /**
     * When the user uploads an input file, attempt to validate it on the server.
     * If successful, we receive an object containing the keys:
     *   - estimated_runtime - the estimated time to run the model
     *   - file_id - a file id used to run the model and to retrieve results
     */
    $('#upload').click(function (e) {
        // do not proceed if there are no input files
        if (!$('#input-file').val()) return;

        // reset the form (excluding file inputs)
        reset();

        $('#upload-progress')
            .addClass('progress-bar-animated')
            .parent().show();

        $.post({
            url: 'validate',
            data: new FormData($('#soccer-form')[0]),
            processData: false,
            contentType: false,
            xhr: function() {
                var xhr = $.ajaxSettings.xhr();
                xhr.upload.addEventListener('progress', function(e) {
                    setProgress(Math.floor(100 * e.loaded / e.total));
                }, false);
                return xhr;
            }
        }).done(function (response) {
            $('#file-id').val(response.file_id);

            showAlert('alert-success', 'Your file has been uploaded successfully.');

            if (response.estimated_runtime > 30) {
                // if the calculation is estimated to take more than 30 seconds, then we should ask the user to enter their email
                $('#email-container').show();
                $('#email').prop('required', true);
                showAlert('alert-success', 'Since it will likely take longer than 30 seconds to process your data, please provide your email address, and you will get an email notification once the processing is complete.');
            }

            $('#submit-container').show();
            $('#upload').disable();
        }).fail(function (error) {
            console.log(error);

            // display validation errors
            var alertText = $('<div/>')
                .append($('<p class="font-weight-bold"/>')
                    .text('Your file has been uploaded successfully but contains the following errors:')
                ).append($('<ul>').append(
                    error.responseJSON.trim().split('\n').map(function(line) {
                        return $('<li>').text(line);
                    })
                )).append($('<p class="font-weight-bold"/>')
                    .text('Please modify your data file and re-upload.'));

            showAlert('alert-warning', alertText, '#secondary-alerts');
        }).always(function() {
            $('#upload-progress').removeClass('progress-bar-animated');
        });
    });

    $('#submit').click(function(e) {
        var form = $('#soccer-form')[0];

        // do not proceed if the form is invalid
        if (!form.checkValidity()) return;

        // determine if we should use 'enqueue' or 'code-file'
        var action = $('#email').val() ? 'enqueue' : 'code-file';

        $('#submit-container').hide();
        $('#loading').show();

        $.post({
            url: action,
            data: new FormData(form),
            processData: false,
            contentType: false,
        }).done(function(response) {
            showAlert('alert-success', 'Your file has been processed successfully.');
            showResults(response);
        }).fail(function(error) {
            console.log(error);
            showAlert('alert-warning', 'Processing has failed due to an unspecified error. Please contact <a href="mailto:NCISOCcerWebAdmin@mail.nih.gov">NCISOCcerWebAdmin@mail.nih.gov</a> if this problem persists.');
        }).always(function() {
            $('#loading').hide();
        });
    })

    // disable default form submission when any button is clicked
    $('#soccer-form').submit(function (e) { return false });

    /**
     * Shows calculation results (sets attributes for graph/download link)
     * @param {string} id A file id containing the results
     */
    function showResults(id) {
        $('#results-container').hide();
        $.getJSON('results/' + id).done(function (results) {
            $('#results-container').show();
            $('#plot').attr('src', results.plot_url);
            $('#download-link').attr('href', results.output_url);
        });
    }

    /**
     * Shows a bootstrap alert within the specified container (default: #alerts)
     *
     * @param {string} type The type of alert (bootstrap class name)
     * @param {string} message The message to display within the alert
     * @param {string | Node} container The alert's container
     */
    function showAlert(type, message, container) {
        $(container || '#alerts').append(
            $('<div class="alert"/>')
                .css('white-space', 'pre-line')
                .addClass(type)
                .html(message)
        );
    }

    /**
     * Sets a progress indicator's text and width
     * @param {number} value The numeric value of the indicator (0-100)
     * @param {string | Node} container The progress indicator's selector
     */
    function setProgress(value, container) {
        return $(container || '#upload-progress')
            .text(value + '%')
            .attr('aria-value-now', value)
            .css('width', value + '%');
    }

    /**
     * Converts a number of bytes to a human-readable string
     * @param {number} bytes
     * @example humanReadableBytes(2048) returns "2 KiB"
     */
    function humanReadableBytes(bytes) {
        var exponent = Math.floor(Math.log(+bytes) / Math.log(1024));
        var result = +(bytes / Math.pow(1024, exponent)).toFixed(2);
        var units = ['B', 'KiB', 'MiB', 'GiB'];
        return result + ' ' + units[exponent];
    }

    /**
     * Parses a query string as a plain object
     * @param {string} query A query string (eg: the value of `location.search`)
     */
    function parseQueryString(query) {
        if (query[0] === '?') query = query.substr(1);
        return query.split('&').reduce(function(parsed, current) {
            var pair = current.split('=').map(decodeURIComponent);
            parsed[pair[0]] = pair[1];
            return parsed;
        }, {});
    }

    // enables bootstrap popovers
    $('[data-toggle="popover"]').popover();

    // enables us to switch tabs by clicking on [data-tab] links
    $('[data-tab]').click(function (e) {
        e.preventDefault();
        var tabSelector = $(this).attr('data-tab');
        $(tabSelector).tab('show');
    });
})