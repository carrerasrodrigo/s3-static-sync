import logging
import boto3
import os
from datetime import datetime, timedelta
import gzip
import io
import mimetypes
import botocore


def normalize_folder_name(folder_name):
    if folder_name.endswith('/'):
        folder_name = folder_name[:-1]

    if folder_name.startswith('/'):
        folder_name = folder_name[1:]
    return folder_name


def guess_mime_type(file_name):
    _, ext = os.path.splitext(file_name)
    return mimetypes.types_map.get(f'{ext}', 'binary/octet-stream')


def get_client(region):
    return boto3.client("s3", region_name=region)


def gzip_content(content):
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="w") as f:
        f.write(content)
    return out.getvalue()


def upload_file(client, file_name, bucket, object_name, acl,
        header_cache_control=None, header_expires_delta=None, gzip=False):

    with open(file_name, 'rb') as f:
        content = f.read()

    params = dict(
        ACL=acl,
        Body=content,
        Bucket=bucket,
        Key=object_name,
        ContentType=guess_mime_type(file_name)
    )

    if header_cache_control is not None:
        params["CacheControl"] = header_cache_control

    if header_expires_delta is not None:
        params["Expires"] = datetime.now() + timedelta(seconds=header_expires_delta)

    if gzip:
        params["Body"] = gzip_content(content)
        params["ContentEncoding"] = "gzip"

    try:
        client.put_object(**params)
        return True, None
    except Exception as ex:
        return False, str(ex)


def check_key_exists(client, bucket, key):
    try:
        client.head_object(Bucket=bucket, Key=key)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            # Something else has gone wrong.
            raise
    return True


def list_folder_s3(s3_client, bucket, folder_path):
    params = {}
    while True:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=folder_path,
            **params)
        if response['KeyCount'] == 0:
            return
        for content in response['Contents']:
            yield content['Key']
        if not response['IsTruncated']:
            return

        params['ContinuationToken'] = response['NextContinuationToken']
