import boto3

# Initialize the Cognito Identity Provider client
client = boto3.client('cognito-idp', region_name='us-east-1')  # Adjust your region accordingly

# Set new password without requiring an OTP
def set_new_password(user_pool_id, username, new_password):
    try:
        response = client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=new_password,
            Permanent=True  # Set to True to make this password permanent
        )
        print("Password updated successfully.")
    except Exception as e:
        print(f"Failed to update password: {str(e)}")

# Example usage
user_pool_id = 'us-east-1_tYM4L1Bcc'  # Replace with your User Pool ID
username = 'pugazhendhi'
new_password = 'Saran@123'

set_new_password(user_pool_id, username, new_password)
