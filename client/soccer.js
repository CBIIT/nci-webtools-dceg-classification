form.onsubmit = handleSubmit;
form.onreset = handleReset;
form.onchange = handleChange;

// load popovers
const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
const popoverList = [...popoverTriggerList].map((popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl));

// load results if id is available
const params = new URLSearchParams(location.search);
const id = params.get("id");
if (id) {
  bootstrap.Tab.getOrCreateInstance("#nav-soccer").show();
  loadResults(id);
}

/**
 * Submits the form
 * @param {Event} event
 */
async function handleSubmit(event) {
  event.preventDefault();
  const body = new FormData(event.target);

  // disable form after form data is collected
  form.fieldset.disabled = true;
  form.submitButton.disabled = true;
  form.resetButton.disabled = true;
  loader.hidden = false;

  try {
    const response = await fetch("/api/submit", { method: "POST", body });
    const results = await response.json();
    if (!response.ok) {
      throw new Error(results.error || results.detail?.map((d) => `${d.msg} [${d.loc.at(-1)}]`).join("\n") || JSON.stringify(results));
    }
    if (form.background.checked) {
      successAlert.hidden = false;
      successMessage.innerText = "Your results will be emailed to you.";
    } else {
      await loadResults(results.id);
    }
  } catch (error) {
    errorAlert.hidden = false;
    errorMessage.innerText = error.message;
  } finally {
    form.resetButton.disabled = false;
    loader.hidden = true;
  }
}

/**
 * Resets the form and clears results and errorAlert
 */
function handleReset() {
  if (id) history.pushState(null, null, window.location.pathname);
  form.fieldset.disabled = false;
  form.submitButton.disabled = false;
  form.resetButton.disabled = false;
  form.email.disabled = true;

  resultsPlot.src = "data:,";
  resultsFile.href = "data:,";
  results.hidden = true;
  errorAlert.hidden = true;
  errorMessage.innerText = "";
  successAlert.hidden = true;
  successMessage.innerText = "";
}

/**
 * Handles changes to the form
 */
async function handleChange() {
  const file = form.file.files && form.file.files[0];
  const model = form.model.value;

  if (file) {
    // validate file
    let errors = await getValidationErrors(file, model);
    if (errors.length) {
      errorAlert.hidden = false;
      errorMessage.innerText = errors.join("\n");
      form.submitButton.disabled = true;
    } else {
      errorAlert.hidden = true;
      errorMessage.innerText = "";
      form.submitButton.disabled = false;

      if (file.size > 10000) {
        // if file is larger than 10kb, use background mode (this is also enforced on the server)
        form.background.checked = true;
      }
    }
  }

  // disable email if background mode is disabled
  form.email.disabled = !form.background.checked;
}

/**
 * Loads results for the specified job id
 * @param {string} id
 */
async function loadResults(id) {
  form.fieldset.disabled = true;
  form.submitButton.disabled = true;
  form.resetButton.disabled = false;

  try {
    const paramsUrl = `/api/jobs/${id}/params.json`;
    const resultsFileUrl = `api/jobs/${id}/results.csv`;
    const resultsPlotUrl = `api/jobs/${id}/results.png`;

    const paramsResponse = await fetch(paramsUrl);
    const resultsFileResponse = await fetch(resultsFileUrl, { method: "HEAD" });
    const resultsPlotResponse = await fetch(resultsPlotUrl, { method: "HEAD" });

    // check if job exists
    if (!paramsResponse.ok || !resultsFileResponse.ok || !resultsPlotResponse.ok) {
      throw new Error("The specified job does not exist. Please submit a new job or try again later.");
    }

    // populate parameters
    const params = await paramsResponse.json();
    form.model.value = params.model;
    form.background.checked = params.background;
    form.email.value = params.email || "";

    // populate results
    resultsFile.href = resultsFileUrl;
    resultsPlot.src = resultsPlotUrl;
    resultsPlot.onload = () => (results.hidden = false);
  } catch (error) {
    errorAlert.hidden = false;
    errorMessage.innerText = error.message;
  }
}

/**
 * Returns an array of validation errors for the specified file and model
 * @param {File} file The file to validate
 * @param {string} model The model version to validate against
 * @returns {Promise<string[]>} An array of validation errors
 */
function getValidationErrors(file, model) {
  const modelV1Headers = ["jobtitle", "sic", "jobtask"];
  const modelV2Headers = ["id", "jobtitle", "sic", "jobtask"]; // v1 is backwards compatible with v2

  return new Promise((resolve, reject) => {
    let errors = [];
    let line = 0;
    let headers = [];
    let hasValidHeaders = true;
    let hasValidV1Headers = false;
    let hasValidV2Headers = false;

    Papa.parse(file, {
      delimiter: ",",
      error: reject,
      complete: () => resolve(errors),
      skipEmptyLines: true,
      step: (results, parser) => {
        line++; // use one-based indexing for users

        // debugger;

        // validate header
        if (line === 1) {
          headers = results.data.map((d) => d.toLowerCase());
          hasValidV1Headers = JSON.stringify(headers) === JSON.stringify(modelV1Headers);
          hasValidV2Headers = JSON.stringify(headers) === JSON.stringify(modelV2Headers);

          if (model == "1.0" && !hasValidV1Headers) {
            errors = errors.concat(`[Line ${line}] Invalid header, expected: ${modelV1Headers.join(",")}`);
            hasValidHeaders = false;
          } else if ((model === "1.9" || model === "2.0") && !hasValidV2Headers && !hasValidV1Headers) {
            errors = errors.concat(`[Line ${line}] Invalid header, expected: ${modelV2Headers.join(",")} or ${modelV1Headers.join(",")}`);
            hasValidHeaders = false;
          }

          if (!hasValidHeaders) {
            parser.abort();
          }

          return;
        }


        // validate # of columns
        if (results.data.length !== headers.length) {
          errors = errors.concat(`[Line ${line}] Expected ${headers.length} columns, found ${results.data.length} columns`);
        }

        // skip lines that contain only empty values
        if (results.data.every((d) => d === "")) {
          return;
        }
        
        // validate sic
        const sic = results.data[headers.indexOf("sic")];
        if (sic && !/^\d+$/.test(sic)) {
          errors = errors.concat(`[Line ${line}] Contains non-digit industry codes`);
        }

        // catch other errors
        if (results.errors.length) {
          let error = results.errors.map((r) => r.message).join(", ");
          errors = errors.concat(`[Line ${line}] ${error}`);
        }
      },
    });
  });
}
