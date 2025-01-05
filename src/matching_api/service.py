from matching_api.constants import MATCHING, PROFILE_COMPATIBILITY,SYSTEM,ENHANCED_COMPATIBILITY,CERITERIA
from helper import FineTuningModal,bytes_extract
from s3_bucket import s3_Storage
import json
from settings.configuration import JD_PARSER_ERROR, RESUME_PARSER_ERROR


def Lambda_Matching(jd,resume):
    if jd and resume:
        system= SYSTEM
        criteria = ','.join(CERITERIA)
        user_message={"jd": jd,"resume": resume,"criteria": criteria}
        result=FineTuningModal(system,str(user_message),MATCHING)
    else:
        result = "Both JD and Resume are required to proceed further."
    return result


def Lambda_Matching_API(event,obj):
    if event.get('jd') and event.get('resume') and event.get('profile_matching'):
        new_obj = {}
        jd_file = f'{event["jd"]["filename"]}.pdf'
        resume_file = f'{event["resume"]["filename"]}'
        jd = s3_Storage(event['jd'],jd_file,folder='Jd/')
        if len(jd) == 0:
            new_obj['error'] = JD_PARSER_ERROR
            new_obj['statusCode'] = 400
        resume = s3_Storage(event['resume'],resume_file,folder='Resume/')
        if len(resume) == 0:
            new_obj['error'] = RESUME_PARSER_ERROR
            new_obj['statusCode'] = 400
        profile_match = bytes_extract(event['profile_matching']['content'])
        enhanced_match = None
        if event.get('enhanced_matching'):
            enhanced_match = bytes_extract(event['enhanced_matching']['content'])
        data = new_obj
        if weightage_calculate(profile_match) and new_obj.get('error') == None:
            data,token = Lambda_Matching(jd,resume)
            profile_matching,profile_score = weightage_provider(data,profile_match,PROFILE_COMPATIBILITY)
            if enhanced_match:
                enhanced_matching,enhanced_score = weightage_provider(data,enhanced_match,ENHANCED_COMPATIBILITY)
                new_obj["enhanced_compatibility"] = enhanced_matching
                new_obj["enhanced_match_score"] = enhanced_score
            new_obj["profile_compatibility"] = profile_matching 
            new_obj["profile_match_score"] = profile_score
            new_obj["success"] = True
            new_obj["statusCode"] = 200
            new_obj["token"] = token
            data = new_obj
        return data
    

def weightage_provider(response,weightage,lst):
    total_score = 0
    if weightage_calculate(weightage):
        if isinstance(response,str):
            response = json.loads(response)
        if isinstance(response,dict):
            arr = response['response'] 
            arr = criteria_removed(arr,weightage)
            if len(arr) > 0 and len(weightage) > 0:
                for ids,i in enumerate(arr):
                    if i['title'] in lst:
                        for item in weightage:
                            if item.get(i['title']):
                                score = int(item.get(i['title']))
                                final_score = int(i['percentage']) / 100 * score
                                i['percentage'] = final_score
                                total_score += final_score
            return arr,total_score
    else:
        return "Overall Weightage is more than 100"
        
    

def weightage_calculate(lst):
    succes = False
    total_score = 0
    if isinstance(lst,str):
        lst = json.loads(lst)
    if isinstance(lst,list):
        for item in lst:
            score = list(item.values())[0]
            if isinstance(score,str):
                score = int(score)
            total_score += score 
        
        if total_score == 100:
            succes = True
        else:
            succes = False
    return succes



def criteria_removed(data,keys_list):
    titles_to_keep = [list(d.keys())[0] for d in keys_list]
    indices_to_remove = [index for index, item in enumerate(data) if item['title'] not in titles_to_keep]
    # Remove elements from the list in reverse order of indices to avoid shifting issues
    for index in reversed(indices_to_remove):
        data.pop(index)
    return data
    