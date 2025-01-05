
from settings.aws_service import textract,s3

'''
Here Its Amazon textract Parser Function For OCR
'''

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
        time.sleep(45)

    # Print or process the response if succeeded
    if status_string == 'SUCCEEDED':
        parsed_text = ""
        for id,block in enumerate(status['Blocks']):
            if block['BlockType'] == 'LINE':
                parsed_text += block['Text'] + "\n"

        return parsed_text
    else:
        return None        



