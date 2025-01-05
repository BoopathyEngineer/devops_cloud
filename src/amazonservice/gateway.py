from settings.aws_service import gateway

# Your API key ID
api_key = '8fdg1o6clf'

def get_apikey(api_key):
    try:
        response = gateway.get_api_key(apiKey=api_key, includeValue=True)
    except Exception as e:
        response = None
    name = None
    if isinstance(response,dict):
        name = response['name']
        response = response['value']
    return response,name


def create_apikey(sub,usermail):
    # Generate a new API Key
    id = None
    response = gateway.create_api_key(
        name=sub,
        description=usermail,
        enabled=True,
        generateDistinctId=True
    )
    if isinstance(response,dict):
        id = response['id']
        response = response['value']
    return id,response


def get_allapi_keys():
    # Initialize pagination
    paginator = gateway.get_paginator('get_api_keys')
    api_keys = []
    # Retrieve all API keys using pagination
    for page in paginator.paginate():
        api_keys.extend(page['items'])
    
    return api_keys


def delete_apikey(api_id,alllist):
    if api_id in alllist:
        for i in alllist:
            response = gateway.delete_api_key(apiKey=i)
    else:
        response = gateway.delete_api_key(apiKey=api_id)
    return response


def apikey_to_usageplan(apikey, usage_id):
    # Add the API key to the usage plan
    if usage_id:
        response = gateway.create_usage_plan_key(
            keyId=apikey,
            keyType='API_KEY',
            usagePlanId=usage_id
        )
        return response
    return None


def get_all_usage_plans():
    # Initialize pagination
    paginator = gateway.get_paginator('get_usage_plans')
    plans = []
    
    # Collect all usage plans using pagination
    for page in paginator.paginate():
        plans.extend(page['items'])
        
    return plans


def disable_api_key(api_key_id,alllist):
    # Update the API key to set its 'enabled' status to False
    if api_key_id in alllist:
        for i in alllist:
            response = gateway.update_api_key(
                apiKey=i,
                patchOperations=[
                    {
                        'op': 'replace',
                        'path': '/enabled',
                        'value': 'false'
                    }
                ]
            )
    else:
        response = gateway.update_api_key(
                apiKey=api_key_id,
                patchOperations=[
                    {
                        'op': 'replace',
                        'path': '/enabled',
                        'value': 'false'
                    }
                ]
            )
    return response


def get_api_base_url(api_id):
    if api_id:
        stage_name = 'prod'
        paginator = gateway.get_paginator('get_rest_apis')
        api_base_url = None
        for page in paginator.paginate():
            for ids, api in enumerate(page['items']):
                if get_custom_domain_urls(api_id):
                    custom_api_id = get_custom_domain_urls(api_id)
                    api_base_url = f"https://{custom_api_id}/"
                    break
                if api['id'] == api_id:
                    api_base_url = f"https://{api_id}.execute-api.{gateway.meta.region_name}.amazonaws.com/{stage_name}/"
                    break
            if api_base_url:
                break
        return api_base_url
    return None



#: Getting Gateway Custom Url 
def get_custom_domain_urls(api_id):
    # Fetch custom domain names
    response = gateway.get_domain_names()
    
    # Extract and print the custom domain names and their associated APIs
    for item in response['items']:
        domain_name = item['domainName']
        base_path_mappings = gateway.get_base_path_mappings(domainName=domain_name)
        
        for mapping in base_path_mappings['items']:
            rest_api_id = mapping['restApiId']
            if rest_api_id == api_id:
                return domain_name
    return None


