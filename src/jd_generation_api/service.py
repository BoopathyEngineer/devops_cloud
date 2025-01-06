import datetime
import json
import time

from openai_client import client

from helper import FineTuningModal
from jd_generation_api.constants import JD_CREATION_AI, SYSTEM
from s3_bucket import s3_Storage

def openai_chat_creations(system,user_messages):
    try:
        # Create a new thread
        thread = client.beta.threads.create()
        thread_id = thread.id

        # Add user message to the thread
        messages_id = client.beta.threads.messages.create(
            thread_id=thread_id,
            content=user_messages,
            role="user"
        )

        # Start a new run
        my_run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=JD_CREATION_AI,
        )
        # print(f"This is the run object: {my_run} \nStatus: {my_run.status} \expires_at: {datetime.utcfromtimestamp(my_run.expires_at)} \created_at: {datetime.utcfromtimestamp(my_run.created_at)}")

        # Check run status periodically
        while my_run.status in ["queued", "in_progress"]:
            keep_retrieving_run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=my_run.id
            )


            if keep_retrieving_run.status == "completed":
                all_messages = client.beta.threads.messages.list(thread_id=thread_id)
                length=len(all_messages.data)
                for ids, i in enumerate(reversed(all_messages.data)):
                    if ids == length-1:
                        response = i.content[0].text.value
                        break
                if response:
                    break
            time.sleep(5)
    except Exception as e:
        print("ChatBotGpt Exception:", e)
        return None
    return response,0

def Jd_Generation_API(event, obj):
    min_exp = event.get('min_experience')
    max_exp = event.get('max_experience',None)
    overview = event.get('overview','')
    mandatory_skills = event.get('skills','')
    nice_to_have = event.get('nice_to_have', '')
    jobTitle = event.get('job_title')
    Industry_and_Domain = event.get('industry_type')
    is_active = False
    if is_active:
        if max_exp:
            input = f'''
                "Job Title": {jobTitle},
                "overview": {overview},
                "min_exp": {min_exp},
                "max_exp": {max_exp},
                "mandatory_skills": [{mandatory_skills}],
                "nice_to_have": [{nice_to_have}],
                "Industry type": {Industry_and_Domain}
                '''
        else:
            input = f'''
                "Job Title": {jobTitle},
                "overview": {overview},
                "min_exp": {min_exp},
                "mandatory_skills": [{mandatory_skills}],
                "nice_to_have": [{nice_to_have}],
                "Industry type": {Industry_and_Domain}
                '''
        html_input = "[{Job Title:string,Roles and Responsibilities:[],Technical Skill:[],Soft Skill:[],Tools and Technologies:[],skills:[],mandatory_skills:[],nice_to_have : []}]"
    else:
        if max_exp:
            input_data = f'''
                "Job Title": {jobTitle},
                "overview": {overview},
                "min_exp": {min_exp},
                "max_exp": {max_exp},
                "mandatory_skills": [{mandatory_skills}],
                "nice_to_have": {nice_to_have},
                "Industry type": {Industry_and_Domain}
                '''
            input = input_data
        else:
            input_data = f'''
                "Job Title": {jobTitle},
                "overview": {overview},
                "min_exp": {min_exp},
                "mandatory_skills": [{mandatory_skills}],
                "nice_to_have": {nice_to_have},
                "Industry type": {Industry_and_Domain}
                '''
            input = input_data
    html_input = '''{
    "Job Title": string,
    "Roles and Responsibilities": [
        // Extracted and transformed from 'overview'
    ],
    "Minimum Experience":'min_exp' years,
    "Maximum Experience":'max_exp' years if max_exp,
    "Technical Skill": [
        // Extracted from 'mandatory_skills' and list more Technical skills related to the 'job title'. Do not include the keyword 'nice to have'. Generate in detail.
    ],
    "Soft Skill": [
        // Generate soft skills for the 'job title' and 'overview'. Generate in detail.
    ],
    "Tools and Technologies": [
        // Generate 'Tools and Technologies' which are required for 'job title', extracted from 'mandatory_skills', extracted from 'nice_to_have' but do not include the keyword 'nice to have'. Generate in detail.
    ],
    "Skills": [
        // Generic skills based on the job 'overview' and 'Industry_and_Domain'. Generate in detail.
    ],
    "mandatory_skills": [
        //list more 'mandatory_skills' related to the 'job title'. Generate 'mandatory_skills' which are required for 'job title' and 'overview'. Generate in detail.
    ],
    "nice_to_have": [
        // Parsed list from 'nice_to_have' and list more nice to have skills related to the 'job title'
    ] 
    }'''

    try:
        new_obj = {}
        user_messages = input + str(html_input)
        # is_active = False
        # if is_active:
        #     system =SYSTEM
        #     user_message = input + str(html_input)
        #     response,count_token = FineTuningModal(system,user_message)
        # else:
        system =SYSTEM
        response,count_token = openai_chat_creations(system,user_messages)
        if isinstance(response,str):
            response = json.loads(response)
            if nice_to_have == '':
                response.pop('nice_to_have')
            if response.get("is_JD"):
                del response["is_JD"]
                new_obj['response'] = response
                new_obj['statusCode'] = 200
                new_obj['success'] = True
            else:
                new_obj['error'] = "Please ensure that the information entered is accurate and relevant."
                new_obj['statusCode'] = 400
    except Exception as e:
        new_obj['error'] = str(e)
        new_obj['statusCode'] = 400
    return new_obj

