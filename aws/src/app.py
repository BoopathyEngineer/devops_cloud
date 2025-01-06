import logging
from rough import *
import json
from datetime import datetime
from extracter import extract_attachments
from settings.detection import (
    content_detection,
    duplicate_mail,
    queue_lambda_function,
    queue_sendmessage,
)
from configure import BUCKET_NAME, DEV_BATCHTABLE, DEV_USERLOGTABLE, DEV_USERTABLE
from settings.queue import delete_receipt_message, receiptid_queue_exists, receive_messages
from aws_lambda_powertools import Logger, Tracer
from s3_bucket import delete_folder
from settings.email_attachement import Outlook_mail, get_mail
from settings.dynamodb import get_item, put_item, scan_item, delete_item
from helper import date_checking
from constants import BATCHSTATUS, QUEUENAME, USERLOGTABLE, USERTABLE
from typing import Dict, Any, Optional
from env import get_env_vars
from email_integration.outlook import (
    Outlook_call_backURL,
    outlook_integration,
    outlook_refresh_tooken,
)
from email_integration.google import (
    Gmail_call_backURL,
    Google_integration,
    google_refresh_tooken,
)


#: main lambda handler
def lambda_handler(event: Dict[str, Any], context: Dict[str, Any]):

    print("event00---->", event, "\ncontext00---->", context)
    start_time = datetime.now()
    obj: dict = {}
    # obj['id'] = event["id"]
    # obj['source'] = event["source"]
    success : bool = False
    statusCode : int = 400
    response: str = "Something went wrong!"
    # if obj.get('source') == 'aws.scheduler':
        # ''' Trigger Lambda`s function based on the Scheduler '''
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    usertable = env_vars.get(USERTABLE,"user-featured6")
    if 'feature' in usertable:
        usertable = DEV_USERTABLE
    data :list = scan_item(usertable)
    try:
        final_response= []
        for i in data:
            try:
                documents = get_mail(i)
            except Exception as e:
                documents = None
            if documents:
                response : list = extract_attachments(documents)
                for ids,resp in enumerate(response):
                    valid,datalist = content_detection(resp)
                    if valid:
                        queue : dict  = queue_sendmessage(datalist)
                        # final_response.append(f'{i['email']} Queues has Been Send Successfully')
            # else:
                # final_response.append(f'{i['email']} Queues Not Send')
        statusCode = 200
        obj['response'] = final_response
    except Exception as e:
        obj['error'] = str(e)
    success = True
    end_time = datetime.now()
    time_diff = end_time - start_time
    context = {
        "success": success,
        "data": obj,
        "time_taken": time_diff.total_seconds(),
    }
    return {"statusCode": statusCode, "body": json.dumps(context)}


#: queue lambda handler
def queue_handler(event: Dict[str, Any], context: Dict[str, Any]):

    print("event01---->", event, "\ncontext01---->", context)
    success: bool = False
    obj: dict = {}
    statusCode: int = 500
    try:
        if event.get("Records"):
            records = event.get("Records")
            if isinstance(records, list):
                for i in records:
                    receipt_id = i.get("receiptHandle")
                    if i.get("body"):
                        body = i.get("body")
                        if isinstance(body, str):
                            body = json.loads(body)
                        response: dict = queue_lambda_function(body)
                        statusCode = 200
                    if receipt_id:
                        env_vars: Dict[str, Optional[str]] = get_env_vars()
                        queue = env_vars.get(QUEUENAME,'queue-featured6')
                        if receiptid_queue_exists(queue,receipt_id):
                            delete_queue_message :dict = delete_receipt_message(queue,receipt_id)
            success = True
        else:
            raise Exception("Records has been Missing")
    except Exception as e:
        obj["error"] = str(e)
    context = {"success": success, "data": obj}
    return {"statusCode": statusCode, "body": json.dumps(context)}


#: mail lambda handler
def email_handler(event: Dict[str, Any], context: Dict[str, Any]):

    print("event02---->", event, "\ncontext02---->", context)
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    batch_table = env_vars.get(BATCHSTATUS,'batch-status-featured6')
    if 'feature' in batch_table:
        batch_table = DEV_BATCHTABLE
    userlog_table = env_vars.get(USERLOGTABLE,'userlog-featured6')
    if 'feature' in userlog_table:
        userlog_table = DEV_USERLOGTABLE
    data :list= scan_item(batch_table)
    obj :dict = {}
    success: bool = False
    statusCode: int = 500
    try:
        if isinstance(data, list):
            for item in data:
                mail = item["email"]
                batch = item["batch"]
                sort_date = item["date"]
                key = {"email": mail, "date": sort_date}
                get_logdata: dict = get_item(userlog_table, key)
                if item.get("date"):
                    validate: bool = date_checking(sort_date)
                    bucket = item.get("folder")
                    if validate and bucket and int(batch) == 0:
                        if isinstance(get_logdata, dict):
                            # TODO here can change error name for
                            duplicate_list = get_logdata["error"]
                            final_mail = []
                            if (
                                get_logdata.get("csv_path")
                                and get_logdata.get("csv_path") != "null"
                            ):
                                csv_path = get_logdata.get("csv_path")
                                final_mail.append(csv_path)
                            if (
                                get_logdata.get("log_path")
                                and get_logdata.get("log_path") != "null"
                            ):
                                csv_path = get_logdata.get("log_path")
                                final_mail.append(csv_path)
                            for x in duplicate_list:
                                final_mail.append(x)
                            if isinstance(final_mail, list):
                                if len(final_mail) > 0:
                                    sender_folder = mail
                                    mailsend = duplicate_mail(
                                        mail, BUCKET_NAME, final_mail, sender_folder
                                    )
                                    """ Here Delete the S3 Bucket Folder and Delete Batch Status for User has Been Completed """
                                    key = {"email": mail}
                                    response = delete_item(batch_table, key)
                                    del_folder = delete_folder(BUCKET_NAME, bucket)
            success = True
            statusCode = 200
    except Exception as e:
        obj["error"] = str(e)

    context = {"success": success, "data": obj}
    return {"statusCode": statusCode, "body": json.dumps(context)}


def google_handler(event, context):
    value = None
    if event:
        value = event.get("queryStringParameters")
    if value:
        code = value.get("code")
        val = Gmail_call_backURL(code)

        # Getting the data from the response of the value on val
        access_token = val.get("data").get("Token")
        Integration = val.get("data").get("Integration")
        mail = val.get("data").get("mail")
        RefreshToken = val.get("data").get("RefreshToken")

        # crate the field and store the data in the table
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        usertable = env_vars.get(USERTABLE,"user-featured6")
        if 'feature' in usertable:
            usertable = DEV_USERTABLE
        if access_token and Integration:
            data: dict = {
                "email": mail,
                "Token": access_token,
                "Integration": Integration,
                "RefreshToken": RefreshToken,
            }
            success = put_item(usertable, data)
    else:
        val = Google_integration()
    return {"statusCode": 200, "body": json.dumps(val)}


def Outlook_handler(event, context):
    if event:
        value = event.get("queryStringParameters")
    if value:
        code = value.get("code")
        state = value.get("state")
        session_state = value.get("session_state")
        val = Outlook_call_backURL(code, state, session_state)

        # Getting the data from the response of the value on val
        access_token = val.get("data").get("Token")
        Integration = val.get("data").get("Integration")
        mail = val.get("data").get("mail")
        RefreshToken = val.get("data").get("RefreshToken")
        Exp = val.get("data").get("Exp")
        # crate the field and store the data in the table
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        usertable = env_vars.get(USERTABLE,"user-featured6")
        if 'feature' in usertable:
            usertable = DEV_USERTABLE
        if access_token and Integration:
            data: dict = {
                "email": mail,
                "Token": access_token,
                "Integration": Integration,
                "RefreshToken": RefreshToken,
            }
            success = put_item(usertable, data)
    else:
        val = outlook_integration()
    return {"statusCode": 200, "body": json.dumps(val)}


# getting the referesh token
def refresh_token_both(event: Dict[str, Any], context: Dict[str, Any]):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    usertable = env_vars.get(USERTABLE,"user-featured6")
    if 'feature' in usertable:
        usertable = DEV_USERTABLE
    data: list = scan_item(usertable)
    for val in data:
        if (
            "RefreshToken" in val
            and val["RefreshToken"]
            and val["Integration"] == "Google"
        ):
            RefreshToken_google = val["RefreshToken"]
            key = google_refresh_tooken(RefreshToken_google)
            if key:
                data: dict = {
                    "email": val["email"],
                    "Token": key,
                    "Integration": val["Integration"],
                    "RefreshToken": val["RefreshToken"],
                }
                success = put_item(usertable, data)
        if (
            "RefreshToken" in val
            and val["RefreshToken"]
            and val["Integration"] == "Outlook"
        ):
            RefreshToken_outlook = val["RefreshToken"]
            access = outlook_refresh_tooken(RefreshToken_outlook)
            if access:
                data: dict = {
                    "email": val["email"],
                    "Token": access,
                    "Integration": val["Integration"],
                    "RefreshToken": val["RefreshToken"],
                }
                success = put_item(usertable, data)
    context = {"success": True}
    return {"statusCode": 200, "body": json.dumps(context)}


# data = queue_handler(que01,None)
# print(data)