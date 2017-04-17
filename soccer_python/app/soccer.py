import json
import os
import subprocess
import sys
import time
from flask import Flask, jsonify, request, Response, send_from_directory
import uuid


from werkzeug.utils import secure_filename

app = Flask(__name__)


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


app.run(debug=False)
