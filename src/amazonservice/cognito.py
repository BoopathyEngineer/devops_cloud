

from settings.aws_service import cognito
import boto3
import jwt
from botocore.exceptions import ClientError
# Initialize a Boto3 client for Cognito Identity Provider


# Define your User Pool ID
user_pool_id = 'us-east-1_L8FKIEUfv'  # Extracted from your ARN




## to get the all userpool inside the users
def cognito_userpool(user_pool_id):
    all_users = []
    pagination_token = None
    try:
        while True:
            # Get a batch of users
            if pagination_token:
                response = cognito.list_users(
                    UserPoolId=user_pool_id,
                    PaginationToken=pagination_token
                )
            else:
                response = cognito.list_users(
                    UserPoolId=user_pool_id
                )

            # Extend the user list with the current batch of users
            all_users.extend(response['Users'])

            # Check if there's a pagination token; if not, break the loop
            pagination_token = response.get('PaginationToken')
            if not pagination_token:
                return all_users
    except:
        return []


## to get sub details of the users
def subuser_details(userpool,sub):
    # Replace 'your-user-pool-id' with your actual user pool ID
    response = cognito.list_users(
        UserPoolId=userpool,
        Filter='sub = "{}"'.format(sub)
    )
    # Check if any users are returned
    if response['Users']:
        user_details = response['Users'][0]  # Get the first user matching the sub ID
        return user_details
    else:
        return None
        
# Initialize a boto3 client for Cognito Identity Provider
def authenticate_user(user_pool_id, client_id, username, password):
    try:
        # Authenticate the user
        response = cognito.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        # Extract tokens from the response
        if response.get('AuthenticationResult'):
            access_token = response['AuthenticationResult']['AccessToken']
            id_token = response['AuthenticationResult']['IdToken']
            refresh_token = response['AuthenticationResult']['RefreshToken']

            # Decode ID Token to extract the sub ID
            decoded_token = jwt.decode(id_token, options={"verify_signature": False})  # Set to False for example; use a public key in production
            sub_id = decoded_token['sub']
            print("Sub ID:", sub_id)
        else:
            print("Authentication failed or additional challenge required.")
    except ClientError as e:
        print("An error occurred:", e)

# # Parameters
# user_pool_id = 'us-east-1_tYM4L1Bcc'  # Your User Pool ID
# client_id = '2c3finlh8hnb5seuko957jtkn4'  # Replace with your Cognito App Client ID
# username = 'Hello'  # The user's username
# password = 'GVTest@123'  # The user's password
# authenticate_user(user_pool_id, client_id, username, password)


def create_cognito_user(user_pool_id, username, password, email):
    try:
        response = cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'True'
                }
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'  # Suppresses sending an email
        )
        print("User created successfully:", response)
        #Set user password directly and mark it as permanent
        password_response = cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True
        )
        print("Password set successfully:", password_response)
    except ClientError as e:
        print("An error occurred:", e)

# # Parameters
# user_pool_id = 'us-east-1_tYM4L1Bcc'  # Your User Pool ID
# username = 'Hello'  # Replace with the desired username
# password = 'GVTest@123'  # Temporary password
# email = 'email@example.com'  # User's email

# # Create a new user
# create_cognito_user(user_pool_id, username, password, email)

def update_cognito_user(userpool,user,attributes):
    # Update user attributes
    response = cognito.admin_update_user_attributes(
        UserPoolId=userpool,
        Username=user,
        UserAttributes=attributes
    )
    print(response)
