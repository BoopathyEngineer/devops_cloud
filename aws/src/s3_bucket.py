import boto3

from configure import BUCKET_NAME

s3 = boto3.client("s3")
from helper import *
from io import BytesIO

## S3 configurations
s3 = boto3.client("s3")
s3_resource = boto3.resource("s3")


def file_extension(file):
    if file.lower().endswith(".pdf"):
        content_type = 'application/pdf'
    elif file.lower().endswith(".docx"):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif file.lower().endswith(".doc"):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif file.lower().endswith(".txt"):
        content_type = 'text/plain'
    else:
        content_type = 'application/pdf'
    return content_type


def s3_Storage(post_data, folder, filename):
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(BUCKET_NAME)
    content_type = file_extension(filename)
    # TODO: Add to the Permission for S3 bucket
    response = bucket.put_object(
        Bucket=BUCKET_NAME, ContentType=content_type, Key=folder, Body=post_data
    )
    response = s3_file_download(BUCKET_NAME, folder, filename)
    return response


def s3_file_download(bucket, path,filename):
    tika_content = None
    try:
        file_obj = BytesIO()
        response = s3.download_fileobj(bucket, path, file_obj)
        tika_content = extract_text_from_pdf(file_obj, filename)
    except Exception as e:
        print(f"Error downloading file: {e}")
    return tika_content


"""
create S3 folder inside a bucket
"""


def put_folder(bucket, folder):
    if "/" not in folder:
        folder = folder + "/"
    response = s3.put_object(Bucket=bucket, Key=folder)
    return response


def put_object(bucket, folder, filename, content):
    #: TODO
    s3 = boto3.resource("s3")
    s3_bucket = s3.Bucket(bucket)
    content_type = file_extension(filename)
    response = s3_bucket.put_object(
        Bucket=bucket, ContentType=content_type, Key=folder, Body=content
    )
    return response


def delete_folder(BUCKET, folder_path):
    # List and delete all objects in the folder
    success = False
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(BUCKET)
    for obj in bucket.objects.filter(Prefix=folder_path):
        obj.delete()
        success = True
    return success


def copy_object(bucket, old_path, new_path):
    s3 = boto3.resource("s3")
    s3_client = s3.meta.client
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=old_path)
    success = False
    for item in response.get("Contents", []):
        copy_source = {"Bucket": bucket, "Key": item["Key"]}
        new_key = item["Key"].replace(old_path, new_path)
        # Copy object to new destination within the same bucket
        success = s3_client.copy_object(
            Bucket=bucket, CopySource=copy_source, Key=new_key
        )
    return success


"""
Here Its a S3 retrieve all filenames
"""


def get_folder_files(bucket, folder):
    success = False
    if not folder.endswith("/"):
        folder += "/"
    s3_client = s3_resource.meta.client
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=folder)
    exists_file = []
    if response.get("Contents"):
        for obj in response["Contents"]:
            file_name = obj["Key"].replace(folder, "", 1)
            if file_name != "":
                exists_file.append(file_name)
        success = True
    return success, exists_file
