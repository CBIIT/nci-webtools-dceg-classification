from os import path
from time import strftime
from traceback import format_exc
from urllib.request import pathname2url
from uuid import uuid4

from flask import Flask, json, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from werkzeug.urls import Href
from utils import make_dirs, read_config, enqueue
from wrapper import prevalidate_file, validate_file, estimate_runtime, code_file, plot_results


if __name__ == '__main__':
    # Serve current directory using Flask for local development
    app = Flask(__name__, static_folder='', static_url_path='')
else:
    # Otherwise, assume mod_wsgi/apache will serve static files
    app = Flask(__name__, static_folder=None)

# Load configuration from file
app.config.update(read_config('config.ini'))


@app.before_request
def before_request():
    """ Ensure input/output directories exist """
    config = app.config['soccer']
    make_dirs(
        config['input_dir'],
        config['output_dir']
    )


@app.errorhandler(Exception)
def error_handler(e):
    """ Ensure errors are logged and returned as json """
    app.logger.error(format_exc())
    output = getattr(e, 'output', None)
    return jsonify(
        output.decode('utf-8') if output
        else str(e)
    ), 500


@app.route('/validate', methods=['POST'], strict_slashes=False)
def validate():
    """ Validate input files against the specified version of the model """

    # get parameters
    input_file = request.files['input_file']
    model_version = request.form['model_version']

    # prevalidate input file before saving
    prevalidate_file(input_file, model_version)

    # save uploaded file to the input directory
    file_id = str(uuid4())
    input_dir = app.config['soccer']['input_dir']
    input_filepath = path.join(input_dir, file_id)
    input_file.save(input_filepath)

    # throws exception if invalid
    validate_file(
        input_filepath=input_filepath,
        model_version=model_version,
    )

    # if estimated runtime is greater than 30, recommend enqueueing file (in UI)
    estimated_runtime = estimate_runtime(
        input_filepath=input_filepath,
        model_version=model_version,
    )

    return jsonify({
        'file_id': file_id,
        'estimated_runtime': estimated_runtime
    })


@app.route('/submit', methods=['POST'], strict_slashes=False)
def submit():
    """ Codes the input file to different SOC categories """

    # get parameters
    file_id = request.form['file_id']
    model_version = request.form['model_version']

    # get configuration
    input_dir = app.config['soccer']['input_dir']
    output_dir = app.config['soccer']['output_dir']
    model_filepath = app.config['soccer']['model_file']

    # specify input/output filepaths
    input_filepath = safe_join(input_dir, file_id)
    parameters_filepath = safe_join(output_dir, file_id + '.json')
    output_filepath = safe_join(output_dir, file_id + '.csv')
    plot_filepath = safe_join(output_dir, file_id + '.png')

    # save form parameters as json file
    with open(parameters_filepath, 'w') as f:
        json.dump(request.form, f)

    # results are written to output_filepath
    code_file(
        input_filepath=input_filepath,
        output_filepath=output_filepath,
        model_version=model_version,
        model_filepath=model_filepath
    )

    plot_results(
        results_filepath=output_filepath,
        plot_filepath=plot_filepath
    )

    return jsonify({
        'file_id': file_id
    })


@app.route('/submit-queue', methods=['POST'], strict_slashes=False)
def submit_queue():
    """ Sends parameters to the queue for processing """
    queue_url = app.config['queue']['url']
    queue_name = app.config['queue']['name']
    parameters = json.dumps({
        'recipient': request.form['email'],
        'file_id': request.form['file_id'],
        'model_version': request.form['model_version'][0],
        'original_filename': request.files['input_file'].filename,
        'results_url': Href(request.form['url_root'])(id=request.form['file_id']),
        'timestamp': strftime('%a %b %X %Z %Y'),
    })

    enqueue(
        queue_url=queue_url,
        queue_name=queue_name,
        data=parameters
    )

    return jsonify(True)


@app.route('/results/<path:filename>', methods=['GET'], strict_slashes=False)
def get_results(filename):
    """
        Serves results files. The following convention is used:
         - /results/<file_id>.json (calculation parameters)
         - /results/<file_id>.csv (output csv)
         - /results/<file_id>.png (output plot)
    """
    return send_from_directory(
        directory=app.config['soccer']['output_dir'],
        filename=filename,
        as_attachment=True
    )


@app.route('/ping', strict_slashes=False)
def ping():
    """ Healthcheck endpoint """
    return jsonify(True)


if __name__ == '__main__':
    """ Serve application on port 10000 when running locally """

    @app.route('/')
    def index():
        return send_file('index.html')

    app.run('0.0.0.0', port=10000, debug=True)
