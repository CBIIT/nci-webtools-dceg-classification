/**
 * @file Contains soccer form handlers
 * @namespace soccer
 */

$(function () {
  /** Show results if the location's query parameters contain an id */
  var query = parseQuery(location.search);
  if (query.id) showResults(query.id);

  /** Begin Attaching Event Handlers */

  /** Override form submit */
  $('#soccer-form').submit(submit);

  /** Attach reset handler without overriding default reset behavior */
  $('#soccer-form :reset').click(reset);

  /** Upload and validate input file on changes */
  $('#input-file').change(upload);

  /** Enable email input if #submit-queue is checked */
  $('#submit-queue').change(function (e) {
    var checked = $(this).prop('checked');
    $('#email').attr('required', checked).disabled(!checked);
  });

  /** End Attaching Event Handlers */

  /**
   * Resets the SOCcer input form
   * @param {ResetEvent} e - The original reset event
   * @memberof soccer
   */
  function reset(e) {
    var form = $('#soccer-form').get(0);
    form.reset();

    // enable inputs, disable submit
    $(form).find(':input').enable().find(':submit').disable();

    // by default, we should not submit to the queue
    $('#submit-queue').prop('checked', false).change();

    // reset file upload progress indicator
    $('#upload-progress').progress(0).parent().hide();

    $('#loading').hide(); // loading indicator
    $('#alerts').empty(); // alerts container
    $('#results').hide(); // results container

    // email help text
    $('#email-help').text(
      'If this job is submitted to the queue, a notification will be sent to your email address once processing is complete.'
    );

    // clear query parameters if they exist
    if (location.search) history.pushState(null, null, location.pathname);

    return false;
  }

  /**
   * When the user uploads an input file, attempt to validate it on the server.
   * If successful, we receive an object containing the keys:
   *   - estimated_runtime - the estimated runtime for the model
   *   - file_id - the file id used to run the model and to retrieve results
   *
   * Otherwise, we obtain a list of validation errors which are displayed
   * in '#secondary-alerts'
   * @memberof soccer
   */
  function upload(e) {
    // do not proceed if no input files are selected
    if ($('#input-file').prop('files').length == 0) return;

    // clear all alerts and results
    $('#alerts').html('');
    $('#results').hide();

    // show upload progress animation
    $('#upload-progress').addClass('progress-bar-animated').parent().show();

    $.post({
      url: 'validate',
      data: $('#soccer-form').formData(),
      processData: false,
      contentType: false,
      xhr: function () {
        // add progress listener
        var xhr = $.ajaxSettings.xhr();
        xhr.upload.addEventListener(
          'progress',
          function (e) {
            $('#upload-progress').progress(
              Math.floor((100 * e.loaded) / e.total)
            );
          },
          false
        );
        return xhr;
      },
    })
      .done(function (response) {
        // disable modifying inputs after file is validated
        $('#input-file').disable();
        $('#model-version').disable();
        $('#soccer-form :submit').enable();

        // update the file id
        $('#file-id').val(response.file_id);
        if (response.estimated_runtime > 30) {
          // if the calculation is estimated to take more than 30 seconds, then we should enqueue the file when submitted
          $('#submit-queue').prop('checked', true).change().disable();
          $('#email-help').text(
            'Since it will likely take longer than 30 seconds to process your data, please provide your email address and you will get a notification once processing is complete.'
          );
        }

        // display success alert (screenreader only)
        $('#alerts').alert(
          'alert-success sr-only',
          'Your file was uploaded successfully.'
        );
      })
      .fail(function (error) {
        $('#soccer-form :submit').disable();
        console.log(error);

        if (!error.status) {
          $('#alerts').alert(
            'alert-danger',
            'An error occurred while uploading your file. Please contact <a href="mailto:NCISOCcerWebAdmin@mail.nih.gov">NCI&shy;SOCcer&shy;Web&shy;Admin@mail.nih.gov</a> if this problem persists.'
          );
          return;
        }

        // determine error text
        var errorText = error.responseJSON.trim();

        // handle error codes
        if (errorText.length <= 4) errorText = 'Invalid file format.';

        // create error list
        var errorList = $('<ul>');
        errorText.split(/\r?\n/).forEach(function (line) {
          errorList.append($('<li>').text(line));
        });

        // display validation errors
        $('#alerts').alert(
          'alert-warning',
          $('<div/>')
            .append(
              '<p><b>Your file could not be uploaded due to the following errors:</b></p>'
            )
            .append(errorList)
            .append('<p><b>Please modify your data file and re-upload.</b></p>')
        );
      })
      .always(function () {
        // only animate progress bar while uploading
        $('#upload-progress').removeClass('progress-bar-animated');
      });
  }

  /**
   * Submits a file for processing
   * @memberof soccer
   */
  function submit() {
    // do not proceed if the form is invalid
    if (!$('#soccer-form')[0].checkValidity()) return false;

    $('#alerts').html('');
    $('#soccer-form :input').disable();
    $('#loading').delay(200).fadeIn(100); // IE does not .show properly when .disable is also in progress

    // determine if we should 'submit' or 'submit/queue'
    var action = $('#submit-queue').prop('checked') ? 'submit-queue' : 'submit';

    var formData = $('#soccer-form').formData();
    formData.append('url_root', location.protocol + '//' + location.host);

    $.post({
      url: action,
      data: formData,
      processData: false,
      contentType: false,
    })
      .done(function (response) {
        if (action === 'submit') showResults(response.file_id);
        else if (action === 'submit-queue')
          $('#alerts').alert(
            'alert-success',
            'Your results will be emailed to you.'
          );
      })
      .fail(function (error) {
        console.log(error);
        $('#alerts').alert(
          'alert-danger',
          'Your request could not be processed due to an internal error. Please contact <a href="mailto:NCISOCcerWebAdmin@mail.nih.gov">NCI&shy;SOCcer&shy;Web&shy;Admin@mail.nih.gov</a> if this problem persists.'
        );
      })
      .always(function () {
        $('#soccer-form :reset').enable();
        $('#loading').fadeOut(100);
      });

    return false;
  }

  /**
   * Shows calculation results (sets attributes for plot/download link)
   * @param {string} id A file id containing the results
   * @memberof soccer
   */
  function showResults(id) {
    $('#results').hide();

    return $.getJSON('results/{0}.json'.format(id))
      .done(function (results) {
        $('#download-link').attr('href', 'results/{0}.csv'.format(id));
        $('#plot').attr('src', 'results/{0}.png'.format(id));
        $('#model-version').val(results.model_version);
        $('#results').show();
      })
      .fail(function (error) {
        console.log(error);
        $('#soccer-form').trigger('reset');
        $('#alerts').alert(
          'alert-danger',
          'Results could not be found for the specified id. Please contact <a href="mailto:NCISOCcerWebAdmin@mail.nih.gov">NCI&shy;SOCcer&shy;Web&shy;Admin@mail.nih.gov</a> for assistance.'
        );
      })
      .always(function () {
        $('#soccer-tab').tab('show');
        $('#soccer-form :input').disable();
        $('#soccer-form :reset').enable();
      });
  }

  window.downloadJNLP = function () {
    var contents = [
      '<?xml version="1.0" encoding="utf-8"?>',
      '<jnlp spec="1.0+" codebase="{codebase}">',
      '    <information>',
      '           <title>SOCAssign</title>',
      '           <vendor>NCI CBIIT</vendor>',
      '           <homepage href="{codebase}" />',
      '           <description>SOCAssign Application</description>',
      '    </information>',
      '    <security>',
      '           <all-permissions/>',
      '    </security>',
      '    <resources>',
      '          <j2se version="1.7+" />',
      '          <jar href="{jarHref}" />',
      '    </resources>',
      '    <application-desc main-class="gov.nih.cit.socassign.SOCAssign" />',
      '</jnlp>',
    ]
      .join('\n')
      .format({
        codebase: location.protocol + '//' + location.host,
        jarHref: 'soccer/static/files/SOCAssign.jar',
      });
    var blob = new Blob([contents], { type: 'text/plain;charset=utf-8' });
    saveAs(blob, 'SOCAssign.jnlp');
  };

  /**
   * Parses a query string as an object
   * @param {string} query A query string (eg: the value of `location.search`)
   * @returns {object} An object containing query parameters
   * @memberof soccer
   */
  function parseQuery(query) {
    // strip leading question mark
    if (query[0] === '?') query = query.substr(1);
    return query.split('&').reduce(function (parsed, current) {
      // iterate over each key-value pair in the query string
      var pair = current.split('=').map(decodeURIComponent);
      parsed[pair[0]] = pair[1];
      return parsed;
    }, {});
  }
});
