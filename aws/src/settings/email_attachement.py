from __future__ import print_function
from typing import Dict, Optional
import requests
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email_integration import settings
base_dir = settings.BASE_DIR
import os
import json



SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_mail(i):
    data = []
    if i.get("Integration"):
        integration = i.get("Integration")
        token = i.get("Token")
        if integration == "Outlook":
            mails = Outlook_mail(token)
            return mails
        if integration == 'Google':
            mails = Google_mail(token)
            return mails
    return data


def Outlook_mail(token):
    date = datetime.now().date()
    yesterday = date - timedelta(days=1)
    start_date = f"{yesterday}T00:00:00Z"
    end_date = f"{yesterday}T23:59:59Z"
    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=receivedDateTime ge {start_date} and receivedDateTime le {end_date}"
    headers = {
        "Authorization": f"Bearer {token}"  # Ensure 'token' is defined and valid
    }

    messages_with_attachments = []
    while url:
        try:
            result = requests.get(url, headers=headers)
            result.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve messages: {e}")
            raise Exception(e)

        messages = result.json().get("value", [])

        for message in messages:
            if message.get("hasAttachments"):
                message_id = message["id"]

                received_date = message["receivedDateTime"]

                # Convert receivedDateTime to the desired format
                received_datetime_obj = datetime.strptime(
                    received_date, "%Y-%m-%dT%H:%M:%SZ"
                )
                received_date_str = received_datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
                attachment_url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"

                try:
                    attachment_result = requests.get(attachment_url, headers=headers)
                    attachment_result.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(
                        f"Failed to retrieve attachments for message {message_id}: {e}"
                    )
                    continue

                attachments = attachment_result.json().get("value", [])
                sender = (
                    message.get("from", {})
                    .get("emailAddress", {})
                    .get("address", "Unknown")
                )
                recipients = [
                    recipient.get("emailAddress", {}).get("address", "Unknown")
                    for recipient in message.get("toRecipients", [])
                ]

                # Process each attachment
                for attachment in attachments:
                    if "contentBytes" in attachment:
                        # Decode the base64 encoded file content
                        import base64

                        attachment["contentBytes"] = base64.b64decode(
                            attachment["contentBytes"]
                        )

                messages_with_attachments.append(
                    {
                        "message_id": message_id,
                        "from": sender,
                        "to": recipients,
                        "attachments": attachments,
                        "date": received_date_str,
                    }
                )

        url = result.json().get("@odata.nextLink")
    return messages_with_attachments


def get_gmail_service(token):
    filepath = base_dir + '/client_secret.json'
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            json_data = json.load(file)
            json_data = json_data.get('web')
    if json_data:
        creds = Credentials(token=token,
                            token_uri=json_data.get('token_uri'),
                    client_id=json_data.get('client_id'),
                    client_secret=json_data.get('client_secret'), scopes=SCOPES)
        return build('gmail', 'v1', credentials=creds)

def Google_mail(token):
    service = get_gmail_service(token)
    user_id = "me"  # Use 'me' to indicate the authenticated user
    today = datetime.now().date()  # Get today's date
    tomorrow = today - timedelta(days=1)  # Get tomorrow's date

    # Format dates in YYYY/MM/DD format for Gmail API
    today_str = today.strftime('%Y/%m/%d')
    tomorrow_str = tomorrow.strftime('%Y/%m/%d')
    
    # Query for messages received today with attachments
    # query = f"in:inbox has:attachment after:{today_str} before:{tomorrow_str}" ## Today Mail
    query = f"in:inbox has:attachment after:{tomorrow_str} before:{today_str}" ## YesterDay Mail
    try:
        # Get messages
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = response.get("messages", [])

        messages_with_attachments = []

    
        for msg in messages:
            msg_id = msg["id"]
            msg_detail = (
                service.users().messages().get(userId=user_id, id=msg_id).execute()
            )
            internalDate = int(msg_detail["internalDate"]) / 1000.0
            date_str = datetime.fromtimestamp(internalDate).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Check if the message has attachments
            if "payload" in msg_detail and "parts" in msg_detail["payload"]:
                attachments = []
                for part in msg_detail["payload"]["parts"]:
                    if part.get("filename") and part["body"].get("size") > 0:
                        attachment_id = part["body"].get("attachmentId")
                        attachment_data = None

                        if attachment_id:
                            attachment = (
                                service.users()
                                .messages()
                                .attachments()
                                .get(userId=user_id, messageId=msg_id, id=attachment_id)
                                .execute()
                            )
                            import base64

                            attachment_data = base64.urlsafe_b64decode(
                                attachment["data"].encode("UTF-8")
                            )

                        attachments.append(
                            {
                                "filename": part["filename"],
                                "mimeType": part["mimeType"],
                                "size": part["body"]["size"],
                                "attachmentId": attachment_id,
                                "data": attachment_data,  # Store the actual data in base64 format,
                                "date": date_str,
                            }
                        )

                # Get sender email
                sender = next(
                    header["value"]
                    for header in msg_detail["payload"]["headers"]
                    if header["name"] == "From"
                )

                # Get receiver(s) email
                receivers = [
                    header["value"]
                    for header in msg_detail["payload"]["headers"]
                    if header["name"] == "To"
                ]

                messages_with_attachments.append(
                    {
                        "message_id": msg_id,
                        "from": sender,
                        "to": receivers,
                        "attachments": attachments,
                    }
                )
        return messages_with_attachments
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

