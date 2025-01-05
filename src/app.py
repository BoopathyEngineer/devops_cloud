from typing import Any, Dict, Optional
from venv import logger
from routes import AUTH_ROUTES, APP_ROUTES
from requests_toolbelt.multipart import decoder
import base64
from rough import *
import json
from datetime import datetime
from extracter import event_extracter, get_authorizer,get_key,extract_key_values
from settings.validation import API_validation, Subscription_validations, api_name, db_result, key_missing, reduce_count, retrive_values, usage_identify
from settings.configuration import COMPARATIVE_COUNT, COMPARATIVE_DUPLICATE, COMPARATIVE_MAX_EXCEED, COMPARATIVE_MIN_INSUFFICIENT, DEVCLIENT_TABLE, FILE_COUNT_EXCEED, HEADERS, INVALID_PATH, REQUIRED, SUBSCRIPTION_PATH
from notification.signal import credit_usage
from Login.Signup import Free_promo_code, Get_confirm_user_signup
from subscriptions.stripe_service import Find_Url






def lambda_handler(event:Dict[str, Any], context: Dict[str, Any]):
    start_time = datetime.now()
    print("event---->",event,"\ncontext---->",context)


    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    user_id,user_email,userobj,err_obj = get_authorizer(event)
    if err_obj == True:
        response = 'Invalid API-Key'
        context = {"success": False,"data": response}
        return {'headers':HEADERS,'statusCode': 401,'body': json.dumps(context)}

    obj = {}
    headers = event['headers']
    ## decode the multipart/form-data request
    success = False
    statusCode = 400
    response = "Something went wrong!"
    resumes=[]
    lambda_event = event_extracter(event)
    if lambda_event:
        request = {} # Save request here
        duplicate_file = []
        file_count = []
        if event.get('isBase64Encoded'):
            postdata = base64.b64decode(event['body'])
            content_type = None
            if headers.get('content-type'):
                content_type = headers.get('content-type')
            if headers.get('Content-Type'):
                content_type = headers.get('Content-Type')
            if content_type:
                try:
                    for part in decoder.MultipartDecoder(postdata, content_type).parts:
                        decoded_header = part.headers[b'Content-Disposition'].decode('utf-8')
                        key,isfile,filename = get_key(decoded_header)
                        file_size_bytes = len(part.content)  # Calculate file size in bytes
                        file_size_mb = file_size_bytes / (1024 * 1024)  # Convert file size to megabytes
                        request[key] = {"content":part.content,"isfile":isfile,"filename":filename,"filesize": file_size_mb}
                        file_count.append(key)
                        if key!="jd" and key!="categories":
                            if filename in duplicate_file and filename:
                                response = {"error": COMPARATIVE_DUPLICATE}
                            else:
                                if request[key].get('isfile'):
                                    if filename:
                                        duplicate_file.append(filename)
                                if key in ["resume1","resume2","resume3","resume4","resume5"]:
                                    resumes.append({"content":part.content,"isfile":isfile,"filename":filename,"filesize": file_size_mb})
                except Exception as e:
                    print("postdata",postdata,"Exceptions",str(e))
                    response = "No Input Data Found"
                    incorrect_path = api_name(event['path'])
                    db_result(user_email,incorrect_path,0,True,1,statusCode,json.dumps(response)) 
                    context = {"success": success,"data": response}   
                    return {'headers':HEADERS,'statusCode': statusCode,'body': json.dumps(context)}  
        else:
            body = lambda_event['body']
            if isinstance(body,dict):
                for key,value in body.items():
                    request[key] =  {"content":value,"isfile":False,"filename":None,"filesize": 0}
        PATH = event['path']
        METHOD = event['httpMethod']
        if PATH in SUBSCRIPTION_PATH:
            if AUTH_ROUTES[METHOD]:
                VERIFY = AUTH_ROUTES[METHOD]
                if VERIFY.get(PATH):
                    lambda_function = AUTH_ROUTES[METHOD][PATH]
                    response = lambda_function(user_email) 
                    if response.get('error') == None:
                        success = True
                    if isinstance(response,dict):
                        if response.get('success'):
                            success = response.get('success')
                            del response['success']
                        obj = response
                        if response.get('statusCode'):
                            statusCode = obj['statusCode']  
                            del response['statusCode']

        else:
            try:
                subscription,datalist = Subscription_validations(user_email,PATH,METHOD)
                if subscription:
                    dataobj = retrive_values(PATH)
                    valid,reason = API_validation(event,context,request,dataobj)
                    # Trigger Lambda`s function based on the PATH and METHOD
                    if valid:
                        if AUTH_ROUTES[METHOD]:
                            VERIFY = AUTH_ROUTES[METHOD]
                            if VERIFY.get(PATH):
                                lambda_function = AUTH_ROUTES[METHOD][PATH]
                                ## if same key has two more files
                                duplicates = [name for name in set(file_count) if file_count.count(name) > 1]
                                if len(duplicates) > 0:
                                    response = {"error": FILE_COUNT_EXCEED}

                                if PATH =='/comparitive_analysis':
                                    comparative_max_count = dataobj.get('max_resume')
                                    comparative_min_count = dataobj.get('min_resume')
                                    if len(resumes) <= comparative_max_count:
                                        response = lambda_function(request,obj,resumes)
                                        if isinstance(response,dict):
                                            if response.get('token'):
                                                del response['token']
                                            if response.get("error") == None:
                                                db_response = reduce_count(datalist,PATH)
                                                credit_usage(user_email)
                                    elif len(resumes) == comparative_min_count:
                                        response = {"error": COMPARATIVE_MIN_INSUFFICIENT}
                                        db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
                                    else:
                                        response = {"error": COMPARATIVE_MAX_EXCEED}
                                        db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
                                else:
                                    duplicates = [name for name in set(file_count) if file_count.count(name) > 1]
                                    if len(duplicates) == 0:
                                        response = lambda_function(request,obj)
                                        if response.get('token'):
                                            del response['token']
                                        if isinstance(response,dict):
                                            if response.get("error") == None:
                                                db_response = reduce_count(datalist,PATH)
                                                credit_usage(user_email)
                                    else:
                                        response = {"error": FILE_COUNT_EXCEED}
                                        db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
                                if isinstance(response,dict):
                                    if response.get('success'):
                                        success = response.get('success')
                                        del response['success']
                                    obj = response
                                    if response.get('statusCode'):
                                        statusCode = obj['statusCode']  
                                        del response['statusCode']
                                db_result(user_email,api_name(PATH),0,True,1,statusCode,"   ")
                    else:
                        if reason.get("error"):
                            statusCode = reason["statusCode"]
                            response = {"error": reason["error"]}
                            db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
                else:
                    if datalist.get("error"):
                        statusCode = datalist["statusCode"]
                        response = {"error": datalist["error"]}
                        db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
            except Exception as e:
                print("Exception-->",e)
                db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
       
            
    elif event["isBase64Encoded"] == False and event["body"] == None:
        PATH = event['path']
        METHOD = event['httpMethod']
        if PATH in SUBSCRIPTION_PATH:
            if AUTH_ROUTES[METHOD]:
                VERIFY = AUTH_ROUTES[METHOD]
                if VERIFY.get(PATH):
                    lambda_function = AUTH_ROUTES[METHOD][PATH]
                    response = lambda_function(user_email)
                    if isinstance(response,dict):
                        if response.get('success'):
                            success = response.get('success')
                            del response['success']
                        obj = response
                        if response.get('statusCode'):
                            statusCode = obj['statusCode']  
                            del response['statusCode']
                    if response.get('error') == None:
                        success = True
        elif PATH not in SUBSCRIPTION_PATH:
            if REQUIRED.get(PATH):
                a = REQUIRED[PATH]  # Required keys
                # b = request.keys()  # Parameters are passed keys
                # missing_elements = [key_change(item) for item in a if item not in b]
                if len(a) != 0:   # Missing Key Elements
                                                 # Based on the missing key elements Working on the response
                    missing = ','.join(a)
                    response = key_missing(missing)
                    db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
            else:
                response = INVALID_PATH
                db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
        else:
            response = "No Input Data Found"
            db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
    else:
        PATH = event['path']
        METHOD = event['httpMethod']
        response = "Content-Type not found"
        PATH = event['path']
        db_result(user_email,api_name(PATH),0,True,1,statusCode,json.dumps(response))
    end_time = datetime.now()
    
    final_time = end_time - start_time
    print("Final Time Difference03",final_time)
    context = {
        "success": success,
        "data": response
    }
    
    return {
        'headers':HEADERS,
        'statusCode': statusCode,
        'body': json.dumps(context)
        }



def auth_handler(event: Dict[str, Any], context: Dict[str, Any]):
    dictobj = event_extracter(event)
    user_id,user_email,username,err_obj = get_authorizer(event)
    statusCode = 400
    success = False
    obj = {}
    
    PATH = event.get('path')
    METHOD = event.get('httpMethod')
    if APP_ROUTES[METHOD]:
        VERIFY = APP_ROUTES[METHOD]
        if VERIFY.get(PATH):
            lambda_function = APP_ROUTES[METHOD][PATH]  
            response = lambda_function(dictobj,user_id,user_email,username)
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




content = None
deta = auth_handler(file,content)
# print(deta)

# content = None
# deta = lambda_handler(file,content)
# print(deta)


