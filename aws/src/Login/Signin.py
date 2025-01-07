import boto3
from botocore.exceptions import ClientError
from settings.constants import COGNITO,CLIENT
from settings.env import get_env_vars
from typing import Dict, Optional
from settings.aws_service import cognito
from Login.Reset_Password import Get_Username
client = cognito
import re



env_vars: Dict[str, Optional[str]] = get_env_vars()
user_pool_id = env_vars.get(COGNITO,'us-east-1_546RUb4gO')
client_id = env_vars.get(CLIENT,'ovkvo2lg5g4j89rash1nmm5q5')


def Get_signin_api(event):
    obj = {}
    if event.get('queryparams'):
        queryparams = event.get('queryparams')
        if queryparams:
            email_username = queryparams.get('username')
            password = queryparams.get('password')
            if not email_username:
                obj['statusCode'] = 404
                obj['message'] = 'Email not found.'
                return obj
            else:
                email_exist = find_username(email_username)
                email = email_username
                if not email_exist:
                    obj['statusCode'] = 404
                    obj['message'] = 'This email is not registered with Zita.'
                    return obj
                
            if not password:
                obj['statusCode'] = 404
                obj['message'] = 'Password not found'
                return obj
            
            user_status = client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )

            if user_status['UserStatus'] != 'CONFIRMED':
                obj['message'] = 'This account has not been verified yet.'
                obj['statusCode'] = 400
                return obj
            else:
                try:                
                    response = client.initiate_auth(
                        ClientId=client_id,
                        AuthFlow='USER_PASSWORD_AUTH',
                        AuthParameters={
                            'USERNAME': email,
                            'PASSWORD': password
                        }
                    )
                    print(f"User {email} authenticated successfully.")
                    if 'AuthenticationResult' in response:
                        id_token = response['AuthenticationResult']['IdToken']
                        access_token = response['AuthenticationResult']['AccessToken']
                        refresh_token = response['AuthenticationResult']['RefreshToken']
                        print("Sign in successful!")
                        userobj = user_profile(access_token)
                        obj['id_token'] = id_token
                        obj['access_token'] = access_token
                        obj['refresh_token'] = refresh_token
                        obj['user_profile'] = userobj
                        obj['success'] = True
                        obj['statusCode'] = 200
                        obj['message'] = 'Sign in successfully.'
                    else:
                        obj['message'] = 'Incorrect username or password.'
                    

                except client.exceptions.NotAuthorizedException:
                    obj['statusCode'] = 401
                    obj['message'] = 'Incorrect email or password.'

                except client.exceptions.UserNotFoundException:
                    obj['statusCode'] = 404
                    obj['message'] = 'User not found.'

                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    obj['statusCode'] = 500
                    obj['message'] = 'An internal server error occurred.'
        else:
            obj['message'] = 'Provide the valid email and password to proceed for signin'
    else:
        obj['message'] = 'Provide the valid email and password to proceed for signin'
        
    return obj


def find_username(email_username):
    # Check if input is an email or username
    if re.match(r"[^@]+@[^@]+\.[^@]+", email_username):
        try:
            response = client.list_users(
                UserPoolId=user_pool_id,
                Filter=f'email = "{email_username}"',
                Limit=1
            )
            if response['Users']:
                # If user is found, return the username
                return response['Users'][0]['Username']
            else:
                return None
        except client.exceptions.ClientError as e:
            print(f"An error occurred while looking up the email: {str(e)}")
            return None
    else:
        # It's already a username
        return email_username
    



def user_profile(token):
    obj = {}
    try:
        # Get user information
        user_info = client.get_user(
            AccessToken=token
        )
        # Extract the username and sub (user ID)

        username = user_info['Username']
        sub = None
        firstName = None
        lastName = None
        # Extract 'sub' from user attributes
        for attribute in user_info['UserAttributes']:
            # print(attribute,'gggg')
            if attribute['Name'] == 'sub':
                sub = attribute['Value']
                obj['user_id'] = sub
            if attribute['Name'] == 'custom:firstname':
                firstName = attribute['Value']
            if attribute['Name'] == 'custom:lastname':
                lastName = attribute['Value']
        
        if firstName and lastName:
            obj['firstName'] = firstName
            obj['lastName'] = lastName
            obj['username'] = username
        elif firstName and not lastName:
            obj['firstName'] = firstName
            obj['lastName'] = lastName
            obj['username'] = username
        else:
            obj['username'] = username
            obj['firstName'] = firstName
            obj['lastName'] = lastName

    except Exception as e:
        obj['error'] = str(e)
    return obj