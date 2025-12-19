import * as clips from "https://cdn.jsdelivr.net/npm/@danielruss/clips@latest/+esm";
import * as soccerNet from "https://cdn.jsdelivr.net/npm/@danielruss/soccernet@latest/+esm"
const outputSuffixMap = new Map([ ['CSV','csv'],['Excel','xlsx'],["JSONL","jsonl"]])

const soccerModelSelect = document.getElementById("soccernet-model")
const soccerNetFileSwitch = document.getElementById("fileSwitch")
const soccerNetRunFilePanel = document.getElementById("soccerNet-file");
const soccerNetRunJobPanel = document.getElementById("soccerNet-singleJob");

const clipsRunJobPanel = document.getElementById("clips-singleJob");
const outputElement = document.getElementById("soccerNet-singleJob-results");

const soccerNetFileElement = document.getElementById("soccerNet-file-file")
const soccerNetRunButton = document.getElementById("soccerNet-run-button")

let modelConfig = await soccerNet.configureSOCcerNet();



async function configApplication(){
    // Am I running clips OR soccerNet?
    let modelInfo = getModelInfo()
    console.log("in configApplication: ",modelInfo)
    if (modelInfo.name == "clips"){
        modelConfig = await clips.configureClips(modelInfo.version)
    } else {
        modelConfig = await soccerNet.configureSOCcerNet(modelInfo.version)
    }
}



async function runSingleJob(event){
    let JobTitleElement = document.getElementById("soccerNet-singleJob-JobTitle");
    let JobTaskElement = document.getElementById("soccerNet-singleJob-JobTask");
    // no job title and no job task... just return!
    if (JobTitleElement.value.trim().length == 0 && JobTaskElement.value.trim().length == 0){
        console.log("... no input data...")
        return
    }
    soccerNetRunButton.disabled = true;

    let inputObject = {JobTitle: JobTitleElement.value,JobTask: JobTaskElement.value}
    const xw= ["soc1980","isco1988","noc2011"]
    xw.forEach( (cs) => {
        let inputElement= document.getElementById(`soccerNet-singleJob-${cs}`);
        if (inputElement.value.length > 0){
            inputObject[cs] = inputElement.value
        }
    })
    let n = parseInt( document.getElementById("soccerNet-n").value )||10;
    if (n<0 || n>840) {
        n=10
    }

    let results = await soccerNet.runSOCcerPipeline(inputObject,modelConfig,{n:n})
    buildResultsTable(results)
    clearSingleJobInput()
}
async function runSingleClipsJob(){
    let products = document.getElementById("clips-singleJob-products").value.trim();
    let sic1987 = document.getElementById("clips-singleJob-sic1987").value.trim();
    let n = parseInt( document.getElementById("soccerNet-n").value )||10
    // no products ... just return!
    if (products.length == 0){
        console.log("... no input data...")
        return
    }
    soccerNetRunButton.disabled = true;
    if (n<0 || n>689) {
        n=10
    }
    let inputObject = {
        products_services: products,
        sic1987: sic1987
    }
    let results = await clips.runClipsPipeline(inputObject,modelConfig,{n:n})
    buildResultsTable(results)
    clearSingleJobInput()
}



function buildResultsTable(results){
    
    outputElement.classList.remove("d-none")
    outputElement.innerHTML = "";
    const {name,_} = getModelInfo();

    let table = document.createElement("table");
    table.classList.add("table")
    let headerRow = table.insertRow();
    headerRow.innerHTML = (name === "clips")
        ? `<th>Rank</th><th>naics 2022</th><th>naics 2022 title</th><th>Score</th>`
        : `<th>Rank</th><th>soc 2010</th><th>soc 2010 title</th><th>Score</th>`;
    let n = results[0].score.length;
    for (let i=0; i<n; i++){
        let row = table.insertRow();
        row.innerHTML = (name === "clips") 
        ? `<td>${i+1}</td><td>${results[0].naics2022[i]}</td><td>${results[0].title[i]}</td><td>${results[0].score[i].toFixed(4)}</td>`
        : `<td>${i+1}</td><td>${results[0].soc2010[i]}</td><td>${results[0].title[i]}</td><td>${results[0].score[i].toFixed(4)}</td>`;
    }
   outputElement.insertAdjacentElement("beforeend",table);
}


function clearSingleJobInput(){
    document.querySelectorAll('#soccerNet-singleJob [type="text"]').forEach((el)=>el.value="")
    document.querySelectorAll('#clips-singleJob [type="text"]').forEach((el)=>el.value="")
    soccerNetRunButton.disabled=false;
}
function clearSingleJob(){
    clearSingleJobInput()
    outputElement.innerText=""
}


function removeFileExtension(filename){
    const lastDotIndex = filename.lastIndexOf('.');
    if (lastDotIndex === -1) {
        return filename;
    }
    return filename.substring(0, lastDotIndex);
}
const progressBar=document.getElementById("soccernet-file-progress")
const progressBarDiv=document.getElementById("soccernet-file-progress-value")
function setProgress(currentProgress){
    progressBar.setAttribute('aria-valuenow', currentProgress);
    progressBarDiv.style.width=currentProgress+'%';
    progressBarDiv.innerText=currentProgress+'%';
}
const alertDiv = document.getElementById("soccernet-file-alert-container")
function createAlert(message, type) {
    const wrapper = document.createElement('div')
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible" role="alert">`,
        `   <div>${message}</div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>'
    ].join('')

    alertDiv.append(wrapper)
}
async function runFile(event){
    const {name,_} = getModelInfo()

    // no file given? return
    if (soccerNetFileElement.files.length<1){
        return
    }
    soccerNetFileElement.disabled=true;
    soccerNetRunButton.disabled=true;
    soccerNetFileSwitch.disabled=true;
    setProgress(0);

    let n = parseInt( document.getElementById("soccerNet-n").value )||10;
    if (n<0 || n>840) {
        n=10
    }

    let outputType = document.getElementById("soccerNet-file-output-format").value;
    let file = soccerNetFileElement.files[0];
    let pb=document.getElementById("soccernet-file-progress")

    // break into blocks for efficent running
    let iterator = await soccerNet.getFileIterator(file)
    let block = await iterator.next()
    let {value: {totalBlocks, totalLines}} = block;
    let utf8Encoder = new TextEncoder();

    let outputFilename = `${removeFileExtension(file.name)}_soccerNet_results.${outputSuffixMap.get(outputType)}`
    let writable = await soccerNet.createOPFSWritableStream(outputFilename)
    try {  
        block = await iterator.next()
        let initial_metadata={
            start_time: new Date().toLocaleString()
        };
        let current_metadata={}
        while (!block.done){
            let results = (name === "clips") ?
                await clips.runClipsPipeline(block.value, modelConfig, { n: n }) :
                await soccerNet.runSOCcerPipeline(block.value, modelConfig, { n: n });
            if(block.value.meta.blockId == 0){
                initial_metadata = await results.metadata
            }
            current_metadata = await results.metadata;
            soccerNet.writeResultsBlockToOPFS(results,writable,utf8Encoder,outputType)

            let nlines = block.value.meta.lines + block.value.data.length;
            setProgress(Math.round(100*(nlines/totalLines)) );
            block = await iterator.next()
        }
        await soccerNet.closeOPFSStream(writable);
        // fix the metadata. we are not interested in the start_time of the last 
        // block...
        current_metadata.start_time = initial_metadata.start_time;
        await soccerNet.downloadResultsFromOPFS(outputFilename,outputType,current_metadata)        
    } catch (error) {
        console.error("ERROR WHILE RUNNING SOCcerNET:\n",error)
        createAlert(`There was a problem running SOCcerNET on ${file.name}. `,"danger")
    } finally {
        clearFile()
        setTimeout(()=>{setProgress(0)},2000)
    }

}
function clearFile(){
    soccerNetFileElement.value=""
    soccerNetFileElement.disabled=false;
    soccerNetRunButton.disabled=false;
    soccerNetFileSwitch.disabled=false;
}
window.clearFile=clearFile



function displayForm(event){
    const modelInfo = getModelInfo();
    const runFile = soccerNetFileSwitch.checked
    console.log(modelInfo,runFile)

    document.getElementById("soccernet-button-model").innerText = (modelInfo.name == "clips")?"CLIPS":"SOCcerNET"
    clearSingleJob()
    clearFile()

    let label = document.querySelector("[for='soccernet-n']");
    let n_element = document.getElementById("soccerNet-n");
    let n = parseInt( n_element.value )||10;
    if (runFile){
        // The form is the same if you are running soccer or clips
        soccerNetRunFilePanel.classList.remove("d-none")
        outputElement.classList.add("d-none")
        soccerNetRunJobPanel.classList.add("d-none")
        clipsRunJobPanel.classList.add("d-none");
        if (modelInfo.name == "clips"){
            n_element.max=689;
            label.innerHTML = `# of codes requested<br><span id="n" class="fs-extra-small"> (max 689)</span>`;
        } else {
            n_element.max=840;
            label.innerHTML = `# of codes requested<br><span id="n" class="fs-extra-small"> (max 840)</span>`;
        }
    } else if (modelInfo.name == "clips"){
        // display the CLIPS single job input + output
        clipsRunJobPanel.classList.remove("d-none");
        document.getElementById("clips-singleJob-products").focus()
        outputElement.classList.remove("d-none")
        soccerNetRunJobPanel.classList.add("d-none")
        soccerNetRunFilePanel.classList.add("d-none")
        n_element.max=689;
        label.innerHTML = `# of codes requested<br><span id="n" class="fs-extra-small"> (max 689)</span>`;
    } else {
        // display the SOCcer single job input
        soccerNetRunJobPanel.classList.remove("d-none")
        document.getElementById("soccerNet-singleJob-JobTitle").focus()
        outputElement.classList.remove("d-none")
        clipsRunJobPanel.classList.add("d-none");
        soccerNetRunFilePanel.classList.add("d-none")
        n_element.max=840;
        label.innerHTML = `# of codes requested<br><span id="n" class="fs-extra-small"> (max 840)</span>`;
    }
}
function getModelInfo(){
    return {
        name: soccerModelSelect.selectedOptions[0].dataset.modelName,
        version: soccerModelSelect.selectedOptions[0].dataset.modelVersion
    }
}
function runSOCcer(){
    let {name, _} = getModelInfo()
    if (soccerNetFileSwitch.checked){
        console.log("calling Runfile()")
        runFile()
    } else if (name == "clips"){
        runSingleClipsJob()
    }else{
        runSingleJob()
    }
}

export function soccerNetNavClicked(event){
    window['nav-soccernet'].click()
    console.log("SOCcerNET/CLiPS navigation",event.target.dataset)
    soccerModelSelect.value = event.target.dataset.modelVersion
    soccerModelSelect.dispatchEvent(new Event('change', { bubbles: true }));
}
document.querySelectorAll('[data-model').forEach((el)=>el.addEventListener("click",soccerNetNavClicked));

soccerNetFileSwitch.addEventListener("click",displayForm)
soccerModelSelect.addEventListener("change",configApplication);
soccerModelSelect.addEventListener("change",displayForm);
soccerNetRunButton.addEventListener("click",runSOCcer);
// if the user clicks on the "single job" or "file" text span, toggle the switch
function labelClicked(event){
    soccerNetFileSwitch.checked = event.target.dataset.singleJob !== "true"
    displayForm();
}
document.querySelectorAll('[data-single-job]').forEach((el)=>el.addEventListener("click",labelClicked));
displayForm();