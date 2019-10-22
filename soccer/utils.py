from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import makedirs, linesep, path
from smtplib import SMTP
from configparser import ConfigParser

from jinja2 import Template
from stompest.config import StompConfig
from stompest.sync import Stomp


def enqueue(queue_url, queue_name, data):
    """ Sends a message to a queue """
    client = Stomp(StompConfig(queue_url))
    client.connect()
    client.send(queue_name, data.encode())
    client.disconnect()


def make_dirs(*dirs):
    """ Creates directories using the same behavior as `mkdir -p` """
    for dir in dirs:
        if not path.isdir(dir):
            makedirs(dir)


def read_config(filepath='config.ini'):
    """ Reads a configuration file as a dictionary """
    config = ConfigParser()
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
