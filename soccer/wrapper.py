from configparser import ConfigParser
from os import makedirs, linesep, path
from subprocess import STDOUT, CalledProcessError, check_call, check_output
from tempfile import TemporaryFile
from time import strftime
from traceback import format_exc
from urllib.request import pathname2url
from uuid import uuid4
import mimetypes
import re

from stompest.config import StompConfig
from stompest.sync import Stomp
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from werkzeug.urls import Href

SOCCER_WRAPPER_PATH = path.join('jars', 'soccer-wrapper.jar')
SOCCER_V1_PATH = path.join('jars', 'SOCcer-v1.0.jar')
SOCCER_V2_PATH = path.join('jars', 'SOCcer-v2.0.jar')

def call_soccer(method='',
                input_filepath='',
                output_filepath='',
                model_version='2',
                model_filepath=''):
    """ Calls methods from the SOCcer wrapper """

    if model_version == '1':
        jar_filepath = SOCCER_V1_PATH
    elif model_version == '2':
        jar_filepath = SOCCER_V2_PATH
    else:
        raise ValueError('Invalid model version selected')

    return check_output([
        'java', '-jar', SOCCER_WRAPPER_PATH,
        '--input-file', input_filepath,
        '--output-file', output_filepath,
        '--model-version', model_version,
        '--method', method,
        '--jar-file', jar_filepath,
        '--model-file', model_filepath,
    ], stderr=STDOUT)


def prevalidate_file(input_file, model_version):
    """ Prevalidates input file before passing to SOCCER validation
        input_file - werkzeug FileStorage object
        model_version - '1' or '2'
    """

    lines = input_file.readlines()
    input_file.seek(0) # reset cursor so we can call save() later

    # these rules stop further validation
    try:
        if (not re.search(r'\.csv$', input_file.filename)
            or ',' not in lines[0].decode('utf-8')):
            raise(Exception()) # catch decode errors as well
    except Exception:
        raise ValueError('The input file must be a valid csv file.')
    if len(lines) < 2:
        raise ValueError('The input file must contain data.')

    errors = []
    if not lines[-1].rstrip():
        errors.append('The input file must not end with multiple empty lines.')

    for index, line in enumerate(lines):
        if not line.strip():
            errors.append('The input file contains an empty line on row %d.' % (index + 1))

    if errors:
        raise ValueError('\n'.join(errors))


def validate_file(input_filepath, model_version):
    """
        Validates an input file against the specified model version
        If there are validation errors, they will be available in the
        'output' attribute of the exception
    """
    call_soccer(
        'validate-file',
        input_filepath=input_filepath,
        model_version=model_version
    )


def estimate_runtime(input_filepath, model_version):
    # get estimated runtime
    return float(call_soccer(
        'estimate-runtime',
        input_filepath=input_filepath,
        model_version=model_version
    ))


def code_file(input_filepath, output_filepath, model_version, model_filepath):
    """ Generates a coded output file """
    call_soccer(
        method='code-file',
        input_filepath=input_filepath,
        output_filepath=output_filepath,
        model_version=model_version,
        model_filepath=model_filepath
    )


def plot_results(results_filepath, plot_filepath):
    check_call([
        'Rscript',
        'soccerResultPlot.R',
        results_filepath,
        plot_filepath
    ])
