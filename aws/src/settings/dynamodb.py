import boto3
from configure import REGION
from env import get_env_vars
from typing import Dict, Optional

# Initialize a session using Amazon DynamoDB
dynamodb = boto3.resource("dynamodb", region_name=REGION)

"""
Inserting Values into DynamoDB
"""


def put_item(table_name, item):
    table = dynamodb.Table(table_name)
    if isinstance(item, dict):
        response = table.put_item(Item=item)
        return response


"""
Retrieving Values from DynamoDB
"""


def get_item(table_name, key):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table = dynamodb.Table(table_name)
    if isinstance(key, dict):
        response = table.get_item(Key=key)
        item = response.get("Item")
        return item


"""
Updating an Item in DynamoDB
"""


def update_item(table_name, key, expression, expression_values, expression_names):
    # env_vars: Dict[str, Optional[str]] = get_env_vars()
    table = dynamodb.Table(table_name)
    response = table.update_item(
        Key=key,
        UpdateExpression=expression,
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values,
        ReturnValues="UPDATED_NEW",
    )
    return response


"""
Deleting an Item from DynamoDB
"""


def delete_item(table_name, key):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table = dynamodb.Table(table_name)
    response = table.delete_item(Key=key)
    return response


"""
Scan Item in the Table
"""


def scan_item(table_name):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table = dynamodb.Table(table_name)
    response = table.scan()
    items = response["Items"]
    return items
