def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": "Hello from Lambda!",
        "success":True
    }
d=lambda_handler("event","context")
print(d)