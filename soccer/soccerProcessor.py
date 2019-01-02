import json
import logging
from twisted.internet import defer, reactor
from subprocess import CalledProcessError, check_call
from stompest.config import StompConfig
from stompest.protocol import StompSpec
from stompest.async import Stomp
from stompest.async.listener import Listener, SubscriptionListener
from stompest.error import StompConnectionError
from traceback import format_exc
from werkzeug.security import safe_join
from werkzeug.test import Client
from utils import read_config, send_mail, render_template
from wrapper import code_file
import soccer

class Processor(Listener):

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    @defer.inlineCallbacks
    def run(self):
        ''' Initializes the stompest async client '''
        queue_url = self.config['queue']['url']
        queue_name = self.config['queue']['name']
        error_queue_name = self.config['queue']['error_name']

        client = Stomp(StompConfig(queue_url))
        yield client.connect()

        client.subscribe(
            queue_name,  # must begin with leading slash (eg: /queue/)
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
            # get configuration
            mail_host = self.config['mail']['host']

            # get parameters
            params = json.loads(frame.body.decode())
            self.logger.debug('received parameters: ' + params)

            # call submit method of flask application
            # generates output file and
            self.logger.debug('processing input file: ' + params['file_id'])
            client = Client(soccer.app)
            client.post('/submit', data=params)
            self.logger.debug('finished processing input file: ' + params['file_id'])

            # send user results
            self.logger.debug('sending results email to user')
            send_mail(
                host=mail_host,
                sender='SOCcer<do.not.reply@nih.gov>',
                recipient=params['recipient'],
                subject='SOCcer - Your file has been processed',
                contents=render_template('templates/user_email.html', params)
            )

        except Exception as e:
            # capture error information
            error_info = {
                'file_id': params['file_id'],
                'params': json.dumps(params, indent=4),
                'exception_info': format_exc(),
                'process_output': getattr(e, 'output', 'None')
            }
            self.logger.exception(error_info)

            # send user error email
            self.logger.debug('sending error email to user')
            send_mail(
                host=mail_host,
                sender='SOCcer<do.not.reply@nih.gov>',
                recipient=params['recipient'],
                subject='SOCcer - An error occurred while processing your file',
                contents=render_template('templates/user_error_email.html', params)
            )

            # send admin error email
            self.logger.debug('sending error email to administrator')
            send_mail(
                host=mail_host,
                sender='SOCcer<do.not.reply@nih.gov>',
                recipient=self.config['mail']['admin'],
                subject='SOCcer - Exception occurred',
                contents=render_template('templates/admin_error_email.html', error_info)
            )

    def onConnectionLost(self, connection, reason):
        ''' Restart the client if we lost the connection '''
        self.run()


if __name__ == '__main__':
    import argparse
    logging.basicConfig(level=logging.DEBUG)
    config = read_config('config.ini')
    Processor(config).run()
    reactor.run()
