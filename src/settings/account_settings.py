from typing import Dict
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

from settings.constants import COGNITO,CLIENT
from settings.env import get_env_vars
from typing import Dict, Optional
from settings.aws_service import cognito
client = cognito


env_vars: Dict[str, Optional[str]] = get_env_vars()
user_pool_id = env_vars.get(COGNITO,'us-east-1_546RUb4gO')
client_id = env_vars.get(CLIENT,'2ttg8rmnvmtmb0ckfn6ffpff0k')

def Patch_Account_Settings(event: Dict, user: str, email: str, username: str) -> Dict:
    obj = {}
    if event.get('body'):
        body = event.get('body')
        if body:
            email = body.get('email')
            user_id = body.get('userid')
            first_name = body.get('firstname')
            last_name = body.get('lastname')
            org_name = body.get('orgname')

            attributes_to_update = []

            if email:
                attributes_to_update.append({'Name': 'email', 'Value': email})
            if first_name:
                attributes_to_update.append({'Name': 'custom:firstname', 'Value': first_name})
            if last_name:
                attributes_to_update.append({'Name': 'custom:lastname', 'Value': last_name})
            if org_name:
                attributes_to_update.append({'Name': 'custom:orgname', 'Value': org_name})
            
            if attributes_to_update:
                response = client.admin_update_user_attributes(
                    UserPoolId=user_pool_id,
                    Username=username,
                    UserAttributes=attributes_to_update
                )
                response = client.admin_get_user(
                    UserPoolId=user_pool_id,
                    Username=username
                )
        
        # Extract and return the attributes in a dictionary format
                user_attributes = {coverting_attributes(attr['Name']): attr['Value'] for attr in response['UserAttributes']}
                obj['message'] = 'User attributes updated successfully.'
                obj['statusCode'] = 200
                obj['success'] = True
                obj['response'] = user_attributes
            else:
                obj['message'] = 'No attributes to update.'
                obj['statusCode'] = 400

    return obj


def Get_Account_Settings(event: Dict, user: str, email: str, username: str) -> Dict:
    obj = {}
    try:
# Fetch user attributes using the user pool ID and username
        response = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        
        # Extract and return the attributes in a dictionary format
        user_attributes = {coverting_attributes(attr['Name']): attr['Value'] for attr in response['UserAttributes']}
        if user_attributes.get('firstName') == None:
            user_attributes['firstName'] = ""
        if user_attributes.get('lastName') == None:
            user_attributes['lastName'] = ""
        if user_attributes.get('organisationName') == None:
            user_attributes['organisationName'] = "Sense7ai"

        cleaned_attributes = user_attributes

        obj['statusCode'] = 200
        obj['success'] = True
        obj['response'] = cleaned_attributes
    except client.exceptions.UserNotFoundException:
        obj['error'] = "User not found."
    except Exception as e:
        print(f"An error occurred: {e}")
    return obj


def coverting_attributes(name):
    if name.startswith('custom:'):
        name = name.replace('custom:', ' ', 1).strip()
    if name == "organisation":
        return "organisationName"
    if name == "sub":
        return "organisationID"
    if name == "lastname":
        return "lastName"
    if name == "firstname":
        return "firstName"
    return name



