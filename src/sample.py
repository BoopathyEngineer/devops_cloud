import time
from typing import Dict, Optional
import stripe
from amazonservice.secert import get_secret, store_secret, update_secret
from settings.configuration import DEVCLIENT_TABLE
from settings.constants import USERTABLE
from settings.env import get_env_vars
from subscriptions.views import ZitaPlan
from subscriptions.stripe_service import StripeKeys,Session
from amazonservice.dynamodb import create_backup,restore_backup,restore_existing_backup
import json


####: STRIPE KEY UPDATIONS
# with open('src/schema/secert.json', 'r') as file:
#     config = json.load(file)

# updated_secret_data = json.dumps(config['feature'])
# print("updated_secret_data",type(updated_secret_data))
# update_res = update_secret('feature', updated_secret_data)
# print("update_res",update_res)
# respon = get_secret('feature')
# print("respon--->",respon)


###: STRIPE KEY
str_key = 'prod_Qq9bgoja0rmk0x'
details = StripeKeys.get_stripekey_details(str_key)
stripe_price = StripeKeys.stripekey_list(str_key)




##: BACKUP
# backup = create_backup('zitaconfig-staging','zitaconfig-dev')
# print("backup",backup)

# arn = 'arn:aws:dynamodb:us-east-1:325442430825:table/zitaconfig-staging/backup/01724758164510-ff682cdb'
# get_backup = restore_backup(arn,'zitaconfig-dev')
# print("get_backup",get_backup)

# restore_exist = restore_existing_backup('api-dev','api-feature398')
# print("restore_exist",restore_exist)

#----------------------------------------------------#
# Dynamodb to S3

# table_name = 'zitaconfig-dev'
# table_name='api-dev'
# table_name='client-purchase-dev'
# table_name='client-subscriptions-dev'
# table_name='invoice-dev'
# table_name='notification-dev'
# bucket_name = 'standalone-dev'
# region = 'us-east-1' 
# export_dynamodb(table_name,bucket_name,region)

#----------------------------------------------------#
# S3 to dynamodb

# table_name = 'notification-s3-dev'
# bucket_name = 'standalone-dev'
# s3_data_key = 'notification-dev/notification-dev-export.json'
# file_path = 'C:/Users/hp/Documents/S3_Dynamo/notification-dev.json'  
# import_s3_to_dynamodb(bucket_name, s3_data_key, table_name, file_path)