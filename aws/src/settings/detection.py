from mail import send_raw_mail
from configure import (
    BATCHES,
    DEV_BATCHTABLE,
    DEV_USERLOGTABLE,
    FILES,
    FROM_ADDRESS,
    TO_ADDRESS,
    get_env_vars,
    BUCKET_NAME,
)
from helper import DCQC_Modal, extract_text_from_pdf
from s3_bucket import (
    copy_object,
    get_folder_files,
    put_folder,
    put_object,
    s3_Storage,
    s3_file_download,
)
from settings.queue import send_message
from constants import BATCHSTATUS, QUEUENAME, S3BUCKETS, USERLOGTABLE
from settings.dynamodb import put_item, update_item, get_item
from settings.download import csv_upload_to_s3_direct, upload_log
from projects.classfication import check_name_in_structure, classfication_s3, JSON_DATA
from extracter import remove_symbols
from templates.raw_format import DUPLICATE_EMAIL_CONTENT
from datetime import datetime
import json
from typing import Dict, Optional, Any
from decimal import Decimal
import base64
from io import StringIO


"""
Here its Duplicate Email Send Functions
"""


def duplicate_mail(mail, bucket, files, folder):
    obj = {}
    obj["subject"] = "Action Required: Correct and Resend Document"
    obj["bucket"] = bucket
    obj["files"] = files
    obj["sender"] = FROM_ADDRESS
    obj["recipent"] = mail
    BODY_HTML = DUPLICATE_EMAIL_CONTENT.format(receipt=mail, folder_name=folder)
    obj["body"] = BODY_HTML
    success = send_raw_mail(obj)
    return success


"""
Content & Filename Duplicate Handling 
"""


def content_detection(lst):
    obj = {}
    success = False
    try:
        date = datetime.now()
        duplicate_filename = []
        if isinstance(lst, dict):
            if lst.get("sender"):
                sender = lst["sender"]
                receiver = remove_symbols(lst["receiver"])
                message_id = lst["message_id"]
                env_vars: Dict[str, Optional[str]] = get_env_vars()
                folder_creation = put_folder(
                    BUCKET_NAME, sender
                )  #### Discussion With Team either From or To
                is_active, get_files = get_folder_files(BUCKET_NAME, sender)
                if lst.get("attachments"):
                    attached_list = lst.get("attachments")
                    date = ""
                    for i in attached_list:
                        filename = i['filename']
                        size = i['size']
                        date = i['lastModifiedDateTime']
                        content = i['content']
                        folder = FILES +'/'+filename
                        print("filename!!!",filename)
                        temp_folder = BATCHES+ '/' + message_id +'/'+filename
                        try:
                            temp_folder = s3_Storage(content,temp_folder,filename)
                        except:
                            pass
                        # storage = put_object(BUCKET_NAME,folder,filename,content)                
                    success = True
                    files_folder = BATCHES + "/" + message_id
                    s3_files, datalist = get_folder_files(BUCKET_NAME, files_folder)
                    obj["message_id"] = message_id
                    obj["sender"] = sender
                    obj["s3_files"] = datalist
                    obj["filelength"] = len(datalist)
                    obj["receiver"] = receiver
                    obj["date"] = date
    except Exception as e:
        print("content_detection Exceptions", e)
        obj["error"] = str(e)
    return success, obj


"""
send the queue message for items 
"""


def queue_sendmessage(obj: Dict[str, Any]):
    if isinstance(obj, dict):
        obj = json.dumps(obj)
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    queue = env_vars.get(QUEUENAME,'queue-featured6')
    response = send_message(queue,obj)
    return response


"""
Dyanmo Db Update the Values
"""
def result_updateTable(result,obj,csv_path,log_path):
    file_length = obj['filelength']
    files = obj['s3_files']
    user_mail = obj['receiver']
    sender = obj['sender']
    date = obj['date']
    if isinstance(result,dict):
        obj['result'] = result['success']
        obj['failure'] = result['failure']
    #TODO :- Working on a S3 Response File Storage
    data = {"email": f'{sender}',"date":date,"error": result['failure'],"file_name": result['success'],
    "receiver": user_mail ,"status": False,"timestamp": date,"file_length":file_length,'files':files,'csv_path': csv_path,'log_path':log_path}
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    userlog_table = env_vars.get(USERLOGTABLE,'userlog-featured6')
    if 'feature' in userlog_table:
        userlog_table = DEV_USERLOGTABLE
    success = put_item(userlog_table,data)
    classfication = classfication_s3(obj)
    return success


"""
queue Lambda Handler Function
"""


def queue_lambda_function(body):
    file_length = body["filelength"]
    files = body["s3_files"]
    mail_id = body["sender"]
    folder_name = body["message_id"]
    date = body["date"]
    filehandle: dict = {}
    success_response = []
    failure_response = []
    csv_response = []
    csv_filename = f"{date}.csv"
    log_filename = f"{date}.txt"
    db_batch = batch_status_updation(mail_id, file_length, date, folder_name)
    is_success, get_existing_file = get_folder_files(BUCKET_NAME, f"{FILES}/")
    log_file = StringIO()
    print("###",files)
    if isinstance(files,list):
        for ids,i in enumerate(files):
            filename =  BATCHES +'/'+ folder_name + '/' + i
            print("filename----->",filename)
            if i not in get_existing_file:
                ''' If Not Exist Process Continue ..'''
                #TODO - Integrate the Chatgpt Modal for DCQC And Based on Write a CSV Write
                parsed_text = s3_file_download(BUCKET_NAME,filename,i)
                response,token = DCQC_Modal(parsed_text,ids)
                #<----For Logging Purpose For Both ------>
                is_active = False
                if is_active:
                    final_obj = response.get('classification')
                    category = final_obj.get('category')
                    category_check = check_name_in_structure(JSON_DATA,category)
                    if category_check != "Not Applicable":
                        log_file.write(f'INFO :- {i} Has Been Classified Under This {category_check}  \n\n')
                    else:
                        log_file.write(f'ERROR :- {i} Has Been Classified Under This {category_check}  \n\n')
                else:
                    log_file.write(f'INFO :- {i} Has Been Classified \n\n')
                if isinstance(response,dict):
                    response['filename'] = i
                    reduce = batch_status_detection(mail_id)
                    success_response.append(response)
                    response["success"] = "Processed"
                    csv_response.append(response)
                new_path  = f'{FILES}/{i}'
                copy_obj = copy_object(BUCKET_NAME,filename,new_path)
                category = response.get('Category') if response.get('Category') else "Others"
            else:
                ''' Already Exist File to Return Back TO the User Folder'''
                log_file.write(f"ERROR :- {i} is Already Exists \n\n")
                error_file = BATCHES + "/" + folder_name + "/" + i
                new_path = f'{mail_id}/{i}'
                copy_object(BUCKET_NAME,filename,new_path)
                failure_response.append(error_file)
                reduce = batch_status_detection(mail_id)
        filehandle['success'] = success_response
        filehandle['failure'] = failure_response
        ''' Here Download the CSV format and Uplod in S3 bucket for Send Mail Attachments'''
        csv_path = csv_upload_to_s3_direct(csv_response,BUCKET_NAME,mail_id,csv_filename)  
        log_path = upload_log(BUCKET_NAME,log_filename,mail_id,log_file.getvalue()) 
        db_updation = result_updateTable(filehandle,body,csv_path,log_path)    
        return True
    return False


"""
Batch Status Length Updation
"""


def batch_status_updation(mail: str, count: int, date: str, folder: str):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    batch_table = env_vars.get(BATCHSTATUS,'batch-status-featured6')
    if 'feature' in batch_table:
        batch_table = DEV_BATCHTABLE
    data : dict = {"email": mail,"date": date,"batch": count,'folder':folder,'totalfile': count}
    success = put_item(batch_table,data)
    return success


"""
Batch Status Detection
"""


def batch_status_detection(mail):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    batch_table = env_vars.get(BATCHSTATUS,'batch-status-featured6')
    if 'feature' in batch_table:
        batch_table = DEV_BATCHTABLE
    key = {'email': mail}
    item = get_item(batch_table,key)
    current_batch = item.get('batch', 0)
    if int(current_batch) > 0:
        expression = "SET #b = #b - :val"
        expression_names = {"#b": "batch"}
        expression_values = {":val": Decimal(1)}
        response = update_item(
            batch_table, key, expression, expression_values, expression_names
        )
        return response


"""
Scan The Table Name With Mail Send Function
"""


# s3 = boto3.client("s3")
# s3 = boto3.resource('s3')
# bucket = s3.Bucket('zita')

# filename = 'src/Physical_therapist.docx'
# with open(filename, 'rb') as file:
#     file_content = file.read()
# response = bucket.put_object(
#             Bucket='zita',
#             ContentType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
#             Key= 'Jd'+'/' + 'Physical_therapist01.docx',
#             Body=file_content
#         )
