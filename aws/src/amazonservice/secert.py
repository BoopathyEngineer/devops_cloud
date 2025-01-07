import boto3
from botocore.exceptions import ClientError
from settings.aws_service import secert

def store_secret(secret_name, secret_value):
    try:
        response = secert.create_secret(
            Name=secret_name,
            SecretString=secret_value
        )
        return response
    except ClientError as e:
        return e


def get_secret(secret_name):
    try:
        get_secret_value_response = secert.get_secret_value(
            SecretId=secret_name
        )
        # Check if the secret uses a string or binary and return appropriately
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return get_secret_value_response['SecretBinary']
    except ClientError as e:
        return e


def update_secret(secret_name, new_secret_value):   
    try:
        response = secert.update_secret(
            SecretId=secret_name,
            SecretString=new_secret_value
        )
        print("Secret updated successfully:", response['ARN'])
    except ClientError as e:
        print("An error occurred:", e)

# # Example usage
# updated_secret_data = '{"STRIPE_SECRET_KEY":"sk_test_51IsaJzJK7wwywY1K08oalOKH7UWogsWBOp4BsbTeKLPwdFYF3VpKORZcdZZYqsUdiivOvRUhKzrs73m1CKTCJnMC00ZnAbrrtU","STRIPE_PUBLISHABLE_KEY":"pk_test_51IsaJzJK7wwywY1KAEAC7m8fWDTPQVJ8zInpb5mrY1p0UzXkbP0fnllZ63ePAtD2Qi9zkhz1B9hYOcUBFtcvgoKQ00K3SZCf2C"}'
# update_secret('dev_stripe', updated_secret_data)


