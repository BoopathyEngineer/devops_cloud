def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": "Hello from Lambda!"
    }
d=lambda_handler("event","context")
print(d)