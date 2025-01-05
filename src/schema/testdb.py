# import boto3
# from boto3.dynamodb.conditions import Key

# # Initialize the DynamoDB resource
# dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# def query_items_by_date(table_name, email, date):
#     table = dynamodb.Table(table_name)
#     response = table.query(
#         KeyConditionExpression=Key('email').eq(email) & Key('date').begins_with(date)
#     )
#     items = response.get('Items', [])
#     return items

# # Define the table name, email, and date
# table_name = "userlog-featureassistance"
# email = "pugazhe@gmail.com"
# date = "2024-08-03"  # Date without time

# # Query the items from the table
# data = query_items_by_date(table_name, email, date)

# # Print the retrieved data
# print(data)



import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def query_items_by_date_range(table_name, email, end_date, days_range):
    table = dynamodb.Table(table_name)
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    start_date_obj = end_date_obj - timedelta(days=days_range)
    start_date = start_date_obj.strftime("%Y-%m-%d")
    print("start_date",start_date,end_date)
    
    response = table.query(
        KeyConditionExpression=Key('email').eq(email) & Key('date').between(start_date, end_date),
        
    )
    items = response.get('Items', [])
    return items

## Define the table name, email, and date
table_name = "notification-featureZ24-274"
email = "pugazhe@gmail.com"
date_prefix = "2024-08-04T00:00:00"  # End date without time
days_range = 7  # Number of days before the end date

# Query the items from the table
# data = query_items_by_date_range(table_name, email, end_date, days_range)
table = dynamodb.Table(table_name)
response = table.query(
    KeyConditionExpression='PartitionKeyName = :email',
    FilterExpression='NumericAttributeName >= :timestamp',
    ExpressionAttributeValues={
        ':email': email,  # Change this to the specific partition key value you're querying
        ':gte_val': date_prefix  # Example GTE condition value
    }
)

# Print the retrieved data
print(response)




import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Specify your DynamoDB table
table = dynamodb.Table('notification-featureZ24-274')

# Define the target date for filtering
target_date_str = "2024-08-06"
target_date = datetime.strptime(target_date_str, "%Y-%m-%d")

# Convert target date to string if necessary, depending on how dates are stored in your table
target_date_str = target_date.strftime('%Y-%m-%d')

# Perform a scan operation with a filter for dates greater than the target date
response = table.query(
    KeyConditionExpression=Key('email').eq('pugazhe@gmail.com'),
    FilterExpression=Attr('timestamp').gt(target_date_str)
)

items = response['Items']

# Print out the filtered items
for item in items:
    print(item)
