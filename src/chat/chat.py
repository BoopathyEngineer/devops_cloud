# from chat.constants import GXP_CREATION_AI, SYSTEM
from openai_client import client

from settings.constants import COGNITO,CLIENT
from typing import Dict, List
import json
import time
from s3_bucket import s3_Storage
from typing import Dict, Optional
from settings.env import get_env_vars
from settings.constants import APIGATEWAY
env_vars: Dict[str, Optional[str]] = get_env_vars()
import boto3
client_id = env_vars.get(CLIENT,'ovkvo2lg5g4j89rash1nmm5q5')
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
from amazonservice.dynamodb import get_item, put_item, delete_item, query_item, scan_item, update_item
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  

def openai_chat_creations(system, user_messages, thread_id, email):
    try:
        print("####################",thread_id)
        if not thread_id:
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            thread = client.beta.threads.create()
            thread_id = thread.id
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("Created new thread:", thread_id)
            
            table = 'gxp_user-dev'
            item = {
                'user_id': email,
                'thread_id': thread_id,
                "created_at": thread.created_at,
                "title": " ".join(user_messages.split()[:4])

            }
            put_item(table, item)
        message_id = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_messages,
              metadata={"input":f'{user_messages}',
                       "validation": 'Validate and return the response in markdown format'
                       }
        )
        print("Message added to thread:", message_id)

        # Start a new run
        my_run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id="asst_MbHVq9H55Z3ShDJNIA3UUJtb",
        )

        # Wait for the run to complete
        while my_run.status in ["queued", "in_progress"]:
            keep_retrieving_run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=my_run.id
            )
            print(my_run, "!@@@@@@@@@@@@@@@", keep_retrieving_run)
            if keep_retrieving_run.status == "completed":
                break

        # Retrieve all messages from the thread
        messages_list = []
        all_messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in all_messages:
            role = getattr(message, 'role', None)
            id = getattr(message, 'id', None)
            created_at = getattr(message, 'created_at', None)
            created_at = datetime.utcfromtimestamp(created_at)
            content = None

            if role == "user":
                print("@@@@@@@@@@@@@@@")
                if hasattr(message, 'metadata') and isinstance(message.metadata, dict):
                    print("*******",message.metadata['input'])
                    content = message.metadata
            elif role == "assistant":
                print("assistantassistantassistant")
                if hasattr(message, 'content') and isinstance(message.content, list) and message.content:
                    first_content_block = message.content[0]
                    if hasattr(first_content_block, 'text') and hasattr(first_content_block.text, 'value'):
                        content = first_content_block.text.value
            
            messages_list.append({
                "id": id,
                "role": role,
                "content": content,
            })

        return messages_list, thread_id
    except Exception as e:
        print("Error in openai_chat_creations:", str(e))
        raise

def gpt_chat(event: Dict, user: str, email: str, username: str) -> Dict:
    try:
        body = event.get('body')
        user_messages = body.get('user_messages')
        thread_id = body.get('thread_id', '')
        system = "you are a helpful assistant"
        # Call the OpenAI chat API
        print("@@@@@@@@@@@@@@@@@@@",thread_id)
        response, thread_id = openai_chat_creations(system, user_messages, thread_id, email)
        return {
            "success": True,
            
                "response": response[::-1],
                "thread_id": thread_id,
                "statusCode": 200
        }
    except Exception as e:
        error_message = f"Error in gpt_chat: {str(e)}"
        print(error_message)
        return {"success": False, "error": error_message}

from s3_bucket import extract_text_from_pdf
from datetime import datetime, timedelta
from typing import Dict, List

def retrieve_chat_list(event: Dict, user: str, email: str, username: str) -> Dict:
    value = email
    table = "gxp_user-dev"
    data = query_item(table, 'user_id', value)
    grouped_threads = group_threads_by_date(data)
    print(grouped_threads)
    return {
        "success": True,
        "response": grouped_threads,
        "statusCode": 200
    }

def group_threads_by_date(data: List[Dict]) -> Dict[str, List[Dict]]:
    # Get the current time
    now = datetime.utcnow()

    # Create time ranges
    today_start = datetime(now.year, now.month, now.day)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Initialize groups
    grouped_data = {
        "Today": [],
        "Yesterday": [],
        "Previous 7 Days": [],
        "Previous 30 Days": [],
        "Older": []
    }

    # Group data based on `created_at` timestamp
    for record in data:
        created_at = record.get('created_at')
        if not created_at:
            continue

        # Convert timestamp to datetime
        created_at_date = datetime.utcfromtimestamp(created_at)

        if created_at_date >= today_start:
            grouped_data["Today"].append(record)
        elif created_at_date >= yesterday_start:
            grouped_data["Yesterday"].append(record)
        elif created_at_date >= week_start:
            grouped_data["Previous 7 Days"].append(record)
        elif created_at_date >= month_start:
            grouped_data["Previous 30 Days"].append(record)
        else:
            grouped_data["Older"].append(record)

    # Sort each group by `created_at` in descending order and remove empty groups
    grouped_data = {
        key: sorted(records, key=lambda x: x.get('created_at', 0), reverse=True)
        for key, records in grouped_data.items() if records
    }

    return grouped_data


def delete_chat(event: Dict, user: str, email: str, username: str) -> Dict:
    print("!!!!!!!!!!!!!!!!!!!",event)
    body = event.get('body')
    thread_id = body.get('thread_id')
    try:
            print("####################",thread_id)

            table = 'gxp_user-dev'
            table=dynamodb.Table(table)
            key = {
                "user_id": email,
                "thread_id": thread_id
            }
            print("^^^^^^^^^^^^^^^",key)

            response=table.delete_item(Key=key)
            print("!!!!!!!!!!!!",response)
            return {
                    "success": True,
                    "message": "item deleted successfully",
                    "statusCode": 200
                }

    except   Exception as error:
    
        return {
        "success": False,
        "message": "invalid request",
        "error":error
    }

def update_chat(event: Dict, user: str, email: str, username: str) -> Dict:
    body = event.get('body')
    thread_id = body.get('thread_id')
    title=body.get('title')
    table="gxp_user-dev"
    key = {
                    'user_id': email,
                    "thread_id":thread_id,
        }
    update_expression = "SET #t = :t"
    update_values = {
        ":t": title
    }
    attr_names = {
        "#t": "title"
    }
    response = update_item(
                    table,
                    key,
                    update_expression,
                    update_values,
                    attr_names
                )
    return {
        "success":True,
        "message":"update item successfully",
        "statusCode": 200

    }

def chat_list(thread_id):
    try:
        # Retrieve all messages from the thread
        messages_list = []
        all_messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in all_messages:
            role = getattr(message, 'role', None)
            id = getattr(message, 'id', None)
            created_at = getattr(message, 'created_at', None)
            created_at = datetime.utcfromtimestamp(created_at)
            content = None
            if role == "user":
                print("@@@@@@@@@@@@@@@")
                if hasattr(message, 'metadata') and isinstance(message.metadata, dict):
                    print("*******",message.metadata['input'])
                    content = message.metadata
            elif role == "assistant":
                print("assistantassistantassistant")
                if hasattr(message, 'content') and isinstance(message.content, list) and message.content:
                    first_content_block = message.content[0]
                    if hasattr(first_content_block, 'text') and hasattr(first_content_block.text, 'value'):
                        content = first_content_block.text.value
            
            messages_list.append({
                "id": id,
                "role": role,
                "content": content,
            })

        return messages_list, thread_id
    except Exception as e:
        print("Error in openai_chat_creations:", str(e))
        raise

def get_chat(event: Dict, user: str, email: str, username: str) -> Dict:
    try:
        body = event.get('body')
        thread_id = body.get('thread_id', '')
        response, thread_id = chat_list(thread_id)
        print("Chat response:", response)
        print("type response:", type(response))
        return {
            "success": True,
            
                "response": response[::-1],
                "thread_id": thread_id,
                "statusCode": 200
        }
    except Exception as e:
        error_message = f"Error in gpt_chat: {str(e)}"
        print(error_message)
        return {"success": False, "error": error_message}
def share_chat(event):
    try:
        if event.get('queryparams'):
            queryparams = event.get('queryparams')
            if queryparams:
                thread_id= queryparams.get('thread_id')
                expression= Attr('thread_id').eq(thread_id)
                table="gxp_user-dev"
                data = scan_item(table,expression=expression)
                print(len(data))
                if len(data) != 0:
                    response, thread_id = chat_list(thread_id)
                else:
                    response={
                        "status":False,
                        "message":"invalid thread_id"
                    }
       
        return {
                    "statusCode": 200,
                    "body": response
                }
            

    except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }

def openai_chat_creations2(user_messages,thread_id,email,parsed_text=None,file_name=''):
    try:
        print("user_messagesuser_messages",user_messages)
        print("####################",thread_id,parsed_text)
        print("file_namefile_namefile_namefile_name",file_name)
        if not thread_id:
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            thread = client.beta.threads.create()
            thread_id = thread.id
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("Created new thread:", thread_id)
            
            table = 'gxp_user-dev'
            item = {
                'user_id': email,
                'thread_id': thread_id,
                "created_at": thread.created_at,
                "title": " ".join(user_messages.split()[:4])

            }
            put_item(table, item)
        message_id = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content = user_messages + (parsed_text or '') + ' Validate and return the response in markdown format',
              metadata={
                  "input":f'{user_messages}',
                        "file_name":file_name,
                       }
        )
        print(file_name,"Message added to thread:", message_id)

        # Start a new run
        my_run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id="asst_MbHVq9H55Z3ShDJNIA3UUJtb",
        )

        # Wait for the run to complete
        while my_run.status in ["queued", "in_progress"]:
            keep_retrieving_run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=my_run.id
            )
            print(my_run, "!@@@@@@@@@@@@@@@", keep_retrieving_run)
            if keep_retrieving_run.status == "completed":
                break

        # Retrieve all messages from the thread
        messages_list = []
        all_messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in all_messages:
            role = getattr(message, 'role', None)
            id = getattr(message, 'id', None)
            created_at = getattr(message, 'created_at', None)
            created_at = datetime.utcfromtimestamp(created_at)
            content = None

            if role == "user":
                print("@@@@@@@@@@@@@@@")
                if hasattr(message, 'metadata') and isinstance(message.metadata, dict):
                    print("*******",message.metadata['input'])
                    content = message.metadata
            elif role == "assistant":
                print("assistantassistantassistant")
                if hasattr(message, 'content') and isinstance(message.content, list) and message.content:
                    first_content_block = message.content[0]
                    if hasattr(first_content_block, 'text') and hasattr(first_content_block.text, 'value'):
                        content = first_content_block.text.value

            
            messages_list.append({
                "id": id,
                "role": role,
                "content": content,
            })

        return messages_list, thread_id
    except Exception as e:
        print("Error in openai_chat_creations:", str(e))
        raise

def gpt_chat2(event: Dict, user: str, email: str, username: str) -> Dict:
    try:
        body = event.get('body')
        user_messages = body.get('user_messages')
        thread_id = body.get('thread_id', '')
        # Call the OpenAI chat API
        print("@@@@@@@@@@@@@@@@@@@",thread_id)
        try:
            resume_file = body.get('file', {}).get('filename', None)
            post_data = body["file"]
            parsed_text = s3_Storage(post_data,resume_file,folder='Resume/')
            print("&&&&&&&&&&&&&&&&",parsed_text)
            file_name=resume_file
            print("file_namefile_name",file_name)
            response, thread_id = openai_chat_creations2(user_messages,thread_id,email,parsed_text,file_name)
        except:
            pass
        response, thread_id = openai_chat_creations2(user_messages, thread_id, email)
        return {
            "success": True,
            
                "response": response[::-1],
                "thread_id": thread_id,
                "statusCode": 200
        }
    except Exception as e:
        error_message = f"Error in gpt_chat: {str(e)}"
        print(error_message)
        return {"success": False, "error": error_message}
def openai_chat_creations3(user_messages,thread_id,email,parsed_text=None,file_name=''):
    try:
        print("user_messagesuser_messages",user_messages)
        print("####################",thread_id,parsed_text)
        print("file_namefile_namefile_namefile_name",file_name)
        if not thread_id:
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            # thread = client.beta.threads.create()
            thread = client.beta.threads.create(
            messages=[
                {
                "role": "user",
                "content": user_messages ,
                "metadata":{"input":user_messages}
                },

            ]
            )
            thread_id = thread.id
            
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("Created new thread:", thread_id)
            
            table = 'gxp_user-dev'
            item = {
                'user_id': email,
                'thread_id': thread_id,
                "created_at": thread.created_at,
                "title": " ".join(user_messages.split()[:4])

            }
            put_item(table, item)
        else:
            message_id = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content = user_messages + (parsed_text or '') + ' Validate and return the response in markdown format',
              metadata={
                  "input":f'{user_messages}',
                        "file_name":file_name,
                       }
        )
            print(file_name,"Message added to thread:", message_id)
        stream = client.beta.threads.runs.create(
  thread_id=thread_id,
  assistant_id="asst_MbHVq9H55Z3ShDJNIA3UUJtb",
  stream=True
)
        messages_list = []
        all_messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in all_messages:
            role = getattr(message, 'role', None)
            id = getattr(message, 'id', None)
            created_at = getattr(message, 'created_at', None)
            created_at = datetime.utcfromtimestamp(created_at)
            content = None

            if role == "user":
                print("@@@@@@@@@@@@@@@")
                if hasattr(message, 'metadata') and isinstance(message.metadata, dict):
                    print("*******",message.metadata['input'])
                    content = message.metadata
            elif role == "assistant":
                print("assistantassistantassistant")
                if hasattr(message, 'content') and isinstance(message.content, list) and message.content:
                    first_content_block = message.content[0]
                    if hasattr(first_content_block, 'text') and hasattr(first_content_block.text, 'value'):
                        content = first_content_block.text.value

            
            messages_list.append({
                "id": id,
                "role": role,
                "content": content,
            })

        return messages_list, thread_id
    except Exception as e:
        print("Error in openai_chat_creations:", str(e))
        raise

def gpt_chat3(event: Dict, user: str, email: str, username: str) -> Dict:
    try:
        body = event.get('body')
        user_messages = body.get('user_messages')
        thread_id = body.get('thread_id', '')
        # Call the OpenAI chat API
        print("@@@@@@@@@@@@@@@@@@@",thread_id)
        try:
            resume_file = body.get('file', {}).get('filename', None)
            post_data = body["file"]
            parsed_text = s3_Storage(post_data,resume_file,folder='Resume/')
            print("&&&&&&&&&&&&&&&&",parsed_text)
            file_name=resume_file
            print("file_namefile_name",file_name)
            response, thread_id = openai_chat_creations3(user_messages,thread_id,email,parsed_text,file_name)
        except:
            pass
        response, thread_id = openai_chat_creations3(user_messages, thread_id, email)
        return {
            "success": True,
            
                "response": response[::-1],
                "thread_id": thread_id,
                "statusCode": 200
        }
    except Exception as e:
        error_message = f"Error in gpt_chat: {str(e)}"
        print(error_message)
        return {"success": False, "error": error_message}
