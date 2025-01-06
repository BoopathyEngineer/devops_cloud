from datetime import datetime
import re


def is_file_format(form_data):
    if 'filename="' in form_data:
        return True
    else:
        return False


def get_filename_value(form_data):
    filename_value = None
    parts = form_data.split(";")
    for part in parts:
        if part.strip().startswith("filename="):
            filename_value = part.split("=")[1].replace('"', "").strip()
            break

    return filename_value


def get_key(form_data):
    # 'form-data; name="birth_date"', 'content': b'2012-123'
    key = form_data.split(";")[1].split("=")[1].replace('"', "")
    isfile = is_file_format(form_data)
    filename_obj = get_filename_value(form_data)
    return key, isfile, filename_obj


def extract_obj(obj: dict):
    size = obj["size"]
    size = size / (1024 * 1024)
    name = obj.get("name")
    if name == None and obj.get("filename"):
        name = obj.get("filename")
    content = obj.get("contentBytes")
    if content == None and obj.get("data"):
        content = obj.get("data")
    lastModifiedDateTime = obj.get("lastModifiedDateTime")
    if lastModifiedDateTime == None:
        lastModifiedDateTime = obj.get("date")
    return {
        "filename": name,
        "size": size,
        "content": content,
        "lastModifiedDateTime": lastModifiedDateTime,
    }


def remove_symbols(string: str):
    if "<" in string:
        emails = re.findall(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", string
        )
        string = ",".join(emails)
    if isinstance(string, list):
        extracted_emails = set()  # Use a set to avoid duplicates
        email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        for item in string:
            found_emails = email_pattern.findall(item)
            extracted_emails.update(found_emails)  # Add found emails to the set
        extracted_emails = list(extracted_emails)
        return ",".join(extracted_emails)
    return string


def extract_attachments(msg: list):
    final_list: list = []
    for part in msg:
        obj: dict = {}
        obj["sender"] = remove_symbols(part["from"])
        obj["receiver"] = part["to"]
        obj["message_id"] = part["message_id"]
        attach: list = []
        if part.get("attachments"):
            attachments = part.get("attachments")
            for i in attachments:
                i = extract_obj(i)
                attach.append(i)
        obj["attachments"] = attach
        final_list.append(obj)
    return final_list
