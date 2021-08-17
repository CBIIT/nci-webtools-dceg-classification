import logging
import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import makedirs, walk, path
from smtplib import SMTP
from configparser import ConfigParser
from jinja2 import Template
from zipfile import ZipFile, ZIP_DEFLATED
from logging.handlers import RotatingFileHandler


def make_dirs(*dirs):
    """ Creates directories using the same behavior as `mkdir -p` """
    for dir in dirs:
        if not path.isdir(dir):
            makedirs(dir)


def read_config(filepath='config.ini'):
    """ Reads a configuration file as a dictionary """
    config = ConfigParser()
    config.optionxform = str
    config.read(filepath)
    return config._sections


def render_template(filepath, data):
    """ Renders a template given a filepath and template variables """
    with open(filepath) as template_file:
        template = Template(template_file.read())
        return template.render(data)


def send_mail(host, sender, recipient, subject, contents):
    """ Sends an email """
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.attach(MIMEText(contents, 'html'))

    smtp = SMTP(host)
    smtp.sendmail(sender, recipient, msg.as_string())


def createArchive(targetDirectory):
    rootDir = path.basename(targetDirectory)
    try:
        with ZipFile(targetDirectory + '.zip', "w", ZIP_DEFLATED) as archive:
            for dirpath, dirnames, filenames in walk(targetDirectory):
                for filename in filenames:
                    filepath = path.join(dirpath, filename)
                    parentpath = path.relpath(filepath, targetDirectory)
                    arcname = path.join(rootDir, parentpath)
                    archive.write(filepath, arcname)
        return targetDirectory + '.zip'
    except Exception as err:
        return False


def create_rotating_log(name, config):
    if not path.exists('../logs'):
        makedirs('../logs')
    config = config['logs']
    size = int(config['size'])
    rollover = int(config['rollover'])

    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                  '%Y-%m-%d %H:%M:%S')
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H")
    logFile = f'../logs/{name}.log.' + time

    my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=size,
                                     backupCount=rollover, encoding=None, delay=0)
    my_handler.setFormatter(formatter)
    my_handler.setLevel(config['loglevel'])

    logger = logging.getLogger('root')
    logger.setLevel(config['loglevel'])

    logger.addHandler(my_handler)
    return logger
