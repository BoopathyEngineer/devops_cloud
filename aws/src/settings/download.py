import csv
import io
import boto3
from configure import LOGFOLDER, SENDERINDOX


def csv_download(obj, filename):
    success = False
    if filename:
        if isinstance(obj, list):
            headers = obj[0].keys()
            with open(filename, mode="w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                for row in obj:
                    writer.writerow(row)
                success = True
                print(f"CSV file '{filename}' has been successfully created.")
    return success


def csv_upload_to_s3_direct(obj, bucket, folder, filename):
    if isinstance(obj, dict):
        obj = obj["success"]
    success = None
    if filename and obj != []:
        # Check if the input object is a list and not empty
        if isinstance(obj, list) and obj:
            # Create an in-memory file-like object
            csv_buffer = io.StringIO()
            headers = ["S.No."] + list(obj[0].keys())

            # Write data to the in-memory file-like object
            writer = csv.DictWriter(csv_buffer, fieldnames=headers)
            writer.writeheader()
            for index, row in enumerate(obj, start=1):
                # Inserting the serial number in each row
                row_with_serial = {"S.No.": index}
                row_with_serial.update(row)
                writer.writerow(row_with_serial)

            # Move to the beginning of the StringIO buffer before reading its content for upload
            csv_buffer.seek(0)

            # Upload the file-like object to S3
            s3 = boto3.client("s3")
            s3_path = (
                f"{SENDERINDOX}/{folder}/{LOGFOLDER}/{filename}" if folder else filename
            )
            try:
                s3.put_object(Bucket=bucket, Key=s3_path, Body=csv_buffer.getvalue())
                print(
                    f"CSV file '{filename}' has been successfully uploaded to S3 bucket '{bucket}'."
                )
                return s3_path
            except Exception as e:
                print(f"Failed to upload CSV to S3: {e}")
        else:
            print("Invalid input: obj must be a non-empty list.")
    else:
        print("Invalid input: obj must be a non-empty list.")
    return success


def upload_log(bucket_name, filename, folder, text_data):
    # Initialize an S3 client
    s3 = boto3.client("s3")

    try:
        # Seek to the beginning of the StringIO object before uploading
        # text_data.seek(0)
        # if text_data.read().strip() == '':
        #     print("Log is empty, not uploading to S3.")
        #     return None

        s3_path = f"{SENDERINDOX}/{folder}/{LOGFOLDER}/{filename}" if folder else filename
        # Upload the text data as a file to S3
        s3.put_object(Bucket=bucket_name, Key=s3_path, Body=text_data)
        print(f"Log file successfully uploaded this path{s3_path}")
        return s3_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
