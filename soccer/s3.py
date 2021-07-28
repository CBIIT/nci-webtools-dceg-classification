import boto3


class S3Bucket:
    def __init__(self, bucket, log):
        self.client = boto3.client('s3')
        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(bucket)
        self.log = log

    def uploadFileObj(self, key, data):
        return self.bucket.put_object(Key=key, Body=data)

    def downloadFile(self, key, filename):
        return self.bucket.download_file(key, filename)

    def downloadFileObj(self, key, obj):
        self.bucket.download_fileobj(key, obj)

    def deleteFile(self, key):
        response = self.bucket.delete_objects(
            Delete={
                'Objects': [
                    {
                        'Key': key
                    }
                ]
            }
        )
        if 'Errors' in response:
            self.log.error('S3: delete file {} failed!'.format(key))
            return False
        else:
            return True

    def uploadFile(self, key, fileName):
        with open(fileName, 'rb') as data:
            object = self.uploadFileObj(key, data)
            if object:
                return {'bucket': self.bucket.name, 'key': key}
            else:
                message = "Upload file {} to S3 failed!".format(fileName)
                self.log.error(message)
                return None
