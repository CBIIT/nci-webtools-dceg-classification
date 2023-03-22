from configparser import ConfigParser
from os import makedirs, linesep, path
from subprocess import STDOUT, CalledProcessError, check_call, check_output
from tempfile import TemporaryFile
from time import strftime
from traceback import format_exc
from urllib.request import pathname2url
from uuid import uuid4
import mimetypes
import csv
import os
import re

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
        model_version - '1' or '1.9' or  '2'
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


def format_file(input_filepath):
    """ Formats an input csv file for use with SOCCER
        input_filepath - path to input file
    """
    output_filepath = input_filepath + '.formatted'

    if os.path.exists(output_filepath):
      os.remove(output_filepath)

    with open(input_filepath, encoding="utf8") as input_file:
        with open(output_filepath, 'w', newline='', encoding="utf8") as output_file:
            reader = csv.reader(input_file)
            writer = csv.writer(output_file)
            for row in reader:
                # replace newlines, tabs, etc within records
                formatted_row = [re.sub('\s+', ' ', str(e)) for e in row]
                writer.writerow(formatted_row)
    
    os.replace(output_filepath, input_filepath)


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
    num_lines = count_lines(input_filepath)
    if model_version == '1':
        return 0.2725 * num_lines + 1.3211
    return 0.0284 * num_lines + 2.2846


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

def read_file_in_chunks(file_obj, chunk_size=1024 * 1024):
    """Yield chunks of data from a file."""
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        yield chunk


def count_lines(file_path, chunk_size=1024 * 1024):
    """Count the number of lines in a file."""
    with open(file_path, 'rb') as file:
        file_chunks = read_file_in_chunks(file, chunk_size)
        newline_count = sum(chunk.count(b'\n') for chunk in file_chunks)
        return newline_count + 1
