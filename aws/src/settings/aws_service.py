
import boto3
from settings.constants import REGION
# Initialize Services in aws
cognito = boto3.client('cognito-idp', region_name=REGION)
gateway = boto3.client('apigateway')
s3 = boto3.resource('s3')
s3_client = boto3.client("s3")
dynamodb = boto3.resource('dynamodb', region_name=REGION)
dynamodb_client = boto3.client('dynamodb')
cloudformation = boto3.client("cloudformation")
textract = boto3.client('textract')
secert = boto3.client('secretsmanager')
sqs = boto3.resource("sqs")
ses = boto3.client('ses', region_name=REGION)
