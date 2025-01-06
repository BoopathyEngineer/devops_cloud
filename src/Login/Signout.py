import boto3
from settings.constants import COGNITO,CLIENT
from settings.env import get_env_vars
from typing import Dict, Optional
from settings.aws_service import cognito
from Login.Reset_Password import Get_Username
client = cognito

env_vars: Dict[str, Optional[str]] = get_env_vars()
user_pool_id = env_vars.get(COGNITO,'us-east-1_546RUb4gO')
client_id = env_vars.get(CLIENT,'ovkvo2lg5g4j89rash1nmm5q5')


def Get_admin_sign_out_user(event):
    obj = {}
    if event.get('queryparams'):
        queryparams = event.get('queryparams')
        if queryparams:
            email = queryparams.get('email')
            if email:
                # user = Get_Username(email)
                if email:
                    username = email
                    try:
                        # Admin global sign out
                        client.admin_user_global_sign_out(
                            UserPoolId=user_pool_id,
                            Username=username
                        )
                        print(f"User {username} has been signed out globally by admin.")
                        obj['statusCode'] = 200
                        obj['success'] = True
                        obj['message'] = f'User {username} signed out successfully from all devices.'

                    except client.exceptions.UserNotFoundException:
                        print(f"User {username} not found.")
                        obj['statusCode'] = 404
                        obj['message'] = f'User {username} not found.'

                    except Exception as e:
                        print(f"An error occurred: {str(e)}")
                        obj['statusCode'] = 500
                        obj['message'] = f'An internal server error occurred during sign out for {username}.'
    return obj