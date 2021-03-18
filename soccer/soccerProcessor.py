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
from wrapper import code_file, plot_results

from jinja2 import Template
from util import Util
from sqs import Queue, VisibilityExtender
from s3 import S3Bucket

class Processor(Listener):

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def process_file(self, file_id, model_version):
        """ Codes the input file to different SOC categories """

        # get configuration
        config = self.config['soccer']
        input_dir = config['input_dir']
        output_dir = config['output_dir']
        model_filepath = config['model_file']

        # specify input/output filepaths
        input_filepath = safe_join(input_dir, file_id)
        output_path = safe_join(output_dir, file_id)
        output_filepath = output_path + '.csv'
        plot_filepath = output_path + '.png'

        # save parameters as json file
        with open(output_path + '.json', 'w') as f:
            json.dump({
                'file_id': file_id,
                'model_version': model_version
            }, f)

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

    def create_rotating_log(config):
        if not os.path.exists('../logs'):
            os.makedirs('../logs')

        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                    '%Y-%m-%d %H:%M:%S')
        time = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M")
        logFile = '../logs/queue.log.' + time

        size = config.LOG_SIZE
        rollover = config.LOG_ROLLOVER

        my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=size,
                                        backupCount=rollover, encoding=None, delay=0)
        my_handler.setFormatter(formatter)
        my_handler.setLevel(config.LOG_LEVEL)

        logger = logging.getLogger('root')
        logger.setLevel(config.LOG_LEVEL)

        logger.addHandler(my_handler)
        return logger

    def calculate(WORKING_DIR,soccerData,timestamp,logger):
        

    @defer.inlineCallbacks
    def run(self):
        ''' Initializes the stompest async client '''
        queue_url = self.config['queue']['url']
        queue_name = self.config['queue']['name']
        error_queue_name = self.config['queue']['error_name']

        logger = create_rotatating_log(self.config)

        try:
            sqs = Queue(logger,self.config)
            logger.info("SOCcer processor has started")
            while True:
                for msg in sqs.receiveMsgs():
                    extender = None
                    try:
                        data = json.loads(msg.body)
                        if data:
                            jobName = 'SOCcer'
                            token = data['jobId']
                            parameters = data['parameters']
                            bucketName = parameters['bucket_name']
                            s3Key = parameters['key']
                            timestamp = parameters['timestamp']
                            soccerData = parameters['data']

                            bucket = S3Bucket(bucketName, logger)

                            extender = VisibilityExtender(msg,jobName,token,self.config.VISIBILITY_TIMEOUT,logger)
                            
                            logger.info('Start processing job name: "{}", token: {} ...'.format(jobName, token))

                            extender.start()

                            saveLoc = os.path.join(self.config.INPUT_DATA_PATH, token)
                            savePath = os.path.join(self.config.INPUT_DATA_PATH, f'{token}.zip')
                            WORKING_DIR = os.path.join(os.getcwd(), saveLoc)

                            # download work file archive
                            bucket.downloadFile(s3Key, savePath)

                            # extract work files
                            with ZipFile(savePath) as archive:
                                archive.extractall(self.config.INPUT_DATA_PATH)


                            try:
                                saveLoc = self.config.createArchive(WORKING_DIR)

                                if saveLoc:
                                    with open(savePath, 'rb') as archive:
                                        object = bucket.uploadFileObj(self.config.getInputFileKey(f'{token}.zip'), archive)
                                        if object:
                                            logger.info(f'Succesfully Uploaded {token}.zip')
                                        else:
                                            logger.error(f'Failed to upload {token}.zip')
                                        
                                    composeSuccess(WORKING_DIR, soccerData, timestamp, logger)
                            except Exception as err:
                                logger.error(f'Failed to upload {token}.zip')
                                composeFail(WORKING_DIR, soccerData, timestamp, logger)

                            msg.delete()
                            logger.info(f'Finish processing job name: {jobName}, token: {token} !')
                        else:
                            logger.debug(data)
                            logger.error('Unknown message type!')
                            msg.delete()        
                    except Exception as e:
                        logger.exception(e)
                    finally:
                        if extender:
                            extender.stop()
        except KeyboardInterrupt:
            logger.info("\nBye!")
            sys.exit()
        except Exception as e:
            logger.exception(e)
            logger.error('Failed to connect to SQS queue')

    def composeFail(WORKING_DIR, params, timestamp, logger):
        logger.info('Composing error email')
        self.logger.debug(params)

        error_info = {
            'file_id': params['file_id'],
            'params': json.dumps(params, indent=4),
            'exception_info': format_exc(),
            'process_output': getattr(e, 'output', 'None')
        }
        self.logger.exception(error_info)

        token = data['tokenId']

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
            recipient=self.config['mail']['support'],
            subject='SOCcer - Exception occurred',
            contents=render_template('templates/admin_error_email.html', error_info)
        )

    def composeSuccess(WORKING_DIR, params, timestamp, logger):
        logger.info('Composing success email')

         self.logger.debug(params)
         

        # call submit method of flask application
        # generates output file and
        self.logger.debug('processing input file: ' + params['file_id'])
        self.process_file(params['file_id'], params['model_version'])
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


    def consume(self, client, frame):
        ''' Consumes a frame from the queue '''
        try:
            # get configuration
            mail_host = self.config['mail']['host']

            # get parameters
            params = json.loads(frame.body.decode())
            self.logger.debug(params)

            # call submit method of flask application
            # generates output file and
            self.logger.debug('processing input file: ' + params['file_id'])
            self.process_file(params['file_id'], params['model_version'])
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
                recipient=self.config['mail']['support'],
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
