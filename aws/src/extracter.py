from urllib.parse import parse_qs
from requests_toolbelt.multipart import decoder
from typing import Any, Dict, List, Optional
from amazonservice.cognito import subuser_details
from amazonservice.gateway import get_apikey
from settings.constants import COGNITO
from settings.env import get_env_vars
import re
import base64
import json
from helper import bytes_extract


def is_file_format(form_data):
    if 'filename="' in form_data:
        return True
    else:
        return False
    
def get_filename_value(form_data):
    filename_value = None
    parts = form_data.split(";")
    for part in parts:
        if part.strip().startswith('filename='):
            filename_value = part.split("=")[1].replace('"', '').strip()
            break  
    return filename_value

def get_key(form_data):
    # 'form-data; name="birth_date"', 'content': b'2012-123'
    key = form_data.split(";")[1].split("=")[1].replace('"', '')
    isfile = is_file_format(form_data)
    filename_obj = get_filename_value(form_data)
    if filename_obj  == '':
        isfile = False
    return key,isfile,filename_obj


def get_authorizer(event:Dict[str, Any]):
    user_id = None
    user_email = None
    username = None
    is_error = False
    if 'requestContext' in event and 'authorizer' in event['requestContext']:
        user = event['requestContext']['authorizer']['claims']
        user_id = user.get('sub')  # User ID from Cognito
        user_email = user.get('email')  # Email from Cognito
        username = user.get('cognito:username')
        if user_email == None:
            user_email = user.get('cognito:username')
    elif 'requestContext' in event and 'identity' in event['requestContext']:
        api_key = event['requestContext']['identity']['apiKeyId']
        resp,user_id = get_apikey(api_key)
        if resp == None and user_id == None:
            is_error = True
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        userpool = env_vars.get(COGNITO,'us-east-1_546RUb4gO') 
        resp = subuser_details(userpool,user_id)
        if resp:
            username = resp.get('Username')
        user_email = None
        if isinstance(resp,dict):
            user_email = next(item['Value'] for item in resp['Attributes'] if item['Name'] == 'email') 
        if user_email == None:
            user_email = user_id
    return user_id,user_email,username,is_error


def extract_key_values(data: str) -> Dict[str, List[str]]:
    # Define a regular expression pattern to match keys and values
    pattern = r'Content-Disposition: form-data; name="([^"]+)"\r\n\r\n(\[.*?\])'
    result = None
    # Find all matches using the pattern
    if data:
        matches = re.findall(pattern, data, re.DOTALL)
        # Convert matches into a dictionary
        result = {}
        for key, value in matches:
            # Strip leading/trailing whitespace and remove surrounding quotes
            value = value.strip('[]').replace('"', '').split(',')
            result[key] = value
    return result




def event_extracter(event):
    dictobj = {}
    try:
        dictobj['requestContext'] = event.get("requestContext")
        dictobj['queryparams'] = event.get("queryStringParameters")
        headers = event.get('headers')
        if headers:
            if headers.get('content-type'):
                content_type = headers.get('content-type')
            if headers.get('Content-Type'):
                content_type = headers.get('Content-Type')
        if event["isBase64Encoded"]:
            postdata = base64.b64decode(event['body'])
            request = {} # Save request here
            for part in decoder.MultipartDecoder(postdata, content_type).parts:
                decoded_header = part.headers[b'Content-Disposition'].decode('utf-8')
                key,isfile,filename = get_key(decoded_header)
                file_size_bytes = len(part.content)  # Calculate file size in bytes
                file_size_mb = file_size_bytes / (1024 * 1024)  # Convert file size to megabytes
                if isfile:
                    request[key] = {"content":part.content,"isfile":isfile,"filename":filename,"filesize": file_size_mb}
                else:
                    request[key] = bytes_extract(part.content)
            dictobj['body'] = request
        elif event["isBase64Encoded"] == False:
            body = event.get('body')
            if isinstance(body,str):
                try:
                    body = json.loads(body)
                    # if isinstance(body,dict):
                    #     for key in body:
                    #         if isinstance(body[key],str):
                    #             body[key] = json.loads(body[key])
                except Exception as e:
                    parsed_body = parse_qs(body)
                    body = {key: value[0] if len(value) == 1 else value for key, value in parsed_body.items()}

            dictobj['body'] = body
    except Exception as e:
        print("event extracter exceptions",e)
    return dictobj

