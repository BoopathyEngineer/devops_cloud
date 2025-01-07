from datetime import datetime,timedelta
from settings.aws_service import dynamodb
from notification.signal import key_expire,key_expired
from notification.dispatcher import Signal
from settings.env import get_env_vars
from settings.constants import CLIENT, COGNITO, USERTABLE
from settings.configuration import DEVCLIENT_TABLE
from typing import Dict, Optional
from rough import *
from settings.validation import update_access_count
from products.api_products import date_exceed_checking
from boto3.dynamodb.conditions import Key, Attr
from amazonservice.dynamodb import scan_item
notify=Signal()



def scheduler_handler(event,context): 
    # table = dynamodb.Table('client-subscriptions-featureZ24-274')
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table= env_vars.get(USERTABLE,'client-subscriptions-featureZ24-274')
    if 'feature' in table:
        table=DEVCLIENT_TABLE
    items = scan_item(table)
    if not items:
        print("No data found")
    for item in items:
        email = item.get('email')
        api_access_list = item.get('subscriptions', [])
        for api_access in api_access_list:
            api_name = api_access.get('api_name')
            expiry_date = api_access.get("expired_at")
            today_date =  datetime.now()
            value = date_exceed_checking(expiry_date,today_date)
            access_count = api_access.get("access_count")
            if api_name:
                if access_count > 0 and value:
                    update_access_count(email, api_name)
                try:
                    now = datetime.now().date()
                    expire_date = api_access.get('expired_at')
                    try:
                        expire_date = datetime.strptime(expire_date, '%Y-%m-%d %H:%M:%S.%f').date()
                    except ValueError:
                        try:
                            expire_date = datetime.strptime(expire_date, '%Y-%m-%d %H:%M:%S').date()
                        except ValueError:
                            raise ValueError("Date format not recognized")
                    notify_date=now-expire_date
                    if now == expire_date+timedelta(days=1):
                        key_expired(email)
                        print("Notification send for key expired")
                    elif notify_date == timedelta(days=7): 
                        key_expire(email)  
                        print("Notification sent for key expire within a week")
                except Exception as e:
                    print(f"Error': {e}")
            else:
                print(f"Missing api_name")

