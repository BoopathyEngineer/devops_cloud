import os
from s3_bucket import s3_Storage
from helper import FineTuningModal
from profile_summary_api.constants import SYSTEM,PROFILE_SUMMARY
from settings.configuration import RESUME_PARSER_ERROR
import json


def Lambda_Profile_Summary(resume):
    if resume:
        system= SYSTEM
        user_message={"resume": resume}
        result= FineTuningModal(system,str(user_message),PROFILE_SUMMARY)
    else:
        result = "Resume are required to proceed further."
    return result

def Lambda_Profile_Summary_API(event,obj):
    obj2 = {}
    if event.get('resume'):
        new_obj = {}
        resume_file = f'{event["resume"]["filename"]}'
        resume = s3_Storage(event['resume'],resume_file,folder='Resume/')
        if len(resume) == 0:
            new_obj['error'] = RESUME_PARSER_ERROR
            new_obj['statusCode'] = 400
        if new_obj.get('error') == None:
            data,token =Lambda_Profile_Summary(resume)
            if isinstance(data,str):
                data = json.loads(data)
            new_obj["response"] = data
            new_obj["statusCode"] = 200
            new_obj["success"] = True
            new_obj["token"] = token
        return new_obj 
    else:
        obj2['error'] = "Key has been Missing"
        obj2['statusCode'] = 400
        return obj2
   