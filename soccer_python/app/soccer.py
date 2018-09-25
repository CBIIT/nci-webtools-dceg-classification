
from ConfigParser import SafeConfigParser
from uuid import uuid4
from os import makedirs, path
from flask import Flask, jsonify, send_file
import subprocess
from flask import Flask, jsonify, request, Response, send_from_directory
import uuid
from stompest.config import StompConfig
from stompest.sync import Stomp
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='', static_url_path='')

def get_config(filepath='config.ini'):
    '''Returns a config file's contents as a dictionary'''
    config = SafeConfigParser()
    config.read(filepath)
    return config._sections

def init():
    app.config.update(get_config())
    output_dir = app.config['folders']['output']

    if not path.isdir(output_dir):
        makedirs(output_dir)

init()

@app.errorhandler(Exception)
def error_handler(e):
    '''Ensures that uncaught errors are logged and returned as json'''
    app.logger.error(format_exc())
    return jsonify(str(e)), 500

@app.route('/upload', methods=['POST'])
def upload():
    output_dir = app.config['folders']['output']
    input_file = request.files['input-file']
    model = request.form['model']
    token = str(uuid4())

    input_filepath = path.join(output_dir, '%s.csv' % token)
    output_filepath = path.join(output_dir, '%s.validated.json' % token)
    input_file.save(input_filepath)

    subprocess.call([
        'java', '-jar', 'soccer.jar',
        '--validate',
        '--model', model,
        '--input-file', input_filepath,
        '--output-file', output_filepath,
    ])

    return send_file(output_path)


@app.route('/calculate', methods=['POST'])
def calculate():

    output_dir = app.config['folders']['output']
    model = request.form['model']
    token = request.form['token']

    input_filepath = path.join(output_dir, '%s.csv' % token)
    output_filepath = path.join(output_dir, '%s.json' % token)

    subprocess.call([
        'java', '-jar', 'soccer.jar',
        '--calculate',
        '--model', model,
        '--input-file', input_filepath,
        '--output-file', output_filepath,
    ])

    return send_file(output_filepath)

@app.route('/enqueue', methods=['POST']):
def enqueue():
    queue = app.config['queue']
    client = Stomp(StompConfig(queue['url']))
    client.connect()
    client.send(queue['name'], json.dumps(request.form))
    client.disconnect()

@app.route('/', methods=['GET'])
def index(path):
    return send_file('index.html')



    # try:
    #     filename = None
    #     if len(request.files) > 0 and 'fileSelect' in request.files:
    #         userFile = request.files['fileSelect']
    #         socSystem = request.form["socSystem"]
    #         originalFileName = userFile.filename

    #         # check for correct file extension
    #         fileName = str(uuid.uuid4())
    #         filePath = os.path.join(
    #             RESULTS_PATH, fileName + ".csv")
    #         saveFile = userFile.save(filePath)
    #         responseObj = jsonify({'status': 'invalid', 'details': ['No file part']})

    #         if socSystem=="model10":
    #             return_code = subprocess.call(['java', '-cp', 'Java_API.jar', 'gov.nih.nci.queue.api.FileUpload', filePath, originalFileName, 'application/vnd.ms-excel'])
    #         else:
    #            return_code = subprocess.call(['/etc/alternatives/jre_1.8.0/bin/java', '-cp', 'Java_API_1_1.jar', 'gov.nih.nci.queue.api.FileUpload', filePath, originalFileName, 'application/vnd.ms-excel'])
    #         with open(filePath + '_response.json', 'r') as resultFile:
    #             responseObj = resultFile.read().replace('\n', '')
    #         os.remove(filePath + '_response.json')

    #     else:
    #         responseObj = jsonify({'status': 'invalid', 'details': ['No file part']})
    # finally:
    #     return responseObj


# @app.route('/calc', methods=["POST"])
# def calc():
#     try:
#         print("INPUTID")
#         inputFileId = os.path.basename(request.form["inputFileId"])
#         socSystem = request.form["socSystem"]
#         if socSystem=="model10":
#             return_code = subprocess.call(['/usr/local/jdk1.7/bin/java', '-cp', 'Java_API.jar', 'gov.nih.nci.queue.api.FileCalculate', inputFileId])
#         else:
#             return_code = subprocess.call(['/etc/alternatives/jre_1.8.0/bin/java', '-cp', 'Java_API_1_1.jar', 'gov.nih.nci.queue.api.FileCalculate', inputFileId])
#         filePath = os.path.join(RESULTS_PATH, inputFileId)
#         with open(filePath + '_response.json', 'r') as resultFile:
#             response = json.load(resultFile)
#         os.remove(filePath + '_response.json')
#     finally:
#         filename, extension = os.path.splitext(inputFileId)
#         if extension != ".csv" or not valid_uuid(filename):
#             response['status'] = 'fail'
#             response['errorMessage'] = 'Invalid input file'

#         return jsonify(response)


# @app.route('/queue', methods=['POST'])
# def queue():

#     inputFileId = request.form["inputFileId"]
#     print(request.form["inputFileId"])

#     emailAddress = request.form["emailAddress"]
#     print(request.form["emailAddress"])

#     fileName = request.form["fileName"]
#     print(request.form["fileName"])

#     url=str(request.form["url"])+"/index.html?fileid="+inputFileId
#     print(request.form["url"])

#     socSystem = request.form["socSystem"]
#     print(socSystem)
#     print("Sending to queue")
#     sendqueue(inputFileId,emailAddress,fileName,url,socSystem)

#     return jsonify({'status': 'pass'})


# def sendqueue(inputFileId,emailAddress,fileName,url,socSystem):
#     #try:
#     import time
#     now = time.strftime("%a %b %X %Z %Y")
#     QUEUE = soccerConfig.getAsString(QUEUE_NAME)
#     QUEUE_CONFIG=StompConfig(soccerConfig.getAsString(QUEUE_URL))
#     filePath = os.path.join(RESULTS_PATH, inputFileId)
#     client = Stomp(QUEUE_CONFIG)
#     client.connect()
#     client.send(QUEUE,json.dumps({"inputFileId":inputFileId,"emailAddress":emailAddress,"fileName":fileName,"timestamp":now,"url":url,"socSystem":socSystem}))
#     client.disconnect()
# def valid_uuid(uuid):
#     regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
#     match = regex.match(uuid)
#     return bool(match)
