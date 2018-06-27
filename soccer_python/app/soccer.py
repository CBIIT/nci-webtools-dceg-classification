import json
import os
import re
import subprocess
import sys
import time
from flask import Flask, jsonify, request, Response, send_from_directory
import uuid
from stompest.config import StompConfig
from stompest.sync import Stomp
from PropertyUtil import PropertyUtil
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='', static_url_path='')
QUEUE_NAME = 'queue.name'
QUEUE_URL = 'queue.url'
soccerConfig = PropertyUtil(r"config.ini")
RESULTS_PATH = soccerConfig.getAsString("soccer.folder.out")

def valid_uuid(uuid):
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuid)
    return bool(match)

@app.route('/upload', methods=["POST"])
def upload():

    try:
        filename = None
        if len(request.files) > 0 and 'fileSelect' in request.files:
            userFile = request.files['fileSelect']
            socSystem = request.form["socSystem"]
            originalFileName = userFile.filename

            # check for correct file extension
            fileName = str(uuid.uuid4())
            filePath = os.path.join(
                RESULTS_PATH, fileName + ".csv")
            saveFile = userFile.save(filePath)
            responseObj = jsonify({'status': 'invalid', 'details': ['No file part']})

            if socSystem=="model10":
                return_code = subprocess.call(['java', '-cp', 'Java_API.jar', 'gov.nih.nci.queue.api.FileUpload', filePath, originalFileName, 'application/vnd.ms-excel'])
            else:
               return_code = subprocess.call(['java', '-cp', 'Java_API_1_1.jar', 'gov.nih.nci.queue.api.FileUpload', filePath, originalFileName, 'application/vnd.ms-excel'])
            with open(filePath + '_response.json', 'r') as resultFile:
                responseObj = resultFile.read().replace('\n', '')
            os.remove(filePath + '_response.json')

        else:
            responseObj = jsonify({'status': 'invalid', 'details': ['No file part']})
    finally:
        return responseObj


@app.route('/calc', methods=["POST"])
def calc():
    try:
        print("INPUTID")
        inputFileId = os.path.basename(request.form["inputFileId"])
        socSystem = request.form["socSystem"]
        if socSystem=="model10":
            return_code = subprocess.call(['/usr/local/jdk1.7/bin/java', '-cp', 'Java_API.jar', 'gov.nih.nci.queue.api.FileCalculate', inputFileId])
        else:
            return_code = subprocess.call(['java', '-cp', 'Java_API_1_1.jar', 'gov.nih.nci.queue.api.FileCalculate', inputFileId])
        filePath = os.path.join(RESULTS_PATH, inputFileId)
        with open(filePath + '_response.json', 'r') as resultFile:
            response = json.load(resultFile)
        os.remove(filePath + '_response.json')
    finally:
        filename, extension = os.path.splitext(inputFileId)
        if extension != ".csv" or not valid_uuid(filename):
            response['status'] = 'fail'
            response['errorMessage'] = 'Invalid input file'

        return jsonify(response)


@app.route('/')
def index(path):
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/queue', methods=['POST'])
def queue():

    inputFileId = request.form["inputFileId"]
    print(request.form["inputFileId"])

    emailAddress = request.form["emailAddress"]
    print(request.form["emailAddress"])

    fileName = request.form["fileName"]
    print(request.form["fileName"])

    url=str(request.form["url"])+"/index.html?fileid="+inputFileId
    print(request.form["url"])

    socSystem = request.form["socSystem"]
    print(socSystem)
    print("Sending to queue")
    sendqueue(inputFileId,emailAddress,fileName,url,socSystem)

    return jsonify({'status': 'pass'})


def sendqueue(inputFileId,emailAddress,fileName,url,socSystem):
    #try:
    import time
    now = time.strftime("%a %b %X %Z %Y")
    QUEUE = soccerConfig.getAsString(QUEUE_NAME)
    QUEUE_CONFIG=StompConfig(soccerConfig.getAsString(QUEUE_URL))
    filePath = os.path.join(RESULTS_PATH, inputFileId)
    client = Stomp(QUEUE_CONFIG)
    client.connect()
    client.send(QUEUE,json.dumps({"inputFileId":inputFileId,"emailAddress":emailAddress,"fileName":fileName,"timestamp":now,"url":url,"socSystem":socSystem}))
    client.disconnect()
