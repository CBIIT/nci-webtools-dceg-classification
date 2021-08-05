import json
import sys

from os import path, getcwd
from zipfile import ZipFile
from traceback import format_exc
from werkzeug.security import safe_join
from wrapper import code_file, plot_results
from utils import createArchive, read_config, create_rotating_log, send_mail, render_template, make_dirs
from sqs import Queue, VisibilityExtender
from s3 import S3Bucket


def process_file(config, file_id, input_file, model_version):
    """ Codes the input file to different SOC categories """

    # get configuration
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    model_filepath = config['model_file_1.1']

    # specify input/output filepaths
    input_filepath = safe_join(input_dir, file_id, input_file)
    output_path = safe_join(output_dir, file_id)
    output_filepath = safe_join(output_dir, file_id, file_id + '.csv')
    plot_filepath = safe_join(output_dir, file_id, file_id + '.png')

    # save parameters as json file
    with open(safe_join(output_dir, file_id, file_id + '.json'), 'w') as f:
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


if __name__ == '__main__':

    config = read_config('../config/config.ini')
    logger = create_rotating_log('queue', config)
    make_dirs(config['soccer']['input_dir'])

    try:
        logger.info("SOCcer processor has started")
        sqs = Queue(logger, config)
        while True:
            for msg in sqs.receiveMsgs():
                extender = None
                try:
                    params = json.loads(msg.body)
                    if params:
                        jobName = 'SOCcer'
                        file_id = params['file_id']
                        mail_host = config['mail']['host']
                        extender = VisibilityExtender(
                            msg, jobName, file_id, int(config['sqs']['visibility_timeout']), logger)

                        logger.info(
                            'Start processing job name: "{}", file_id: {}'.format(jobName, file_id))

                        extender.start()

                        # specify paths
                        input_dir = config['soccer']['input_dir']
                        input_archive_path = path.join(
                            config['soccer']['input_dir'], f'{file_id}.zip')
                        WORKING_DIR = path.join(getcwd(), input_dir, file_id)

                        # download input file archive
                        s3Key = path.join(
                            config['s3']['input_folder'], file_id + '.zip')
                        bucketName = config['s3']['bucket']
                        bucket = S3Bucket(bucketName, logger)
                        bucket.downloadFile(s3Key, input_archive_path)

                        # extract input files
                        with ZipFile(input_archive_path) as archive:
                            archive.extractall(input_dir)

                        try:
                            # call submit method of flask application
                            # generates output file and
                            logger.debug(
                                'processing input file: ' + params['file_id'])
                            process_file(
                                config['soccer'], file_id, params['original_filename'], params['model_version'])
                            logger.debug(
                                'finished processing input file: ' + params['file_id'])

                            # zip and upload to s3 and send email
                            output_dir_archive = createArchive(WORKING_DIR)

                            if output_dir_archive:
                                with open(output_dir_archive, 'rb') as archive:
                                    object = bucket.uploadFileObj(
                                        path.join(config['s3']['output_folder'], f'{file_id}.zip'), archive)
                                    if object:
                                        logger.info(
                                            f'Succesfully Uploaded {file_id}.zip')
                                    else:
                                        logger.error(
                                            f'Failed to upload {file_id}.zip')

                                # send user results
                                logger.debug(
                                    'sending results email to user')
                                send_mail(
                                    host=config['mail']['host'],
                                    sender=config['mail']['sender'],
                                    recipient=params['recipient'],
                                    subject='SOCcer - Your file has been processed',
                                    contents=render_template(
                                        'templates/user_email.html', {**params, 'admin': config['mail']['admin']})
                                )

                        except Exception as e:
                            # capture error information
                            error_info = {
                                'file_id': params['file_id'],
                                'params': json.dumps(params, indent=4),
                                'exception_info': format_exc(),
                                'process_output': getattr(e, 'output', 'None'),
                                'admin': config['mail']['admin']
                            }
                            logger.exception(error_info)

                            # send user error email
                            logger.debug('sending error email to user')
                            send_mail(
                                host=mail_host,
                                sender=config['mail']['sender'],
                                recipient=params['recipient'],
                                subject='SOCcer - An error occurred while processing your file',
                                contents=render_template(
                                    'templates/user_error_email.html', {**params, 'admin': config['mail']['admin']})
                            )

                            # send admin error email
                            logger.debug(
                                'sending error email to administrator')
                            send_mail(
                                host=mail_host,
                                sender=config['mail']['sender'],
                                admin=config['mail']['admin'],
                                recipient=config['mail']['support'],
                                subject='SOCcer - Exception occurred',
                                contents=render_template(
                                    'templates/admin_error_email.html', error_info)
                            )

                        msg.delete()
                        logger.info(
                            f'Finish processing job name: {jobName}, file_id: {file_id} !')
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
