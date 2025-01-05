from comparitive_analysis.constants import SYSTEM,COMPARITIVA_ANALYSIS,CATEGORIES
from helper import FineTuningModal,bytes_extract
from s3_bucket import s3_Storage
import json
import csv
from settings.configuration import JD_PARSER_ERROR, RESUME_PARSER_ERROR
import os

# Assuming this script is in the root directory of your project
base_dir = os.path.dirname(os.path.abspath(__file__))




def Lambda_Comparative(jd,resume,categories):
    if jd and resume and categories:
        system= SYSTEM
        user_message={
            "resume": resume,
            "jd":jd,
            "criteria":categories
        }
        result=FineTuningModal(system,str(user_message),COMPARITIVA_ANALYSIS)
    else:
        result = "Both JD and Resume are required to proceed further."
    return result

def is_category_valid(categories):
    final_category=[]
    removed_array=[]
    for category in categories:
        if category in CATEGORIES:
            final_category.append(category)
        else:
            removed_array.append(category)
    if len(removed_array)!=0:
        error_string=','.join(removed_array)
        final_error=error_string+" "+"the above skills are not in our list so we not considered it"
    else:
        final_error= None
    return final_category,final_error


def Lambda_Comparitive_Analysis_API(event,obj,resumes):
    if event.get('jd') and len(resumes)>1 and len(resumes)<6:
        val = []
        for i,j in event.items():
            if i not in ['jd','resume1','resume2','resume3','resume4','resume5']:
                val.append(i)
        final_skill,error=is_category_valid(val)
        result = ','.join(final_skill)
        result = '\n' + result + '\n'
        categories=json.dumps(result)
        jd_file = f'{event["jd"]["filename"]}.pdf'
        resume_list=[]
        new_obj = {}
        for resume in resumes:
            resume_file = f'{resume["filename"]}'
            resume_store = s3_Storage(resume,resume_file,folder='Resume/')
            if len(resume_store) == 0:
                new_obj['error'] = RESUME_PARSER_ERROR
            resume_list.append(resume_store)
       
        jd = s3_Storage(event['jd'],jd_file,folder='Jd/')
        if len(jd) == 0:
            new_obj['error'] = JD_PARSER_ERROR
            new_obj['statusCode'] = 400
        if new_obj.get('error') == None:
            data,token = Lambda_Comparative(jd,resume_list,categories)
            if isinstance(data,str):
                data = json.loads(data)
            if isinstance(data,dict):
                data = data.get('response')
                data = hiring_recommentation(data)
                if event.get('csv'):
                    csv_download = csv_writer(data)
                    new_obj["filepath"] = csv_download
                if len(data) != 1:
                    new_obj['response'] = data
                    new_obj['statusCode'] = 200
                    new_obj['success'] = True
                    data = new_obj['response']
                    # Initialize lists for storing values
                    arr, arrs = [], []
                    # Loop once through data to extract 'Total matching percentage' and 'Roles and Responsibilities'
                    for i in data:
                        if isinstance(i, dict):
                            value = i.get('Total matching percentage')
                            roles = i.get('Roles and Responsibilities')
                            if value:
                                arr.append(value)
                            if roles:
                                arrs.append(roles)

                    # Get max values for Total Matching Percentage and Roles
                    Max_val_Ai = max(arr) if arr else None
                    Max_val_roles = max(arrs) if arrs else None

                    # Initialize counts
                    count_max_Ai = sum(1 for i in data if isinstance(i, dict) and i.get('Total matching percentage') == Max_val_Ai)
                    count_max_roles = sum(1 for i in data if isinstance(i, dict) and i.get('Roles and Responsibilities') == Max_val_roles)

                    # Assign AI Recommendation based on conditions
                    for i in data:
                        if isinstance(i, dict):
                            total_matching_percentage = i.get('Total matching percentage')
                            roles = i.get('Roles and Responsibilities')

                            if count_max_Ai > 1:  # Multiple with max Total Matching Percentage
                                if count_max_roles > 1:  # Multiple with max Roles and Responsibilities
                                    i['Ai Recommendation'] = (roles == Max_val_roles)
                                elif count_max_roles == 1:  # Only one has max Roles and Responsibilities
                                    i['Ai Recommendation'] = (roles == Max_val_roles)
                                else:
                                    i['Ai Recommendation'] = False
                            else:  # Only one has max Total Matching Percentage
                                i['Ai Recommendation'] = (total_matching_percentage == Max_val_Ai)
                    # Assign token to new_obj
                    new_obj['token'] = token
                else:
                    if new_obj.get('error') == None:
                        new_obj['response'] = "Cannot Proceed With Single Resume"
                        new_obj['statusCode'] = 400
        return new_obj


def categories_removed(data,keys_list):
    indices_to_remove = [index for index, item in enumerate(data) if item not in keys_list]
    # Remove elements from the list in reverse order of indices to avoid shifting issues
    for index in reversed(indices_to_remove):
        if isinstance(data,dict):
            data.pop(index)
    return data


def csv_writer(data):
    if isinstance(data,list):
        # Get the headers from the keys of the first dictionary
        headers = data[0].keys()
        file_path = "output.csv"
        # Writing to CSV file
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            serial_number = 1
            headers = ["S.No"] + list(headers)
            writer.writerow(headers)
            for ids,i in enumerate(data):
                row = data[ids].values()
                row = [serial_number] + list(row)
                writer.writerow(row)
                serial_number += 1
        return file_path
    
def score_calculation(score):
    if score: 
        if score >= 0 and score <= 40:
            return "Not recommended"
        if score >= 40 and score <= 80:
            return "Neutral"
        if score >= 80 and score <= 100:
            return "Strongly recommended"
    return "Not recommended"


def hiring_recommentation(data):
    if isinstance(data,list):
        for i in data:
            if i.get("Total matching percentage"):
                i['Hiring Recommendation'] = score_calculation(i['Total matching percentage'])
        return data
    return data



