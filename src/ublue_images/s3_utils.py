import boto3
from botocore.exceptions import ClientError
from loguru import logger

S3 = boto3.client("s3")


def upload_file(file_name, bucket, object_name=None):
    try:
        S3.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logger.error(e)
        return False
    return True
