import json
import os
import subprocess
import sys
import time
from flask import Flask, jsonify, request, Response, send_from_directory
import uuid
from stompest.config import StompConfig
from stompest.sync import Stomp
from PropertyUtil import PropertyUtil
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='', static_url_path='/') 
QUEUE_NAME = 'queue.name'
QUEUE_URL = 'queue.url'
soccerConfig = PropertyUtil(r"config.ini")

@app.route('/upload', methods=["POST"])
def upload():

    try:
        filename = None
        if len(request.files) > 0 and 'fileSelect' in request.files:
            userFile = request.files['fileSelect']
            originalFileName = userFile.filename

            # check for correct file extension
            fileName = str(uuid.uuid4())
            filePath = os.path.join(
                '/local/content/soccer/files', fileName + ".csv")
            saveFile = userFile.save(filePath)
            print(filePath)
            print("We have a file")

            responseObj = jsonify({'status': 'invalid', 'details': ['No file part']})

            subprocess.call(['java', '-jar', 'Blender.jar'])

            return_code = subprocess.call(['java', '-cp', 'Java_API.jar', 'gov.nih.nci.queue.api.FileUpload', filePath, originalFileName, 'application/vnd.ms-excel'])
            
            with open(filePath + '_response.json', 'r') as resultFile:
                responseObj = resultFile.read().replace('\n', '')
            print('response object: ' + responseObj)
            os.remove(filePath + '_response.json')

        else:
            print("here")
            flash('No file part')
            responseObj = jsonify({'status': 'invalid', 'details': ['No file part']})
    finally:
        return responseObj


@app.route('/calc', methods=["POST"])
def calc():
    try:
        print("INPUTID")
        inputFileId = request.form["inputFileId"]
        print(inputFileId)
        return_code = subprocess.call(['java', '-cp', 'Java_API.jar', 'gov.nih.nci.queue.api.FileCalculate', inputFileId])
        filePath = os.path.join('/local/content/soccer/files', inputFileId)
        with open(filePath + '_response.json', 'r') as resultFile:
            responseObj = resultFile.read().replace('\n', '')
        print('response object: ' + responseObj)
        os.remove(filePath + '_response.json')

    finally:
        return responseObj


@app.route('/<path:path>')
def static_files(path):
    if path.endswith('/'):
        path += 'index.html'
    return send_from_directory(os.getcwd(), path)

@app.route('/queue', methods=['POST']) 
def queue():

    inputFileId = request.form["inputFileId"]
    print(request.form["inputFileId"])
    
    emailAddress = request.form["emailAddress"]
    print(request.form["emailAddress"])

    fileName = request.form["fileName"]
    print(request.form["fileName"])

    url=str(request.form["url"])
    print(request.form["url"])

    sendqueue(inputFileId,emailAddress,fileName,url);


    status = "{\"status\":\"pass\"}"
    mimetype = 'application/json'
    out_json = json.dumps(status)

    return out_json


def sendqueue(inputFileId,emailAddress,fileName,url):
    #try:
    import time
    now = time.strftime("%a %b %X %Z %Y")
    QUEUE = soccerConfig.getAsString(QUEUE_NAME)
    QUEUE_CONFIG=StompConfig(soccerConfig.getAsString(QUEUE_URL)) 
    filePath = os.path.join('/local/content/soccer/files', inputFileId)
    client = Stomp(QUEUE_CONFIG)
    client.connect()
    client.send(QUEUE,json.dumps({"inputFileId":inputFileId,"emailAddress":emailAddress,"fileName":fileName,"timestamp":now,"url":url}))
    client.disconnect()