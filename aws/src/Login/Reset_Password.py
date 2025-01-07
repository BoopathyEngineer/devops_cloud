import boto3
from settings.constants import COGNITO,CLIENT
from settings.env import get_env_vars
from typing import Dict, Optional
from settings.aws_service import cognito
client = cognito

env_vars: Dict[str, Optional[str]] = get_env_vars()
user_pool_id = env_vars.get(COGNITO,'us-east-1_546RUb4gO')
client_id = env_vars.get(CLIENT,'ovkvo2lg5g4j89rash1nmm5q5')


def initiate_forgot_password(event):
    obj = {}
    if event.get('queryparams'):
        queryparams = event.get('queryparams')
        if queryparams:
            email = queryparams.get('email')
            try:
                # user = Get_Username(email)
                if email:
                    username = email
                    print(username,'user')
                    print(f"Username for the email {email} is {username}")
                    response = client.list_users(
                        UserPoolId=user_pool_id,
                        Filter=f"email=\"{email}\"")
            
                    if response.get('Users'):
                        response = client.forgot_password(
                        ClientId=client_id,
                        Username=username
                        )
                        print(f"Password reset initiated for {email}.")
                        obj['statusCode'] = 200
                        obj['success']= True
                        obj['message']= 'Password reset code sent to email.'
                    else:
                        print("No user found with that email.")
                        obj['statusCode'] = 400
                        obj['message'] = 'This email is not registered with GXP.'
                else:
                    obj['statusCode'] = 400
                    obj['message'] = 'Please enter the email address registered with GXP.'

            except client.exceptions.UserNotFoundException:
                print(f"User with email {email} not found.")
                obj['statusCode'] = 404
                obj['success']= False
                obj['message']= 'User not found.'

            except client.exceptions.LimitExceededException:
                    print(f"Limit exceeded for sending OTP to {email}.")
                    obj['statusCode'] = 429
                    obj['success'] = False
                    obj['message'] = 'You have exceeded the maximum number of OTP requests. Please try again later.'        

            except Exception as e:
                print(f"An error occurred: {str(e)}")
                obj['message']= 'An internal server error occurred.'
        else:
            obj['message'] = 'Provide the valid email to proceed for reset password'
    else:
        obj['message'] = 'Provide the valid email to proceed for reset password'
    return obj


def verify_code_and_reset_password(event):
    obj = {}
    if event.get('queryparams'):
        queryparams = event.get('queryparams')
        if queryparams:
            email = queryparams.get('email')
            confirmation_code=queryparams.get('confirmation_code')
            new_password=queryparams.get('new_password')
            user = Get_Username(email)
            username = user['username']
            print(username,'user')
            if not new_password:
                obj['success']= False
                obj['message']= 'Please provide new password'
            else:
                try:
                    response = client.confirm_forgot_password(
                        ClientId=client_id,
                        Username=username,
                        ConfirmationCode=confirmation_code,
                        Password=new_password
                    )
                    print(f"Password has been reset for {username}.")
                    obj['statusCode'] = 200
                    obj['success']= True
                    obj['message']= 'Password reset successfully.'

                except client.exceptions.CodeMismatchException:
                    print(f"Invalid confirmation code for {username}.")
                    obj['statusCode'] = 400
                    obj['success']= False
                    obj['message']= 'Invalid confirmation code.'

                except client.exceptions.ExpiredCodeException:
                    print(f"Confirmation code expired for {username}.")
                    obj['statusCode'] = 400
                    obj['success']= False
                    obj['message']= 'Confirmation code expired.'

                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    obj['success']= False
                    obj['message']= 'An internal server error occurred.'
        else:
            obj['message'] = 'Please provide the proper Username, Confirmation Code, New Password'
    else:
        obj['message'] = 'Please provide the proper Username, Confirmation Code, New Password'
    
    return obj

def Get_Username(email):
    obj = {}
    if email:
        response = client.list_users(
            UserPoolId=user_pool_id,
            Filter=f'email = "{email}"',
            Limit=1
        )    
        if response['Users']:
            username = response['Users'][0]['Username']
            print(username,'user')
            obj['username'] = username
    return obj

# email = "saransaran6967@gmail.com"
# username = Get_Username(email)
# print(username['username'],'user')

