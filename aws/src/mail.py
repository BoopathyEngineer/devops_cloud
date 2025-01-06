import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from configure import REGION
from templates.raw_format import DUPLICATE_EMAIL_CONTENT

# Create a new SES resource and specify a region.
client = boto3.client("ses")
s3_client = boto3.client("s3")
ses_client = boto3.client("ses", region_name=REGION)


# send mail
def sendmail(receipt, message, sender):
    success = False
    destination = {"ToAddresses": [receipt]}
    response = client.send_email(
        Destination=destination, Message=message, SENDER=sender
    )
    if response.get("MessageId", None):
        success = True
    return success


'''

#########-----------Send Mail function reference-------------##########

# Replace the following values with your own
SENDER = "dcqc@yopmail.com"
RECIPIENT = "dcqc@yopmail.com"
AWS_REGION = "us-east-1"
SUBJECT = "Test Email from SES"
BODY_TEXT = "This is a test email sent from Amazon SES using the AWS SDK for Python (Boto3)."
BODY_HTML = """<html>
<head></head>
<body>
  <h1>Amazon SES Test Email (SDK for Python)</h1>
  <p>This email was sent with
    <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
    <a href='https://boto3.amazonaws.com/v1/documentation/api/latest/index.html'>AWS SDK for Python (Boto3)</a>.</p>
</body>
</html>
"""
CHARSET = "UTF-8"

# Try to send the email.
try:
    # Provide the contents of the email.
    response = client.send_email(
        Destination={
            'ToAddresses': [
                RECIPIENT,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': CHARSET,
                    'Data': BODY_HTML,
                },
                'Text': {
                    'Charset': CHARSET,
                    'Data': BODY_TEXT,
                },
            },
            'Subject': {
                'Charset': CHARSET,
                'Data': SUBJECT,
            },
        },
        Source=SENDER,
    )
# Display an error if something goes wrong.    
except (NoCredentialsError, PartialCredentialsError) as e:
    print("Credentials not available", e)
except Exception as e:
    print("Error sending email", e)
else:
    print("Email sent! Message ID:"),
    print(response['MessageId'])

'''

######## Attachment Reference ############


def send_raw_mail(obj):
    success = False
    try:
        subject = obj["subject"]
        sender = obj["sender"]
        recipent = obj["recipent"]
        body_html = obj["body"]
        CHARSET = "UTF-8"
        BUCKET_NAME = obj["bucket"]
        FILE_KEYS = obj["files"]
        if isinstance(FILE_KEYS, list):
            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipent
            msg_body = MIMEMultipart("alternative")
            # Encode the text and HTML content and attach it to the child container
            textpart = MIMEText(body_html.encode(CHARSET), "plain", CHARSET)
            htmlpart = MIMEText(body_html.encode(CHARSET), "html", CHARSET)
            msg_body.attach(textpart)
            msg_body.attach(htmlpart)
            # Attach the multipart/alternative child container to the multipart/mixed parent container
            msg.attach(msg_body)
            for i in FILE_KEYS:
                # Download the file from S3
                if i != None:
                    key = i
                    s3_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
                    file_content = s3_response["Body"].read()
                    file_name = i.split("/")[-1]

                    # file_name = i['filename']
                    # file_content = base64.b64decode(i['content'])
                    attachment = MIMEApplication(file_content)
                    attachment.add_header(
                        "Content-Disposition", "attachment", filename=file_name
                    )
                    msg.attach(attachment)
            send_args = {
                "Source": sender,
                "Destinations": [recipent],
                "RawMessage": {"Data": msg.as_string()},
            }
            CONFIGURATION_SET = None
            if CONFIGURATION_SET:
                send_args["ConfigurationSetName"] = CONFIGURATION_SET
            response = ses_client.send_raw_email(**send_args)
            if response.get("MessageId", None):
                success = True
        else:
            response = "must pass the values in files in list format"
    except ClientError as e:
        print(e.response["Error"]["Message"])
    else:
        print(response["MessageId"])
    return success


"""


import boto3
import base64
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Create a new SES client
ses_client = boto3.client('ses', region_name='us-east-1')

# Create a new S3 client
s3_client = boto3.client('s3')

# Replace with your sender and recipient email addresses
SENDER = "dcqc@yopmail.com"
RECIPIENT = "dcqc@yopmail.com"

# The subject line for the email
SUBJECT = "Amazon SES Test with Attachments (SDK for Python)"

# The email body for recipients with non-HTML email clients
# BODY_TEXT = ("Amazon SES Test with Attachments\r\n"
#              "This email was sent with Amazon SES using the "
#              "AWS SDK for Python (Boto)."
#             )

# The HTML body of the email
BODY_HTML = DUPLICATE_EMAIL_CONTENT.format(
    receipt = 'hello',
    folder_name = 'zita'
)

# The character encoding for the email
CHARSET = "UTF-8"

# The S3 bucket and file key
BUCKET_NAME = "zita"
FILE_KEYS = ["Jd/Physical_therapist.docx","Jd/Abhi_Ray.pdf.pdf"]

# Create a multipart/mixed parent container
msg = MIMEMultipart('mixed')
msg['Subject'] = SUBJECT
msg['From'] = SENDER
msg['To'] = RECIPIENT

# Create a multipart/alternative child container
msg_body = MIMEMultipart('alternative')

# Encode the text and HTML content and attach it to the child container
# textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

# msg_body.attach(textpart)
msg_body.attach(htmlpart)

# Attach the multipart/alternative child container to the multipart/mixed parent container
msg.attach(msg_body)

for file_key in FILE_KEYS:
    # Download the file from S3
    s3_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
    file_content = s3_response['Body'].read()
    file_name = file_key.split('/')[-1]

    # Define the attachment part and encode it using base64
    attachment = MIMEApplication(file_content)
    attachment.add_header('Content-Disposition', 'attachment', filename=file_name)

    # Attach the file to the message
    msg.attach(attachment)

send_args = {
    'Source': SENDER,
    'Destinations': [RECIPIENT],
    'RawMessage': {'Data': msg.as_string()},
}
CONFIGURATION_SET = None
if CONFIGURATION_SET:
    send_args['ConfigurationSetName'] = CONFIGURATION_SET

# Try to send the email
try:
    response = ses_client.send_raw_email(**send_args)
except ClientError as e:
    print(e.response['Error']['Message'])
else:
    print("Email sent! Message ID:"),
    print(response['MessageId'])

"""
