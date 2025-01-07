from settings.aws_service import dynamodb,dynamodb_client
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime,timedelta
import json

def decimal_default(obj):
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    raise TypeError


def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return decimal_default(obj)
    else:
        return obj
    
# Convert all float values to Decimal
def convert_float_to_decimal(data):
    if isinstance(data, list):
        return [convert_float_to_decimal(i) for i in data]
    elif isinstance(data, dict):
        return {k: convert_float_to_decimal(v) for k, v in data.items()}
    elif isinstance(data, float):
        return Decimal(str(data))
    else:
        return data

'''
Inserting Values into DynamoDB
'''

def put_item(table,item):
    table = dynamodb.Table(table)
    if isinstance(item,dict):
        response = table.put_item(
        Item=item)
        return response

'''
Retrieving Values from DynamoDB
'''
def get_item(table,key):
    table = dynamodb.Table(table)
    if isinstance(key,dict):
        response = table.get_item(Key=key)
        item = response.get('Item')
        items = convert_decimals(item)
        return items
    

'''
Updating an Item in DynamoDB
'''

def update_item(table,key,updateexpression,updateobj,attr,expression = "UPDATED_NEW"):
    # print("key",updateobj)
    table = dynamodb.Table(table)
    response = table.update_item(
        Key=key,
        UpdateExpression=updateexpression,
        ExpressionAttributeNames=attr,
        ExpressionAttributeValues=updateobj,
        ReturnValues="UPDATED_NEW"
    )
    return response

'''
Deleting an Item from DynamoDB
'''

def delete_item(table,key):
    # table = dynamodb.Table(table)
    response = table.delete_item(
        Key=key
    )
    return response

'''
Scan Item in the Table
'''

def scan_item(table,expression = None):
    table = dynamodb.Table(table)  
    if expression:
        response = table.scan(FilterExpression=expression)
    else:
        response = table.scan()
    items = response['Items']
    items = convert_decimals(items)
    return items


def query_item(table, key, value,expression=None):
    # Initialize a session using Amazon DynamoDB
    table = dynamodb.Table(table)
    # Query the table using only the partition key
    if expression:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value),
            FilterExpression=expression
        )
    else:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)
        )
    items = response.get('Items',[])
    items = convert_decimals(items)
    return items



def querysort_item(table, key, value,sortkey,sortvalue,expression=None):
    # Initialize a session using Amazon DynamoDB
    table = dynamodb.Table(table)
    print("expression",expression)

    today = datetime.now().date()
    today_date = str(today)
    # Query the table using only the partition key
    print("todaytoday",sortvalue,today_date)
    if isinstance(today_date, str):
        todate_datetime = datetime.strptime(today_date, '%Y-%m-%d')
        todate = (todate_datetime + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')

    if expression:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).between(sortvalue,todate),
            FilterExpression=expression
        )
    else:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).between(sortvalue,todate)
        )
    items = response.get('Items',[])
    items = convert_decimals(items)
    return items


def querysort(table, key, value,sortkey,sortvalue,expression=None):
    # Initialize a session using Amazon DynamoDB
    table = dynamodb.Table(table)
    if expression:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).eq(sortvalue),
            FilterExpression=expression
        )
    else:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).eq(sortvalue)
        )
    items = response.get('Items',[])
    items = convert_decimals(items)
    return items


def querysort_betweendates(table, key, value,sortkey,fromdate,todate,expression=None):
    # Initialize a session using Amazon DynamoDB
    table = dynamodb.Table(table)

    today = datetime.now().date()
    today_date = str(today)

    
    # Adjust todate to ensure it includes the full day
    if isinstance(todate, str):
        todate_datetime = datetime.strptime(todate, '%Y-%m-%d')
        todate = (todate_datetime + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')


    # Query the table using only the partition key
    print("fromdate",fromdate,"todate",todate)
    if expression:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).between(fromdate,todate),
            FilterExpression=expression
        )
    elif fromdate and todate:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).between(fromdate,todate)
        )
    else:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).between(fromdate,today_date)
        )
    items = response.get('Items',[])
    items = convert_decimals(items)
    return items


def query_beginwith(table, key, value,sortkey,sortvalue,expression=None):
    # Initialize a session using Amazon DynamoDB
    table = dynamodb.Table(table)
    if expression:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).begins_with(sortvalue),
            FilterExpression=expression
        )
    else:
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)& Key(sortkey).begins_with(sortvalue)
        )
    items = response.get('Items',[])
    items = convert_decimals(items)
    return items

#------- DynamoDB Backup 
#: Backup
def create_backup(table_name, backup_name):
    response = dynamodb_client.create_backup(
        TableName=table_name,
        BackupName=backup_name
    )
    return response

#: Restore the new items
def restore_backup(backup_arn, restored_table_name):
    response = dynamodb_client.restore_table_from_backup(
        TargetTableName=restored_table_name,
        BackupArn=backup_arn
    )
    return response

#: Restore the existing items
def restore_existing_backup(source_table,target_table):
    source_table = dynamodb.Table(source_table)
    target_table = dynamodb.Table(target_table)
    # Scan source table
    response = source_table.scan()
    items = response['Items']
    
    # Batch write items to the target table
    with target_table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)
    
    return response

#----------------------------------------------------------#
# To export table from dynamodb to S3

import json
from datetime import datetime
from botocore.exceptions import ClientError
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] =='404':
            return False
        else:
            print("Error occured while checking bucket existence")
            return False
        
def create_s3(bucket_name,region): 
    if bucket_exists(bucket_name):
        print(f"Bucket already exist")
        return bucket_name
    try:
        if region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
            print("Bucket created successfully")
        else:
            s3.create_bucket(Bucket=bucket_name,CreateBucketConfiguration={'LocationConstraint': region})
            print("Bucket created")
    except ClientError as e:
        print(f"An error occurred: {e}")
    

def get_timestamp(table):
    return f'{table}/timestamp.txt'

def get_last_timestamp(table,bucket_name):
    timestamp_s3_key=get_timestamp(table)
    try:
        response=s3.get_object(Bucket=bucket_name, Key=timestamp_s3_key)
        last_timestamp = response['Body'].read().decode('utf-8')
        return datetime.fromisoformat(last_timestamp)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return None # If no timestamp, then this is first export
        else:
            print("Error fetching the last timestamp")

def set_last_timestamp(table,timestamp,bucket_name):
    timestamp_s3_key=get_timestamp(table)
    try:
        s3.put_object(Bucket=bucket_name, Key=timestamp_s3_key, Body=timestamp.isoformat())
    except Exception as e:
        print("Error in setting the last timestamp")


def export_dynamodb(table_name,bucket_name,region):
    bucket_name=create_s3(bucket_name,region)
    table = dynamodb.Table(table_name)
    try:
        last_export = get_last_timestamp(table_name,bucket_name)
        filter_expression = ''
        expression_values = {}
        print("last export",last_export)
        if last_export:
            filter_expression = 'attribute_not_exists(LastModified) OR LastModified > :last_export'
            expression_values = {':last_export': last_export.isoformat()}
            response = table.scan(FilterExpression=filter_expression , ExpressionAttributeValues=expression_values)
            print("has last_export")
        response = table.scan()
        data = response['Items']
        print("RESPONSE",response)
        print("DATA",data)
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'],
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values)
            data.extend(response['Items'])
        json_data = json.dumps(convert_decimals(data), indent=4)
        s3_data_key = f'{table_name}/{table_name}-export.json'

        s3.put_object(
            Bucket=bucket_name,
            Key=s3_data_key,
            Body=json_data
        )
        print(f"Successfully exported data from DynamoDB table '{table_name}' to S3 bucket '{bucket_name}/{s3_data_key}'.")
        set_last_timestamp(table_name, datetime.utcnow(),bucket_name)

    except Exception as e:
        print(f"An error occurred during export for table '{table_name}': {str(e)}")

#-------------------------------------------------------------------------------------#
# From S3 to Dynamodb

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')



s3 = boto3.client('s3')
def download_json(bucket_name, s3_data_key, file_path):

    try:
        print("filename",file_path)
        s3.head_object(Bucket=bucket_name, Key=s3_data_key)
        s3.download_file(bucket_name, s3_data_key, file_path)
        print("Successfully downloaded from the bucket.")
        return True
    except ClientError as e:
        print(f"Error downloading file from S3: {e}")
        return False


def upload_json(table_name, file_path):
    table = dynamodb.Table(table_name)
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        items = [convert_float_to_decimal(item) for item in data]
        with table.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)
                    print("batch",batch)
        print("Successfully uploaded data to DynamoDB table")
    except Exception as e:
        print(f"Error uploading data to DynamoDB: {e}")

def import_s3_to_dynamodb(bucket_name, s3_data_key, table_name, file_path):
    download = download_json(bucket_name, s3_data_key, file_path)
    if download:
        upload_json(table_name, file_path)


