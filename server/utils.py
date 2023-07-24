import logging
from sys import stdout
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from jinja2 import Template

DEFAULT_LOG_FORMAT = "[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"

def get_logger(
    name = __name__,
    level = logging.INFO,
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)
):
    """ Returns a logger with the specified name and level that logs to stdout """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler(stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

def render_template(filepath: str, data: dict):
    """ Renders a template given a filepath and template variables """
    with open(filepath, encoding="utf-8") as template_file:
        template = Template(template_file.read())
        return template.render(data)


def send_mail(sender: str, recipient: str, subject: str, contents: str, env: dict):
    """ Sends an email """

    # get SMTP settings from environment
    host = env.get("EMAIL_SMTP_HOST")
    port = int(env.get("EMAIL_SMTP_PORT", 25))
    user = env.get("EMAIL_SMTP_USER")
    password = env.get("EMAIL_SMTP_PASSWORD")

    # create message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.attach(MIMEText(contents, 'html'))

    smtp = SMTP(host, port)

    if user and password:
        smtp.starttls()
        smtp.login(user, password)

    smtp.sendmail(sender, recipient, msg.as_string())
    smtp.quit()

