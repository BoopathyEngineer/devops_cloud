from helper import FineTuningModal
from s3_bucket import s3_Storage, s3_file_download
from jd_parser_api.constants import *
import json
from settings.configuration import JD_PARSER_ERROR, EXCESSIVE_CHARACTERS_JD, INSUFFICIENT_CHARACTERS_JD, UNSUPPORTED_TEXT_FORMAT, MIN_LENGTH, MAX_LENGTH



def Lambda_jd_parser(jd):
    if jd:
        system = SYSTEM
        result=FineTuningModal(system,jd,JD_PARSER)
    else:
        result = "Job Description required to proceed further."
    return result

def Lambda_Jd_Parser_API(event,obj):
    if event.get('jd'):
        new_obj = {}
        jd_file = f'jd_{event["jd"]["filename"]}'
        jd = s3_Storage(event['jd'],jd_file,folder='Jd/')
        if len(jd) == 0:
            new_obj['error'] = JD_PARSER_ERROR
            new_obj['statusCode'] = 400
        elif len(jd) < MIN_LENGTH:
            new_obj['error'] = INSUFFICIENT_CHARACTERS_JD
            new_obj['statusCode'] = 400
        elif len(jd) > MAX_LENGTH:
            new_obj['error'] = EXCESSIVE_CHARACTERS_JD
            new_obj['statusCode'] = 400
        else:
            data,token = Lambda_jd_parser(jd)
            dele = {}
            if isinstance(data,str):
                try:
                    dele = json.loads(data)
                    if dele.get("Is_JD"):
                        def recurse(dele):
                            if dele:
                                try:
                                    for i in dele:
                                        if dele[i]=="None" or dele[i] == ["None"] or dele[i] == "null" or dele[i] == ["null"] or dele[i] == None:
                                            dele.pop(i)
                                        elif len(dele[i]) == 0:
                                            dele.pop(i)
                                except:
                                    recurse(dele)
                            return dele
                        del dele["Is_JD"]
                        val = recurse(dele)
                        new_obj['response'] = val
                        new_obj['statusCode'] = 200
                        new_obj['success'] = True
                    else:
                        new_obj['error'] = "Please upload a relevant JD document."
                        new_obj['statusCode'] = 400
                except:
                    new_obj['error'] = UNSUPPORTED_TEXT_FORMAT
                    new_obj['statusCode'] = 400
            new_obj['token'] = token
    return new_obj
