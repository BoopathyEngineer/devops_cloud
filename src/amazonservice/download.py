import csv
import io
import boto3
# from settings.configuration import LOGFOLDER, SENDERINDOX
from settings.aws_service import s3_client
from s3_bucket import generate_url
from botocore.exceptions import NoCredentialsError

# CSV file download in local path
def csv_download(datalist:list,filename:str):
    success = False
    if filename:
        if isinstance(datalist,list):
            headers = datalist[0].keys()
            with open(filename, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                for row in datalist:
                    writer.writerow(row)
                success = True
                print(f"CSV file '{filename}' has been successfully created.")
    return success

# CSV file download in S3 path
def csv_upload_to_s3_direct(datalist:list,bucket:str,folder:str,filename:str,email= None):
    success = None
    if filename and datalist != []:
        # Check if the input object is a list and not empty
        if isinstance(datalist, list) and datalist:
            # Create an in-memory file-like object
            csv_buffer = io.StringIO()
            overall_header = 'User ID'
            headers = ['S.No.'] + list(datalist[0].keys())
            csv_buffer.write(f"{overall_header}: {email}\n")
            
            # Write data to the in-memory file-like object
            writer = csv.DictWriter(csv_buffer, fieldnames=headers)
            writer.writeheader()
            for index, row in enumerate(datalist, start=1):
                # Inserting the serial number in each row
                row_with_serial = {'S.No.': index}
                row_with_serial.update(row)
                writer.writerow(row_with_serial)

            # Move to the beginning of the StringIO buffer before reading its content for upload
            csv_buffer.seek(0)
            # Upload the file-like object to S3
            s3_path = f"{folder}/{filename}" if folder else filename
            try:
                file_response = s3_client.put_object(Bucket=bucket, Key=s3_path, Body=csv_buffer.getvalue())
                print("file_response\n",file_response)
                print(f"CSV file '{filename}' has been successfully uploaded to S3 bucket '{bucket}'.")
                object_url = generate_url(bucket,s3_path)
                return object_url
            except Exception as e:
                print(f"Failed to upload CSV to S3: {e}")
        else:
            print("Invalid input: obj must be a non-empty list.")
    else:
        print("Invalid input: obj must be a non-empty list.")
    return success


# Txt file download in S3 path
def upload_log(bucket:str, filename:str,folder:str, text_data):
    # Initialize an S3 client
    s3 = boto3.client('s3')

    try:
        # Seek to the beginning of the StringIO object before uploading
        text_data.seek(0)
        if text_data.read().strip() == '':
            print("Log is empty, not uploading to S3.")
            return None
        s3_path = f"{SENDERINDOX}/{folder}/{LOGFOLDER}/{filename}" if folder else filename
        # Upload the text data as a file to S3
        s3_client.put_object(Bucket=bucket, Key=s3_path, Body=text_data.read())
        print(f"Log file successfully uploaded this path{s3_path}")
        return s3_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

def upload_s3_files(bucket,folder,filename,content):
    try:
        s3_path = f"{folder}/{filename}" if folder else filename
        s3_client.put_object(Bucket=bucket, Key=s3_path, Body=content)
        object_url = generate_url(bucket,s3_path)
        print(f"Invoice successfully uploaded to {s3_path}")
        return object_url
    except NoCredentialsError:
        print("Credentials not available")
