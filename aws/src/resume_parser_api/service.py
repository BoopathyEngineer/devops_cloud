from helper import FineTuningModal
from s3_bucket import s3_Storage
from resume_parser_api.constants import *
import json
from settings.configuration import RESUME_PARSER_ERROR, MIN_LENGTH, MAX_LENGTH, INSUFFICIENT_CHARACTERS_RESUME, EXCESSIVE_CHARACTERS_RESUME, UNSUPPORTED_TEXT_FORMAT


def Lambda_resume_parser(resume):
    if resume:
        system = SYSTEM
        result=FineTuningModal(system,resume,RESUME_PARSER)
    else:
        result = "Resume required to proceed further."
    return result

def Lambda_Resume_Parser_API(event,obj):
    if event.get('resume'):
        new_obj = {}
        resume_file = f'{event["resume"]["filename"]}'
        resume = s3_Storage(event['resume'],resume_file,folder='Resume/')
        data,token = Lambda_resume_parser(resume)
        dele = {}
        if isinstance(data,str):
            try:
                new_obj['response'] = json.loads(data)
                dele = new_obj['response']

                def recurse(dele):
                    try:
                        for i in dele:
                            if dele[i]=="None" or dele[i] == ["None"] or dele[i] == ["null"] or dele[i] == "null" or dele[i] == None:
                                dele.pop(i)
                            elif i == "Projects":
                                for j in dele.get(i,[]):
                                    if isinstance(j,dict):
                                        keys_to_delete = [key for key, value in j.items() if value in ["None", None]]
                                        for key in keys_to_delete:
                                            del j[key]
                    except:
                        recurse(dele)
                    return dele
                
                val = recurse(dele)
                new_obj['response'] = val
                new_obj['success'] = True
                new_obj['statusCode'] = 200
            except:
                new_obj['error'] = UNSUPPORTED_TEXT_FORMAT
                new_obj['statusCode'] = 400
            new_obj['token'] = token
    return new_obj