
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from settings.aws_service import ses
from settings.constants import FROM_MAIL


# send mail without attachments
def sendmail(receipt,message,sender):
    success = False
    destination={'ToAddresses': [receipt]}
    response = ses.send_email(Destination= destination,Message=message,SENDER =sender)
    if response.get('MessageId',None):
        success = True
    return success


# send mail with attachments
def send_raw_mail(obj):
    success = False
    recipent = obj['recipient']
    body_html = obj['body']
    CHARSET = "UTF-8"
    msg = MIMEMultipart('mixed')
    msg['Subject'] = obj['subject']
    msg['From'] = FROM_MAIL
    msg['To'] = obj['recipient']
    msg_body = MIMEMultipart('alternative')
    # Encode the text and HTML content and attach it to the child container
    htmlpart = MIMEText(body_html.encode(CHARSET), 'html', CHARSET)
    msg_body.attach(htmlpart)
    msg.attach(msg_body)
    send_args = {
        'Source': FROM_MAIL,
        'Destinations': [recipent],
        'RawMessage': {'Data': msg.as_string()},
    }
    CONFIGURATION_SET = None
    if CONFIGURATION_SET:
        send_args['ConfigurationSetName'] = CONFIGURATION_SET
    response = ses.send_raw_email(**send_args)
    if response.get('MessageId',None):
        success = True
    return success