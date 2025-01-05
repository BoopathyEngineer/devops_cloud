#!/bin/bash

# Variables
FUNCTION_NAME="myLambdaFunction"
API_NAME="myApi"
ROLE_ARN="arn:aws:iam::your_account_id:role/your_lambda_role"
API_GATEWAY_ID="your_api_gateway_id"
ZIP_FILE="lambda_function.zip"

# Package Lambda function
zip -r $ZIP_FILE lambda_function.py

# Create Lambda function
aws lambda create-function \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://$ZIP_FILE \
  --handler lambda_function.lambda_handler \
  --runtime python3.8 \
  --role $ROLE_ARN

# Create API Gateway
API_ID=$(aws apigateway create-rest-api --name $API_NAME --query 'id' --output text)

# Create resources and methods in API Gateway
RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $API_GATEWAY_ID --path-part "hello" --query 'id' --output text)
aws apigateway put-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method GET --authorization-type NONE
aws apigateway put-integration --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method GET --integration-http-method POST --type AWS_PROXY --uri arn:aws:apigateway:REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:REGION:ACCOUNT_ID:function:$FUNCTION_NAME/invocations

# Grant API Gateway permissions to invoke Lambda
aws lambda add-permission --function-name $FUNCTION_NAME --principal apigateway.amazonaws.com --statement-id $(date +%s) --action lambda:InvokeFunction --source-arn arn:aws:execute-api:REGION:ACCOUNT_ID:$API_ID/*/GET/hello

# Deploy the API
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod
