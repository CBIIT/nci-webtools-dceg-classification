from ConfigParser import SafeConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, jsonify, render_template, request, send_file
from os import makedirs, linesep, path
# from stompest.config import StompConfig
# from stompest.sync import Stomp
from smtplib import SMTP
from subprocess import STDOUT, CalledProcessError, check_call, check_output
from threading import Thread
from time import strftime
from traceback import format_exc
from urllib import pathname2url
from uuid import uuid4
from werkzeug.security import safe_join


SOCCER_WRAPPER_PATH = path.join('jars', 'soccer-wrapper.jar')
SOCCER_V1_PATH = path.join('jars', 'SOCcer-v1.0.jar')
SOCCER_V2_PATH = path.join('jars', 'SOCcer-v2.0.jar')


if __name__ == '__main__':
    '''Serve static files using Flask for local development'''
    app = Flask(__name__, static_folder='', static_url_path='')
else:
    '''Otherwise, use mod_wsgi/apache to serve files'''
    app = Flask(__name__)


def get_config(filepath='config.ini'):
    '''Reads a config file as a dictionary'''
    config = SafeConfigParser()
    config.read(filepath)
    return config._sections


def init():
    '''Loads configuration and creates output directories'''
    app.config.update(get_config())
    input_dir = app.config['soccer']['input_dir']
    output_dir = app.config['soccer']['output_dir']

    for dir in [input_dir, output_dir]:
        if not path.isdir(dir):
            makedirs(dir)

def send_mail(sender, recipient, subject, contents):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.attach(MIMEText(contents, 'html'))

    smtp = SMTP(app.config['mail']['host'])
    smtp.sendmail(sender, recipient, msg.as_string())


init()


@app.errorhandler(Exception)
def error_handler(e):
    '''Ensures errors are logged and returned as json'''
    app.logger.error(format_exc())
    return jsonify(getattr(e, 'output', str(e))), 500


@app.route('/validate', methods=['POST'], strict_slashes=False)
def validate():
    '''Validates input files against the specified version of the model'''
    input_dir = app.config['soccer']['input_dir']
    input_file = request.files['input-file']
    model_version = request.form['model-version']
    file_id = str(uuid4())

    input_filepath = path.join(input_dir, file_id)
    input_file.save(input_filepath)

    if model_version == '1':
        jar_filepath = SOCCER_V1_PATH
    elif model_version == '2':
        jar_filepath = SOCCER_V2_PATH
    else:
        raise ValueError('Invalid model version selected')

    # common arguments for soccer-wrapper.jar
    common_args = [
        '--input-file', input_filepath,
        '--jar-file', jar_filepath,
        '--model-version', model_version,
    ]

    # validate file
    check_output([
        'java', '-jar', SOCCER_WRAPPER_PATH,
        '--method', 'validate-file',
    ] + common_args, stderr=STDOUT)

    # get estimated runtime
    estimated_runtime = check_output([
        'java', '-jar', SOCCER_WRAPPER_PATH,
        '--method', 'estimate-runtime',
    ] + common_args, stderr=STDOUT)

    return jsonify({
        'estimated_runtime': float(estimated_runtime),
        'file_id': file_id,
    })


@app.route('/code-file', methods=['POST'], strict_slashes=False)
def code_file():
    '''Codes the input file to different SOC categories'''

    input_dir = app.config['soccer']['input_dir']
    output_dir = app.config['soccer']['output_dir']
    model_version = request.form['model-version']
    file_id = request.form['file-id']

    input_filepath = safe_join(input_dir, file_id)
    output_filepath = safe_join(output_dir, file_id + '.csv')
    plot_filepath = safe_join(output_dir, file_id + '.png')

    if model_version == '1':
        jar_filepath = SOCCER_V1_PATH
    elif model_version == '2':
        jar_filepath = SOCCER_V2_PATH
    else:
        raise ValueError('Invalid model version selected')

    # code file
    check_call([
        'java', '-jar', SOCCER_WRAPPER_PATH,
        '--input-file', input_filepath,
        '--output-file', output_filepath,
        '--model-version', model_version,
        '--method', 'code-file',
        '--jar-file', jar_filepath,
        '--model-file', app.config['soccer']['model_file'],
    ], stderr=STDOUT)

    # create plot
    check_call([
        'Rscript', 'soccerResultPlot.R',
        output_filepath, plot_filepath
    ])

    return jsonify(file_id)


@app.route('/results/<file_id>', methods=['GET'], strict_slashes=False)
def get_results(file_id):
    '''Retrieves paths to the results files based on the file token'''

    output_dir = app.config['soccer']['output_dir']
    output_filepath = safe_join(output_dir, file_id + '.csv')
    plot_filepath = safe_join(output_dir, file_id + '.png')

    if not all(path.isfile(i) for i in [output_filepath, plot_filepath]):
        raise ValueError('Invalid file id')

    return jsonify({
        'output_url': pathname2url(output_filepath),
        'plot_url': pathname2url(plot_filepath),
    })


@app.route('/enqueue', methods=['POST'], strict_slashes=False)
def enqueue():
    '''Processes files in a separate thread and sends an email once complete'''
    context = request.environ
    def execute():
        with app.request_context(context):
            parameters = {
                'email': request.form['email'],
                'filename': request.files['input-file'].filename,
                'model_version': request.form['model-version'],
                'timestamp': strftime('%a %b %X %Z %Y'),
                'results_url': request.url_root + '?id=' + request.form['file-id'],
            }
            code_file()
            send_mail(
                app.config['mail']['admin'],
                parameters['email'],
                'SOCcer - Your request has been processed',
                render_template('email.html', **parameters)
            )

    Thread(target=execute).start()
    return jsonify(True)


@app.route('/', methods=['GET'], strict_slashes=False)
def index():
    return send_file('index.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=10000, debug=True)