from ast import Dict
from typing import Optional
from settings.configuration import DEV_S3BUCKET, JD_PARSER_ERROR, RESUME_PARSER_ERROR
from settings.aws_service import s3,textract,s3_client
from helper import bytes_extract,extract_text_from_pdf
from io import BytesIO
from settings.constants import BUCKETNAME, CONFIGTABLE
from settings.env import get_env_vars




def file_extension(file):
    if file.endswith(".pdf"):
        content_type = 'application/pdf'
    elif file.endswith(".docx"):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif file.endswith(".doc"):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif file.endswith(".txt"):
        content_type = 'text/plain'
    else:
        content_type = 'application/pdf'
        raise ValueError("Unsupported file format")
    return content_type

 

def s3_Storage(post_data,path,folder):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    AWS_BUCKET_NAME = "zita" #env_vars.get(BUCKETNAME,'zita-featurez24-297')

    bucket = s3.Bucket(AWS_BUCKET_NAME)
    if post_data['isfile'] == True:
        filename = post_data['filename']
        post_data = post_data['content']
        #TODO: Add to the Permission for S3 bucket
        response = bucket.put_object(
            Bucket=AWS_BUCKET_NAME,
            ContentType=file_extension(filename),
            Key= folder + path,
            Body=post_data
        )
        response = s3_file_download(AWS_BUCKET_NAME,folder + path,filename)
        return response
    else:
        response = bytes_extract(post_data['content'])
        return response

def s3_file_download(bucket, path,filename):
    tika_content = None
    try:    
        file_obj = BytesIO()
        response = s3_client.download_fileobj(bucket, path, file_obj)
        tika_content = extract_text_from_pdf(file_obj,filename)
        if tika_content:
            tika_content = "".join(tika_content.split())
        # tika_content = amazon_textract_parser(bucket,path)
    except Exception as e:
        print(f"Error downloading file: {e}")
    return tika_content


def amazon_textract_parser(bucket,file_path):
    # Call Amazon Textract
    response = textract.start_document_analysis(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucket,
                'Name': file_path
                }},
        FeatureTypes=['TABLES','FORMS']
    )

    job_id = response['JobId']
    # Check the status of the job
    while True:
        status = textract.get_document_analysis(JobId=job_id)
        status_string = status['JobStatus']
        
        if status_string in ['SUCCEEDED', 'FAILED']:
            break
        # Optionally, wait before checking the status again
        import time
        time.sleep(5)

    # Print or process the response if succeeded
    if status_string == 'SUCCEEDED':
        parsed_text = ""
        for id,block in enumerate(status['Blocks']):
            if block['BlockType'] == 'LINE':
                parsed_text += block['Text'] + "\n"

        return parsed_text
    else:
        print("Document analysis failed")
        return None
    

def generate_url(bucket,path):
    url = s3_client.generate_presigned_url('get_object',
        Params={
            'Bucket': bucket,
            'Key': path
        },
        ExpiresIn=3600  # URL expiration time in seconds
    )
    return url
