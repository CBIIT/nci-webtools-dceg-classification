import * as soccerNet from "https://cdn.jsdelivr.net/npm/@danielruss/soccernet@latest/+esm"
const outputSuffixMap = new Map([ ['CSV','csv'],['Excel','xlsx'],["JSONL","jsonl"]])

const soccerModelSelect = document.getElementById("soccernet-model")
const runFilePanel = document.getElementById("soccerNet-file");
const runJobPanel = document.getElementById("soccerNet-singleJob");
const runJobButton = document.getElementById("soccerNet-singleJob-run")
const outputElement = document.getElementById("soccerNet-singleJob-results");
const fileElement = document.getElementById("soccerNet-file-file")
const runFileButton = document.getElementById("soccerNet-file-run")
let soccerConfig = await soccerNet.configureSOCcerNet();
async function configSOCcerNet(){
    console.log(soccerModelSelect.value)
    soccerConfig = await soccerNet.configureSOCcerNet(soccerModelSelect.value)
}
soccerModelSelect.addEventListener("change",configSOCcerNet);



async function runSingleJob(event){
    let JobTitleElement = document.getElementById("soccerNet-singleJob-JobTitle");
    let JobTaskElement = document.getElementById("soccerNet-singleJob-JobTask");
    // no job title and no job task... just return!
    if (JobTitleElement.value.trim().length == 0 && JobTaskElement.value.trim().length == 0){
        console.log("... no input data...")
        return
    }
    runJobButton.disabled = true;
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

    let results = await soccerNet.runSOCcerPipeline(inputObject,soccerConfig,{n:n})
    buildResultsTable(results)
    runJobButton.disabled=false;
}

function buildResultsTable(results){
    
    outputElement.classList.remove("d-none")
    outputElement.innerHTML = "";

    let table = document.createElement("table");
    table.classList.add("table")
    let headerRow = table.insertRow();
    headerRow.innerHTML = `<th>Rank</th><th>soc 2010</th><th>soc 2010 title</th><th>Score</th>`;
    let n = results[0].soc2010.length;
    for (let i=0; i<n; i++){
        let row = table.insertRow();
        row.innerHTML = `<td>${i+1}</td><td>${results[0].soc2010[i]}</td><td>${results[0].title[i]}</td><td>${results[0].score[i].toFixed(4)}</td>`;
    }
   outputElement.insertAdjacentElement("beforeend",table);
}

function clearSingleJob(){
    document.querySelectorAll('#soccerNet-singleJob [type="text"]').forEach((el)=>el.value="")
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
    
    // no file given? return
    if (fileElement.files.length<1){
        return
    }
    fileElement.disabled=true;
    runFileButton.disabled=true;
    setProgress(0);

    let n = parseInt( document.getElementById("soccerNet-n").value )||10;
    if (n<0 || n>840) {
        n=10
    }

    let outputType = document.getElementById("soccerNet-file-output-format").value;
    let file = fileElement.files[0];
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
        let initial_metadata={};
        let current_metadata={}
        while (!block.done){
            let results = await soccerNet.runSOCcerPipeline(block.value,soccerConfig,{n:n})
            if(block.value.meta.blockId == 0){
                initial_metadata = results.metadata
            }
            current_metadata = results.metadata;
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
    fileElement.disabled=false;
    fileElement.value=""
    runFileButton.disabled=false;
}
window.clearFile=clearFile

document.getElementById("soccernet-file-switch").addEventListener("click",(event)=>{
    // we could just toggle, but let's be safe
    if (event.target.checked){
        runFilePanel.classList.remove("d-none")
        outputElement.classList.add("d-none")
        runJobPanel.classList.add("d-none")
        clearSingleJob()
    }else{
        runJobPanel.classList.remove("d-none")
        outputElement.classList.remove("d-none")
        runFilePanel.classList.add("d-none")
        clearFile()
    }
})
runJobButton.addEventListener("click",runSingleJob)
runFileButton.addEventListener("click",runFile)