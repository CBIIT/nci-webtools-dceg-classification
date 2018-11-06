/**
 * Disables an element and updates its aria-disabled attribute
 */
$.fn.disable = function () {
    return $(this)
        .prop('disabled', true)
        .attr('aria-disabled', true);
}

/**
 * Enables an element and updates its aria-disabled attribute
 */
$.fn.enable = function () {
    return $(this)
        .prop('disabled', false)
        .attr('aria-disabled', false);
}

/**
 * Sets a progress indicator's text, aria-value, and width
 * @param {number} value The numeric value of the indicator (0-100)
 */
$.fn.setProgress = function (value) {
    return $(this)
        .text(value + '%')
        .attr('aria-valuenow', value)
        .css('width', value + '%');
}

/**
 * Shows a bootstrap alert in the specified container
 * @param {string} type The type of alert (bootstrap class name)
 * @param {string} message The message to display within the alert
 */
$.fn.showAlert = function (type, message) {
    return $(this).append(
        $('<div class="alert" role="alert"/>')
            .addClass(type)
            .html(message)
    );
}

/**
 * Creates a FormData object from a form (which includes disabled elements)
 */
$.fn.formData = function () {
    var formData = new FormData();
    $(this).find('input, textarea, select').each(function (index, el) {
        if (el.files) formData.append(el.name, el.files[0]);
        else formData.append(el.name, el.value);
    });
    return formData;
}

$(function () {

    // handle form reset events (triggered by clicking [type="reset"])
    $('#soccer-form').on('reset', function () {
        // file input (accept only csv)
        $('#input-file').val('').enable().change();

        // model version selector (default: model version 2)
        $('#model-version').val('2').enable();

        // email input (only visible when queueing)
        $('#submit-queue').prop('checked', false).enable();
        $('#email').val('').enable().prop('required', false);

        // input file id (internal, hidden)
        $('#file-id').val('');

        // upload progress indicator (bootstrap)
        $('#upload-progress').setProgress(0).parent().hide();

        // submit button
        $('#submit').show().disable();

        // reset button
        $('#reset').enable();

        // loading indicator (replaces submit when processing)
        $('#loading').hide();

        // results container in right panel
        $('#results-container').hide();

        // alerts container
        $('#alerts').html('');

        $('#queue-description').text('Note: If this job is submitted to the queue, a notification will be sent to your email address once processing is complete.');

        return false;
    }).trigger('reset'); // reset form on startup

    // disable default form submission
    $('#soccer-form').submit(function (e) { return false });

    // if we have a file id in the url, fetch and show the results
    var query = parseQueryString(location.search);
    if (query.id) {
        showResults(query.id);
        $('#soccer-tab').tab('show');
        $('#upload').disable();
        $('#model-version').disable();
        $('#input-file').disable();
    }

    // update the input file's description when a new file is selected
    $('#input-file').change(function (e) {
        updateDescription();
        uploadFile();
    });

    $('#submit-queue').change(function(e) {
        var emailRequired = $(this).prop('checked');
        $('#email')
            .prop('required', emailRequired)
            .prop('readonly', !emailRequired);
    }).change();

    $('#submit').click(function (e) {
        submitFile();
    });

    function updateDescription() {
        $('#input-file-description').text('');
        $('#upload-progress').setProgress(0);
        if (!this.files || !this.files.length) return;

        var file = this.files[0];
        var description = [
            'File Name: ' + file.name,
            'File Size: ' + humanReadableBytes(file.size)
        ].join('; ');

        $('#input-file-description').text(description);
    }

    /**
     * When the user uploads an input file, attempt to validate it on the server.
     * If successful, we receive an object containing the keys:
     *   - estimated_runtime - the estimated runtime for the model
     *   - file_id - the file id used to run the model and to retrieve results
     *
     * Otherwise, we obtain a list of validation errors which are displayed
     * in '#secondary-alerts'
     */
    function uploadFile (e) {
        // do not proceed if there are no input files
        if (!$('#input-file').val()) return;

        // clear all alerts and results when starting file upload
        $('#alerts').html('');
        $('#results-container').hide();

        // disable upload button and show upload progress animation
        $('#upload').disable();
        $('#upload-progress')
            .addClass('progress-bar-animated')
            .parent().show();

        $.post({
            url: 'validate',
            data: $('#soccer-form').formData(),
            processData: false,
            contentType: false,
            xhr: function () {
                var xhr = $.ajaxSettings.xhr();
                xhr.upload.addEventListener('progress', function (e) {
                    $('#upload-progress').setProgress(
                        Math.floor(100 * e.loaded / e.total)
                    );
                }, false);
                return xhr;
            }
        }).done(function (response) {
            // disable modifying input parameters after the file is validated
            $('#input-file').disable();
            $('#model-version').disable();

            // update the file id
            $('#file-id').val(response.file_id);

            $('#submit').enable();

            if (response.estimated_runtime > 30) {
                // if the calculation is estimated to take more than 30 seconds, then we should enqueue the file when submitted
                $('#email').prop('required', true);
                $('#submit-queue').prop('checked', true).change().disable();
                $('#queue-description').text('Note: Since it will likely take longer than 30 seconds to process your data, please provide your email address and you will get an email notification once processing is complete.');
            }
        }).fail(function (error) {
            $('#upload').enable();
            console.log(error);

            if (!error.status) {
                $('#alerts').showAlert('alert-warning', 'An error occurred while uploading your file. Please ensure the file is not currently in use.');
                return;
            }

            // determine error text
            var errorText = error.responseJSON.trim();

            // handle error codes
            if (errorText.length <= 4)
                errorText = 'Invalid file header';

            // map errors to an unordered list
            var errorList = $('<ul>').append(
                errorText.split(/\r?\n/).map(function (line) {
                    return $('<li>').text(line);
                })
            );

            // display validation errors
            $('#alerts').showAlert('alert-warning',
                $('<div/>')
                    .append('<p><b>Your file has been uploaded successfully but contains the following errors:</b></p>')
                    .append(errorList)
                    .append('<p><b>Please modify your data file and re-upload.</b></p>')
            );
        }).always(function () {
            // only animate progress bar while uploading
            $('#upload-progress').removeClass('progress-bar-animated');
        });
    }

    function submitFile() {

        // do not proceed if the form is invalid
        if (!$('#soccer-form')[0].checkValidity()) return;

        // determine if we should use 'enqueue' or 'code-file'
        var action = $('#submit-queue').prop('checked')
            ? 'enqueue'
            : 'code-file';

        $('#submit').hide();
        $('#loading').show();
        $('#reset').disable();

        $.post({
            url: action,
            data: $('#soccer-form').formData(),
            processData: false,
            contentType: false,
        }).done(function (response) {
            if (action === 'code-file') {
                showResults(response);
            } else {
                $('#email').disable();
                $('#alerts').showAlert('alert-success', 'Your file has been enqueued successfully.');
            }
        }).fail(function (error) {
            console.log(error);
            $('#alerts').showAlert('alert-warning', 'Your request could not be processed due to an internal error. Please contact <a href="mailto:NCISOCcerWebAdmin@mail.nih.gov">NCI&shy;SOCcer&shy;Web&shy;Admin@mail.nih.gov</a> if this problem persists.');
        }).always(function () {
            $('#reset').enable();
            $('#loading').hide();
        });
    }

    /**
     * Shows calculation results (sets attributes for plot/download link)
     * @param {string} id A file id containing the results
     */
    function showResults(id) {
        $('#results-container').hide();
        $.getJSON('results/' + id).done(function (results) {
            $('#plot').attr('src', results.plot_url);
            $('#download-link').attr('href', results.output_url);
            $('#results-container').show();
        }).fail(function (error) {
            console.log(error);
            $('#soccer-form').trigger('reset');
            $('#alerts').showAlert('alert-warning', 'We were unable to retrieve results for the specified file id.');
        });
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
        // strip leading question mark
        if (query[0] === '?') query = query.substr(1);
        return query.split('&').reduce(function (parsed, current) {
            // iterate over each key-value pair in the query string
            var pair = current.split('=').map(decodeURIComponent);
            parsed[pair[0]] = pair[1];
            return parsed;
        }, {});
    }

    // enables bootstrap popovers
    $('[data-toggle="popover"]').popover();

    // allows us to switch tabs by clicking on [data-tab] links
    $('[data-tab]').click(function (e) {
        e.preventDefault();
        var tabSelector = $(this).attr('data-tab');
        $(tabSelector).tab('show');
    });
})