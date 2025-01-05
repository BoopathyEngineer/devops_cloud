# import requests
from typing import Any, Dict
from venv import logger
from routes import AUTH_ROUTES, APP_ROUTES, SIGNIN_ROUTES
from requests_toolbelt.multipart import decoder
import base64
from rough import *
import json
from datetime import datetime
from extracter import event_extracter, get_authorizer, get_key
from settings.validation import API_validation, Subscription_validations, key_missing, reduce_count, retrive_values, usage_identify
from settings.configuration import COMPARATIVE_COUNT, COMPARATIVE_DUPLICATE, COMPARATIVE_MAX_EXCEED, COMPARATIVE_MIN_INSUFFICIENT, FILE_COUNT_EXCEED, HEADERS, INVALID_PATH, REQUIRED, SUBSCRIPTION_PATH
from amazonservice.cognito import subuser_details

def auth_handler(event: Dict[str, Any], context: Dict[str, Any]):
    print("event",event)
    dictobj = event_extracter(event)
    statusCode = 400
    success = False
    obj = {}
    PATH = event.get('path')
    METHOD = event.get('httpMethod')
    if SIGNIN_ROUTES.get(METHOD):
        VERIFY = SIGNIN_ROUTES[METHOD]
        if VERIFY.get(PATH):
            lambda_function = SIGNIN_ROUTES[METHOD][PATH]  
            response = lambda_function(dictobj)
            if isinstance(response,dict):
                if response.get('success'):
                    success = response.get('success')
                    del response['success']
                obj = response
                if response.get('statusCode'):
                    statusCode = obj['statusCode']  
                    del response['statusCode']
    
    else:
        obj['error'] = INVALID_PATH
    context = {
        "success": success,
        "data": obj
    }
    return {
        'headers':HEADERS,
        'statusCode': statusCode,
        'body': json.dumps(context)
        }

# content = None
# deta = auth_handler(signup,content)
# print(deta)