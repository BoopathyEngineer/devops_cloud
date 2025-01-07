from typing import Dict
import boto3
from Login.Reset_Password import Get_Username
from settings.constants import COGNITO,CLIENT
from settings.env import get_env_vars
from typing import Dict, Optional
from settings.aws_service import cognito
client = cognito


env_vars: Dict[str, Optional[str]] = get_env_vars()
user_pool_id = env_vars.get(COGNITO,'us-east-1_546RUb4gO')
client_id = env_vars.get(CLIENT,'ovkvo2lg5g4j89rash1nmm5q5')



def Put_Change_Password_Without_Otp(event: Dict, user: str, email: str, username: str) -> Dict:
    obj = {}
    if event.get('body'):
        body = event.get('body')
        if body:
            email = body.get('email')
            current_password = body.get('current_password')
            new_password = body.get('new_password')

            if not email or not current_password or not new_password:
                obj['statusCode'] = 400
                obj['message'] = 'Email, current password, and new password are required.'
                return obj

            username = email
            try:
                # Step 1: Authenticate user to verify the current password
                auth_response = client.admin_initiate_auth(
                    UserPoolId=user_pool_id,
                    ClientId=client_id,  # Replace with your Cognito App Client ID
                    AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                    AuthParameters={
                        'USERNAME': username,
                        'PASSWORD': current_password
                    }
                )
                # If authentication is successful, proceed to change the password
                response = client.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=username,
                    Password=new_password,
                    Permanent=True
                )
                
                print(f"Password updated successfully for {username}.")
                obj['statusCode'] = 200
                obj['success'] = True
                obj['message'] = 'Password updated successfully.'

            except client.exceptions.NotAuthorizedException:
                print("The current password is incorrect.")
                obj['statusCode'] = 401
                obj['message'] = 'Entered password does not match the current password.'

            except client.exceptions.UserNotFoundException:
                print(f"User with email {email} not found.")
                obj['statusCode'] = 404
                obj['message'] = 'User not found.'

            except Exception as e:
                print(f"An error occurred: {str(e)}")
                obj['statusCode'] = 500
                obj['message'] = 'An internal server error occurred.'

        else:
            obj['statusCode'] = 400
            obj['message'] = 'Provide a valid email, current password, and new password to proceed with password change.'
    else:
        obj['statusCode'] = 400
        obj['message'] = 'Provide a valid email, current password, and new password to proceed with password change.'
    
    return obj