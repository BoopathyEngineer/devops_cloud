
from helper import FineTuningModal,bytes_extract
from s3_bucket import s3_Storage
from interview_questions_api.constants import INTERVIEW_QUESTIONS, SYSTEM
import json
from settings.configuration import JD_PARSER_ERROR, RESUME_PARSER_ERROR


def Lambda_Interview_Questions(jd,resume,criteria,questions):
    if jd and resume:
        system= SYSTEM
        user_message={"jd": jd,"criteria": criteria,"questions": questions}
        result= FineTuningModal(system,str(user_message),INTERVIEW_QUESTIONS)
    else:
        result = "Both JD and Resume are required to proceed further."
    return result

def Lambda_Interview_Questions_API(event,obj):
    new_obj = {}
    if event.get('jd') and event.get('resume'):
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
        questions_criteria = bytes_extract(event['criteria']['content'])
        total_questions = 0
        if event.get('criteria'):
            if isinstance(questions_criteria,list):
                for i in questions_criteria:
                    if i.get('count').isdigit() ==True:
                        total_questions += int(i.get('count'))
        if new_obj.get('error') == None:
            data,token = Lambda_Interview_Questions(jd,resume, questions_criteria, total_questions)
            print("data",data)
            if isinstance(data,str):
                data = json.loads(data)
            if 'response' in data:
                for r in data['response']:
                    if 'priority' in r:
                        del r['priority']
            if 'reponse' in data:
                for r in data['reponse']:
                    if 'priority' in r:
                        del r['priority']

            new_obj["response"] = data.get('response')
            new_obj['statusCode'] = 200
            new_obj['success'] = True
            new_obj["token"] = token
        return new_obj
    else:
        new_obj['error'] = "Key has been Missing"
        new_obj['statusCode'] = 400
        return new_obj