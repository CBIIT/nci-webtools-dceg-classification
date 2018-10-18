import json
import logging
from ConfigParser import SafeConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from twisted.internet import defer, reactor
from smtplib import SMTP
from soccer import get_config, call_soccer
from subprocess import CalledProcessError, check_call
from stompest.config import StompConfig
from stompest.protocol import StompSpec
from stompest.async import Stomp
from stompest.async.listener import Listener, SubscriptionListener
from stompest.error import StompConnectionError
from traceback import format_exc
from werkzeug.security import safe_join


class SOCcerProcessor(Listener):

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def process_file(self, file_id, model_version):
        ''' Codes an input file and generates the output plot '''
        input_dir = self.config['soccer']['input_dir']
        output_dir = self.config['soccer']['output_dir']
        model_filepath = self.config['soccer']['model_file']

        input_filepath = safe_join(input_dir, file_id)
        output_filepath = safe_join(output_dir, file_id + '.csv')
        plot_filepath = safe_join(output_dir, file_id + '.png')

        # code file
        call_soccer(
            'code-file',
            input_filepath=input_filepath,
            output_filepath=output_filepath,
            model_version=model_version,
            model_filepath=model_filepath
        )

        # generate plot
        check_call([
            'Rscript', 'soccerResultPlot.R',
            output_filepath, plot_filepath
        ])

    def send_mail(self, sender, recipient, subject, contents):
        ''' Sends an email '''
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        msg.attach(MIMEText(contents, 'html'))

        smtp = SMTP(self.config['mail']['host'])
        smtp.sendmail(sender, recipient, msg.as_string())

    @staticmethod
    def render_template(filepath, data):
        ''' Renders a template given a filepath and environment '''
        with open(filepath) as template_file:
            template = Template(template_file.read())
            return template.render(data)

    @defer.inlineCallbacks
    def run(self):
        ''' Initializes the stompest async client '''
        queue_url = self.config['queue']['url']
        queue_name = self.config['queue']['name']
        error_queue_name = self.config['queue']['error_name']

        client = Stomp(StompConfig(queue_url))
        yield client.connect()

        client.subscribe(
            queue_name,  # must begin with /queue/
            headers={StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL},
            listener=SubscriptionListener(
                self.consume,
                errorDestination=error_queue_name
            )
        )

        client.add(self)

    def consume(self, client, frame):
        ''' Consumes a frame from the queue '''
        try:
            data = json.loads(frame.body.decode())
            self.logger.debug(data)

            # code file and generate plot
            self.process_file(
                data['file_id'],
                data['model_version'],
            )
            self.logger.debug('processed input file: ' + data['file_id'])

            # send user results
            self.send_mail(
                'SOCcer<do.not.reply@nih.gov>',
                data['email'],
                'SOCcer - Your file has been processed',
                self.render_template('templates/user_email.html', data)
            )
            self.logger.debug('sent results email to user')

        except Exception as e:
            # capture error information
            error_info = {
                'file_id': data['file_id'],
                'data': json.dumps(data, indent=4),
                'exception_info': format_exc(),
                'process_output': getattr(e, 'output', 'None')
            }

            self.logger.exception(error_info)

            # send user error email
            self.send_mail(
                'SOCcer<do.not.reply@nih.gov>',
                data['email'],
                'SOCcer - An error occurred while processing your file',
                self.render_template('templates/user_error_email.html', data)
            )
            self.logger.debug('sent error email to user')

            # send admin error email
            self.send_mail(
                'SOCcer<do.not.reply@nih.gov>',
                self.config['mail']['admin'],
                'SOCcer - Exception occurred',
                self.render_template('templates/admin_error_email.html', error_info)
            )
            self.logger.debug('sent error email to administrator')

    def onConnectionLost(self, connection, reason):
        ''' Restart the client if we lost the connection '''
        self.run()


if __name__ == '__main__':
    import argparse
    logging.basicConfig(level=logging.DEBUG)
    config = get_config('config.ini')
    SOCcerProcessor(config).run()
    reactor.run()
