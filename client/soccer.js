form.onsubmit = submit;
form.onreset = reset;
form.onchange = handleChange;
// form.file.onchange = validateFile;

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
async function submit(event) {
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
      backgroundAlert.hidden = false;
    } else {
      await loadResults(results.id);
    }
  } catch (error) {
    warnings.hidden = false;
    warnings.innerText = error.message;
  } finally {
    form.resetButton.disabled = false;
    loader.hidden = true;
  }
}

/**
 * Resets the form and clears results and warnings
 */
function reset() {
  if (id) history.pushState(null, null, window.location.pathname);
  form.fieldset.disabled = false;
  form.submitButton.disabled = false;
  form.resetButton.disabled = false;
  form.email.disabled = true;

  resultsPlot.src = "data:,";
  resultsFile.href = "data:,";
  results.hidden = true;
  warnings.hidden = true;
  backgroundAlert.hidden = true;
}

/**
 * Handles changes to the form
 */
async function handleChange() {
  const file = form.file.files && form.file.files[0];

  // enforce background mode if file is larger than 4kb
  if (file) {
    // todo: validate file

    // if file is larger than 4kb, enforce background mode
    if (file.size > 10000)
      form.background.checked = true;
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
    resultsPlot.onload = () => results.hidden = false;
  } catch (error) {
    warnings.hidden = false;
    warnings.innerText = error.message;
  }
}
