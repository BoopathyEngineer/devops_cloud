from typing import Dict, Optional
from helper import bytes_extract
from boto3.dynamodb.conditions import Key, Attr
from matching_api.service import weightage_calculate
from comparitive_analysis.constants import CATEGORIES
from comparitive_analysis.service import categories_removed
from amazonservice.gateway import *
from settings.configuration import *
import json
from decimal import Decimal
from amazonservice.dynamodb import get_item, put_item, delete_item, query_item, update_item
from settings.constants import APIGATEWAY, CONFIGTABLE, ENV, APITABLE, COGNITO, USERTABLE
from settings.env import get_env_vars
from interview_questions_api.constants import TYPES, LEVELS, COUNTS
from settings.aws_service import dynamodb
from datetime import datetime

from products.api_products import date_exceed_checking

"""
You can add any Validation for inside your api path

GET Info:-
2MB - resume
5MB - jd
"""


def db_result(email: str, api_name: str, credits: int, is_active: bool, request: int, status_code: int, message: str):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table= env_vars.get(APITABLE,'api-dev')
    user_table = env_vars.get(USERTABLE,'client-subscriptions-dev')
    if 'feature' in table:
        table = DEVAPI_TABLE
    if 'feature' in user_table:
        user_table = DEVCLIENT_TABLE
    if status_code == 200:
        credits=1
    user_key = {'email':email}

    api_credits = 0
    client_data = get_item(user_table,user_key)
    if client_data:
        if client_data.get('subscriptions'):
            subscriptions = client_data.get('subscriptions')
            if isinstance(subscriptions,list):
                for i in subscriptions:
                    if i.get('api_name') == api_name:
                        api_credits = i.get('access_count')   
    if status_code != 409:
        Item={
                'email': email,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                'api_name': api_name,
                'credits': credits,
                'is_active': is_active,
                'request': request,  
                'statuscode':  str(status_code),
                'message': message,
                'remaining_count':api_credits
            }
        put_item(table,Item)
        print("Error message updated in DB")

def api_name(path):
    after_slash = path.split("/")[-1]
    return after_slash


def converting_values(name, key):
    if name == "jd" and key == "file":
        return "Jd_file_size"
    if name == "resume" and key == "file":
        return "Resume_size"
    if name == "jd" and key == "min":
        return "Jd_minLength"
    if name == "jd" and key == "max":
        return "Jd_maxLength"
    return name





def retrive_values(path):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table = env_vars.get(CONFIGTABLE,'zitaconfig-dev')
    print("env_vars[CONFIGTABLE]",table,env_vars)
    if 'feature' in table:
        table = DEVCONFIG_TABLE
    pk = {"api_name": api_name(path)}
    data = get_item(table, pk)
    return data


def Subscription_validations(email, PATH, METHOD):
    from routes import AUTH_ROUTES

    path = api_name(PATH)
    success = False
    obj = {}
    statusCode = 500
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table = env_vars.get(USERTABLE,'client-subscriptions-dev')
    if 'feature' in table:
        table = DEVCLIENT_TABLE
    pk = {"email": email}
    data = get_item(table, pk)
    try:
        if AUTH_ROUTES[METHOD]:  # Check if method is valid
            VERIFY = AUTH_ROUTES[METHOD]
            if VERIFY.get(PATH):
                if data and isinstance(data, dict):
                    plan = data.get("subscriptions",[])
                    avail_api = [item.get('api_name','') for item in plan]
                    print("avail_api",avail_api)
                    if path not in avail_api:
                        statusCode = 409
                        raise Exception(INSUFFICIENT_CREDITS)
                    for i in plan:
                        if i.get("api_name") == path:
                            expiry_date = i.get("expired_at")
                            today_date =  datetime.now()
                            value = date_exceed_checking(expiry_date,today_date)
                            access_count = i.get("access_count")
                            
                            apiname = api_name(path)

                            if access_count == 0:
                                statusCode = 409
                                raise Exception(CREDITS_EXPIRED)
                            if access_count > 0 and value:
                                expiry_count = 0
                                db = update_access_count(email, apiname)
                                statusCode = 402
                                raise Exception(SUBSCRIPTION_EXPIRED)
                            if access_count > 0:
                                success = True
                                statusCode = 200
                    obj = data
                else:
                    statusCode = 409
                    raise Exception(INSUFFICIENT_CREDITS)
            else:
                statusCode = 404
                raise Exception(INVALID_PATH)
    except Exception as e:
        obj["error"] = str(e)
        obj["statusCode"] = statusCode
    return success, obj

#
def update_access_count(email, api_name):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table = env_vars.get(USERTABLE,'client-subscriptions-dev')
    if 'feature' in table:
        table = DEVCLIENT_TABLE
    pk = {"email": email}
    data = get_item(table, pk)
    subscription = data.get('subscriptions',[])
    for i in subscription:
        if i['api_name'] == api_name:
            i['access_count'] = 0
            i['feature_count'] = 0
    userkey = {'email':email}
    update_expression = 'SET #sub = :sub_val'
    attribute_names = {'#sub': 'subscriptions'}
    attribute_values = {':sub_val': subscription}
    ## CLIENT TABLE UPDATION 
    table_updation = update_item(table,userkey,update_expression,attribute_values,attribute_names)
    return True

def odd_or_even(number):
    if number % 2==0: ## Even
        return True
    else: ## Odd
        return True

def reduce_count(item, path):
    path = api_name(path)
    try:
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        usertable = env_vars.get(USERTABLE,'client-subscriptions-dev')
        if "feature" in usertable:
            usertable = DEVCLIENT_TABLE
        subscription = item.get('subscriptions',[])
        email = item.get('email','')
        apitable = env_vars.get(APITABLE,'api-feature-z277')
        if "feature" in apitable:
            apitable = DEVAPI_TABLE
        filterexpression = Attr('api_name').eq(path) & Attr('statuscode').eq("200")
        key = 'email'
        api_data = query_item(apitable,key,email,expression=filterexpression)
        for i in subscription:
            if i['api_name'] == path:
                addon_count = int(i['addon_count'])
                reduces = int(i['access_count'])
                feat_count = int(i['feature_count'])
                print("odd_or_even(len(api_data))!!!!!!!",odd_or_even(len(api_data)))
                if odd_or_even(len(api_data)):
                    reduces = int(i['access_count']) - 1
                    if feat_count == 0 and addon_count > 0:
                        addon_count = int(i['addon_count']) - 1
                    else:
                        feat_count = int(i['feature_count']) - 1
                i['access_count'] = reduces
                i['feature_count'] = feat_count
                i['addon_count'] = addon_count
        userkey = {'email':email}
        update_expression = 'SET #sub = :sub_val'
        attribute_names = {'#sub': 'subscriptions'}
        attribute_values = {':sub_val': subscription}
        ## CLIENT TABLE UPDATION 
        table_updation = update_item(usertable,userkey,update_expression,attribute_values,attribute_names) 
        return True
    except Exception as e:
        print("reduce_count Exception-->", e)
        return False


def API_validation(event, context, request, dataobj):
    from routes import AUTH_ROUTES

    success = False
    obj = {}
    statusCode = 400
    PATH = event['path']
    METHOD = event['httpMethod']
    try:
        if AUTH_ROUTES[METHOD]:  # Check if method is valid
            VERIFY = AUTH_ROUTES[METHOD]
            if VERIFY.get(PATH):  # Check if path is valid
                if isinstance(request, dict):
                    if REQUIRED.get(PATH):
                        a = REQUIRED[PATH]  # Required keys
                        b = request.keys()  # Parameters are passed keys
                        missing_elements = [
                            key_change(item) for item in a if item not in b
                        ]
                        if len(missing_elements) == 0:  # Missing Key Elements
                            for i, y in request.items():
                                isfile = y.get("isfile")
                                filesize = y.get("filesize")
                                filename = y.get("filename")
                                if isfile:
                                    if filename:
                                        if get_extension(filename) not in SUPPORTED_FORMAT:
                                            statusCode = 415
                                            raise Exception(UNSUPPORTED_FILE_FORMAT)
                                    if EXCEED_FILESIZE[PATH].get(i):
                                        EXCEED_FEAT_COUNT = dataobj.get(converting_values(i,'file'))
                                        if filesize > EXCEED_FEAT_COUNT and i in RESUMES_FILE:  # FILESIZE EXCEEDS 2MB 
                                            statusCode = 413
                                            raise Exception(RESUME_FILESIZE_EXCEED)
                                        if filesize > JD_EXCEED and i in JD_FILE:  # FILESIZE EXCEEDS 5MB
                                            statusCode = 413
                                            raise Exception(JD_FILESIZE_EXCEED)
                                elif isfile == False and i in ['jd']:
                                    content = y['content']
                                    jd_min = dataobj.get(converting_values(i,'min'))
                                    jd_max = dataobj.get(converting_values(i,'max'))
                                    #### JD Characters Exceed Here #####
                                    if len(content) < jd_min and i in JD_FILE:
                                        statusCode = 400
                                        raise Exception(INSUFFICIENT_CHARACTERS_JD) #INSUFFICIENT JD
                                    if len(content) > jd_max and i in JD_FILE:
                                        statusCode = 400
                                        raise Exception(EXCESSIVE_CHARACTERS_JD)  # EXCESSIVE JD
                                    #### Resume Characters Exceed Here #####
                                    if len(content) < MIN_LENGTH and i in RESUMES_FILE:
                                        statusCode = 400
                                        raise Exception(INSUFFICIENT_CHARACTERS_RESUME) #INSUFFICIENT RESUME
                                    if len(content) > MAX_LENGTH and i in RESUMES_FILE:
                                        statusCode = 400
                                        raise Exception(EXCESSIVE_CHARACTERS_RESUME) # EXCESSIVE RESUME
                                    
                            feat_valid,feat_obj = feature_validation(PATH,request)
                            if feat_valid:
                                ###### HERE VALIDATION HAS BEEN DONE ######
                                success = True
                            else:
                                if feat_obj.get("error"):
                                    feat_err = feat_obj["error"]
                                    raise Exception(feat_err)
                        else:  # Based on the missing key elements Working on the response
                            missing = ",".join(missing_elements)
                            # missing = {'missing_key':missing_elements}
                            statusCode = 400
                            raise Exception(key_missing(missing))
                    return success, obj
            else:
                statusCode = 404
                raise Exception(INVALID_PATH)
        else:
            statusCode = 404
            raise Exception(INVALID_METHOD)
    except Exception as e:
        obj["error"] = str(e)
        obj["statusCode"] = statusCode
    return success, obj


def key_missing(key):
    txt = key
    keys = "key"
    if "," in txt:
        keys = "keys"
    if key == "jd":
        txt = "Job description"
    if key == "resume":
        txt = "Resume"
    if key == "role":
        txt = "Interviewer role"
    if key == "job_title":
        txt = "Job Title"
    if key == "industry_type":
        txt = "Industry type"
    if key == "skills":
        txt = "Mandatory competencies"
    if key == "overview":
        txt = "Role overview"
    if key == "min_experience":
        txt = "Minimum experience"
    return f"{txt} {keys} is missing"


def key_change(key):
    txt = key
    if key == "jd":
        txt = "Job description"
    if key == "resume":
        txt = "Resume"
    if key == "role":
        txt = "Interviewer role"
    if key == "job_title":
        txt = "Job Title"
    if key == "industry_type":
        txt = "Industry type"
    if key == "skills":
        txt = "Mandatory competencies"
    if key == "overview":
        txt = "Role overview"
    if key == "min_experience":
        txt = "Minimum experience"
    return txt


def get_extension(file_name):
    import os

    file_extension = os.path.splitext(file_name)[1]
    return file_extension


def Subscription_validation(event, context, request):
    return True


def feature_validation(path, request):
    success = False
    statusCode = 400
    feat = {}
    try:

        if path == "/matching":
            for i, y in request.items():
                if i not in ["jd", "resume"]:
                    if request.get(i):
                        if request[i].get("content"):
                            if request[i]["isfile"] == False:
                                weightage =  bytes_extract(request[i]['content'])
                                if not isinstance(weightage,list):
                                    valid_format = "give me a valid format"
                                    statusCode = 403
                                    raise Exception(valid_format)
                                if len(weightage) == 0:
                                    statusCode = 400
                                    raise Exception(NO_CRITEIRA)
                                if isinstance(weightage, list):
                                    for x in weightage:
                                        digit_check = list(x.values())[0]
                                        if isinstance(digit_check, int):
                                            digit_check = str(digit_check)
                                        if digit_check.isdigit() == False:
                                            statusCode = 403
                                            raise Exception(INVALID_WEIGHTAGE_INPUT)
                                    sum = weightage_calculate(weightage)
                                    if sum == False:             
                                        if i == 'profile_matching':
                                            statusCode = 400
                                            raise Exception(MISMATCH_PROFILE_COMPATIBILITY)
                                        elif i == 'enhanced_matching':
                                            statusCode = 400
                                            raise Exception(MISMATCH_ENHANCED_COMPATIBILITY)
                elif i in ['resume']:
                    if request[i].get('content'):
                        if request[i]["isfile"] == False:
                            statusCode = 403
                            raise Exception(RESUME_FORMAT)

            ######## MATCHING VALIDATION DONE #######
            success = True

        if path == "/interview_questions":
            for i, y in request.items():
                if i not in ["jd", "resume"]:
                    if request[i].get("content"):
                        if request[i]["isfile"] == False:
                            content = bytes_extract(request[i]["content"])
                            if i == "criteria":
                                if not isinstance(content, list):
                                    if len(content) == 0:
                                        raise Exception(EMPTY_FIELD)
                                    raise Exception(LIST_FORMAT)
                                if isinstance(content, list):
                                    final_questions = 0
                                    if len(content) == 0:
                                        statusCode = 400
                                        raise Exception(LEAST_LEVEL) 
                                    for o in content:
                                        counts = o.get("count")
                                        levels = o.get("level")
                                        types = o.get("type")

                                        if (
                                            types not in TYPES
                                            and levels not in LEVELS
                                            and counts not in COUNTS
                                        ):
                                            raise Exception(INVALID_TYPE_LEVEL_COUNT)
                                        elif (
                                            types not in TYPES and levels not in LEVELS
                                        ):
                                            raise Exception(INVALID_TYPE_LEVEL)
                                        elif (
                                            types not in TYPES and counts not in COUNTS
                                        ):
                                            raise Exception(INVALID_TYPE_COUNT)
                                        elif (
                                            counts not in COUNTS
                                            and levels not in LEVELS
                                        ):
                                            raise Exception(INVALID_LEVEL_COUNT)
                                        elif types not in TYPES:
                                            raise Exception(INVALID_TYPE)
                                        elif levels not in LEVELS:
                                            raise Exception(INVALID_LEVEL)
                                        elif counts not in COUNTS:
                                            if len(counts) == 0:
                                                raise Exception(INVALID_COUNT)

                                        if counts == None and levels == None:
                                            statusCode = 400
                                            raise Exception(LEVEL_COUNT_MISSING)
                                        elif counts == None:
                                            statusCode = 400
                                            raise Exception(COUNTS_MISSING)
                                        elif levels == None:
                                            statusCode = 400
                                            raise Exception(TYPE_MISSING)
                                        elif o.get("count"):
                                            count = o.get("count")
                                            if count.isdigit() == False:
                                                statusCode = 403
                                                raise Exception(INVALID_COUNT_INPUT)
                                            else:
                                                final_questions += int(count)
                                    if final_questions > 15 or final_questions < 1:
                                        raise Exception(QUESTION_LIMIT_FORMAT)
                                if len(content) == 0:
                                    statusCode = 400
                                    raise Exception(LEAST_LEVEL) 

                            if i == "summary":
                                if len(content) == 0:
                                    statusCode = 403
                                    raise Exception(VALID_INFO)
                                elif len(content) > 150:
                                    statusCode = 400
                                    raise Exception(SUMMARY_CHARACTERS)

                            if i == "role":
                                if len(content) == 0:
                                    statusCode = 403
                                    raise Exception(VALID_INFO)
                        else:
                            if i == 'summary':
                                statusCode = 403
                                raise Exception(VALID_INFO)
                                
                            if i == 'role':
                                statusCode = 403
                                raise Exception(VALID_INFO)
                    else:
                        content = bytes_extract(request[i]["content"])
                        if i == "criteria":
                            if not isinstance(content, list):
                                if len(content) == 0:
                                    raise Exception(EMPTY_FIELD)
                                raise Exception(CRITERIA_FORMAT)
                        if i == "summary":
                            if len(content) == 0:
                                raise Exception(EMPTY_FIELD)
                        if i == "role":
                            if len(content) == 0:
                                raise Exception(EMPTY_FIELD)
                elif i in ["resume"]:
                    if request[i].get("content"):
                        if request[i]["isfile"] == False:
                            statusCode = 403
                            raise Exception(RESUME_FORMAT)
            ######## INTERVIEW QUESTIONS VALIDATION DONE #######
            success = True
        
        if path == '/comparitive_analysis':
            for i,y in request.items():
                if request.get('resume2') == None:
                    statusCode = 400
                    raise Exception(COMPARATIVE_MIN_INSUFFICIENT)
                if i not in [
                    "jd",
                    "resume1",
                    "resume2",
                    "resume3",
                    "resume4",
                    "resume5",
                ]:
                    if request[i].get("content"):
                        if request[i]["isfile"] == False:
                            content = bytes_extract(request[i]["content"])
                            if len(content) == 0:
                                statusCode = 400
                                raise Exception(COMPARATIVE_CRITERIA)
                            if len(content) < 0:
                                new_content = categories_removed(content, CATEGORIES)
                                request["categories"]["content"] = new_content
                elif i in ["resume1", "resume2", "resume3", "resume4", "resume5"]:
                    if request[i].get("content"):
                        if request[i]["isfile"] == False:
                            statusCode = 403
                            raise Exception(RESUME_FORMAT)
            # request['criteria']['content'] = arr
            ######## COMPARATIVE ANALYSIS VALIDATION DONE #######
            success = True

        if path == "/profile_summary":
            ######## PROFILE SUMMARY VALIDATION DONE ########
            for i, y in request.items():
                if i in ["resume"]:
                    if request[i].get("content"):
                        if request[i]["isfile"] == False:
                            raise Exception(RESUME_FORMAT)
            success = True

        if path == "/jd_parser":
            ######## JD PARSER VALIDATION DONE #######
            success = True

        if path == "/resume_parser":
            ######## RESUME PARSER VALIDATION DONE #######
            for i, y in request.items():
                if i in ["resume"]:
                    if request[i].get("content"):
                        if request[i]["isfile"] == False:
                            statusCode = 403
                            raise Exception(RESUME_FORMAT)
                    else:
                        if request[i]["isfile"] == False:
                            statusCode = 403
                            raise Exception(RESUME_FORMAT)
                        content = bytes_extract(request[i]["content"])
                        if len(content) == 0:
                            statusCode = 400
                            raise Exception(RESUME_PARSER_ERROR)

            success = True
        
        if path == '/jd_generation':
            for i,y in request.items():
                if i == 'job_title' and len(y["content"]) == 0:
                    statusCode = 403
                    raise Exception(VALID_JOB_TITLE)
                elif i == 'industry_type' and len(y["content"]) == 0:
                    statusCode = 403
                    raise Exception(VALID_INDUSTRY_TYPE)
                elif i in ["min_experience", "max_experience"]:
                    if y["content"].isdigit() == False:
                        content = bytes_extract(y["content"])
                        if isinstance(content, int):
                            if int(content) < 0:
                                statusCode = 400
                                raise Exception(NEGATIVE_NUM_FORMAT)
                        else:
                            statusCode = 403
                            raise Exception(VALID_NUM_FORMAT)
                    if int(y["content"]) < 0:
                        statusCode = 400
                        raise Exception(NEGATIVE_NUM_FORMAT)
                    if int(y["content"]) > EXCEED_MAX_EXP_VALUE:
                        statusCode = 400
                        raise Exception(EXCEED_EXP_VALUE)
                elif i == "skills":
                    content = bytes_extract(y["content"])
                    if isinstance(content, list):
                        if len(content) == 0:
                            statusCode = 400
                            raise Exception(COMPENTENCIES_MISSING)
                    if len(content) == 0:
                        statusCode = 400
                        raise Exception(COMPENTENCIES_MISSING)
                elif i == "overview":
                    content = bytes_extract(y["content"])
                    if len(content) == 0:
                        statusCode = 400
                        raise Exception(OVERVIEW_MISSING)
                elif i == "nice_to_have":
                    content = bytes_extract(y["content"])
                    if isinstance(content, list):
                        if len(content) == 0:
                            statusCode = 400
                            raise Exception(NICETOHAVE_MISSING)
                    if len(content) == 0:
                            statusCode = 400
                            raise Exception(NICETOHAVE_MISSING)

            if request.get("min_experience") and request.get("max_experience"):
                min_expp = request["min_experience"]["content"]
                max_expp = request["max_experience"]["content"]
                if int(min_expp) > int(max_expp):
                    statusCode = 400
                    raise Exception(MAX_MIN_EXP)
            ######## JD GENERATION VALIDATION DONE #######
            success = True

    except Exception as e:
        feat["error"] = str(e) 
        feat["statusCode"] = statusCode
    return success,feat


def apikey_function(event: Dict, user: str, email: str, username: str) -> Dict:
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    environment = env_vars.get(ENV,'feature')
    gateway_id = env_vars.get(APIGATEWAY,None)
    if "dev" in environment:
        environment = "feature"
    access = usage_identify(environment)
    obj = {}
    statusCode = 400
    success = False

    try:
        apikeys = get_allapi_keys()
        matched, alllist = get_userkey(apikeys, user)
        # matched = next((api_key for api_key in apikeys if api_key['name'] == user), None)
        access_url = get_api_base_url(gateway_id)
        if matched and isinstance(matched, dict) and access:
            response, user_id = get_apikey(matched["id"])
            queryparams = None
            if event.get("queryparams"):
                queryparams = event.get("queryparams")
            if queryparams == None and event.get("body"):
                queryparams = event.get("body")
            if queryparams:
                generation = queryparams.get("generate")
                deletion = queryparams.get("delete")
                if generation == "True" and deletion == None:
                    api_id, response = create_apikey(user, email)
                    usageplan = apikey_to_usageplan(api_id, access)
                    disable_key = disable_api_key(matched["id"], alllist)
                    delete_id = delete_apikey(matched["id"], alllist)
                    obj["message"] = "New Api-key has been created"
                    obj["org_id"] = user_id
                    obj["response"] = response
                    obj["access_url"] = access_url
                    obj["statusCode"] = 200
                    obj["success"] = True

                elif deletion == "True" and generation == None:
                    response = delete_apikey(matched["id"], alllist)
                    obj["org_id"] = user_id
                    obj["message"] = "Api-key has been deleted"
                    obj["access_url"] = access_url
                    obj["statusCode"] = 200
                    obj["success"] = True

                else:
                    obj["org_id"] = user_id
                    obj["apikey"] = response
                    obj["access_url"] = access_url
                    obj["statusCode"] = 200
                    obj["success"] = True

            else:
                # obj['access_token_url'] = access_token_url
                obj["response"] = response
                obj["org_id"] = user_id
                obj["access_url"] = access_url
                obj["statusCode"] = 200
                obj["success"] = True

        else:
            queryparams = None
            if event.get("queryparams"):
                queryparams = event.get("queryparams")
            if queryparams == None and event.get("body"):
                queryparams = event.get("body")
            if queryparams:
                generation = queryparams.get("generate")
                if generation == "True":
                    api_id, response = create_apikey(user, email)
                    usageplan = apikey_to_usageplan(api_id, access)
                    obj["message"] = "New Api-key has been created"
                    obj["statusCode"] = 200
                    obj["user_id"] = user
                    obj["response"] = response
                    obj["access_url"] = access_url
                    obj["success"] = True
                else:
                    obj["response"] = "API key is Not created"
                    obj["statusCode"] = 400
            else:
                obj["response"] = "API key is Not created"
                obj["statusCode"] = 400
    except Exception as e:
        obj["error"] = str(e)
        obj["statusCode"] = 400
    return obj

def usage_identify(usage):
    datalist = get_all_usage_plans()
    for x in datalist:
        if x["name"] == usage:
            return x["id"]
    return None

def get_userkey(api_keys,user):
    name_to_last_id = {}
    matched_entries = []
    for api_key in api_keys:
        if api_key["name"] == user:
            matched_entries.append(api_key["id"])
            name_to_last_id[user] = api_key
    last_id = name_to_last_id.get(user)
    return last_id, matched_entries
