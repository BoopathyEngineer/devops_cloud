import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from amazonservice.ses import send_raw_mail
from Login.Reset_Password import initiate_forgot_password
from templates.raw_html import PASSWORD_RESET_EMAIL_CONTENT
from settings.constants import COGNITO,CLIENT
from settings.env import get_env_vars
from typing import Dict, Optional
from settings.aws_service import cognito
client = cognito

env_vars: Dict[str, Optional[str]] = get_env_vars()
user_pool_id = env_vars.get(COGNITO,'us-east-1_546RUb4gO')
client_id = env_vars.get(CLIENT,'ovkvo2lg5g4j89rash1nmm5q5')


def Get_Send_Mail_For_Forgot_Password(event):
    obj = {}
    if event.get('queryparams'):
        queryparams = event.get('queryparams')
        if queryparams:
            email = queryparams.get('email')
        if not email:
            obj['statusCode'] = 400
            obj['message'] = 'Email is required.'
            return obj
        
        try:
            response = client.list_users(
                UserPoolId=user_pool_id,
                Filter=f'email = "{email}"'
            )

            # Generate password reset link
            reset_link = f"https://localhost:3000/reset-password?email={email}"
            email_body = PASSWORD_RESET_EMAIL_CONTENT.format(
                recipient=email,
                reset_link=reset_link
            )

            # Prepare the email object
            email_obj = {
                'recipient': email,
                'subject': 'Password Reset Request',
                'body': email_body
            }

            # Send the password reset email
            email_success = send_raw_mail(email_obj)
            if email_success:
                print(f"Password reset email sent to {email}.")
                obj['success'] = True
                obj['statusCode'] = 200
                obj['message'] = 'Password reset email has been sent successfully.'
            else:
                obj['success'] = False
                obj['statusCode'] = 500
                obj['message'] = 'Failed to send password reset email.'

        except client.exceptions.UserNotFoundException:
            print(f"Email {email} does not exist.")
            obj['statusCode'] = 404
            obj['message'] = 'Email not found.'

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            obj['statusCode'] = 500
            obj['message'] = 'An internal server error occurred.'

    return obj



def Get_Forgot_Password(event, user_id, email):
    obj = {}
    
    if event.get('queryparams'):
        queryparams = event.get('queryparams')
        
        if queryparams:
            email = queryparams.get('email')
            new_password = queryparams.get('new_password')
        
        # Validate if required parameters are provided
        if not email or not new_password:
            obj['statusCode'] = 400
            obj['message'] = 'Email and new password are required.'
            return obj

        try:
            # Check if the user exists in the User Pool
            response = client.list_users(
                UserPoolId=user_pool_id,
                Filter=f'email = "{email}"'
            )
            print(f"Email {email} exists in the User Pool.")
            
            # If authentication is successful, update the password
            client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=new_password,
                Permanent=True
            )
            
            print(f"Password for user {email} has been updated.")
            obj['success'] = True
            obj['statusCode'] = 200
            obj['message'] = 'Password updated successfully.'

        except client.exceptions.UserNotFoundException:
            print(f"Email {email} does not exist.")
            obj['statusCode'] = 404
            obj['message'] = 'Email not found.'


        except Exception as e:
            print(f"An error occurred: {str(e)}")
            obj['statusCode'] = 500
            obj['message'] = 'An internal server error occurred.'

    return obj
