import os
from configparser import SafeConfigParser

class Util:
    def __init__(self, filename):
        config = SafeConfigParser()
        config.read(filename)

        # Folder settings
        #self.INPUT_DATA_PATH = config.get('folders', 'input_data_path')
        #if not os.path.exists(self.INPUT_DATA_PATH):
        #    os.makedirs(self.INPUT_DATA_PATH)

        #self.OUTPUT_DATA_PATH = config.get('folders', 'output_data_path')
        #if not os.path.exists(self.OUTPUT_DATA_PATH):
        #    os.makedirs(self.OUTPUT_DATA_PATH)


        # S3 settings
        self.INPUT_BUCKET = config.get('s3', 'input_bucket')
        self.OUTPUT_BUCKET = config.get('s3', 'output_bucket')
        self.URL_EXPIRE_TIME = int(config.get('s3', 'url_expire_time'))
        self.S3_INPUT_FOLDER = config.get('s3', 'input_folder')
        self.S3_OUTPUT_FOLDER = config.get('s3', 'output_folder')

        # SQS settings
        self.QUEUE_NAME = config.get('sqs', 'queue_name')
        self.VISIBILITY_TIMEOUT = int(config.get('sqs', 'visibility_timeout'))
        self.QUEUE_LONG_PULL_TIME = int(config.get('sqs', 'queue_long_pull_time'))
        self.QUEUE_MSG_RETENTION = int(config.get('sqs','queue_msg_retention_seconds'))
        self.PULL_DELAY = int(config.get('sqs','pull_delay'))

    #def getInputFilePath(self, id):
    #    return self.getFilePath(self.INPUT_DATA_PATH, id)

    #def getOutputFilePath(self, id):
    #    return self.getFilePath(self.OUTPUT_DATA_PATH, id)

    def getInputFileKey(self, id):
        return (self.S3_INPUT_FOLDER + id)

    def getOutputFileKey(self, id):
        return (self.S3_OUTPUT_FOLDER + id)

    def getFilePath(self, path, id):
        return os.path.join(path + id)