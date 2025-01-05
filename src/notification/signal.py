import boto3
from notification.dispatcher import Signal
from settings.aws_service import dynamodb
from datetime import datetime,timedelta
from boto3.dynamodb.conditions import Key
from settings.constants import  NOTIFICATIONTABLE,USERTABLE
from settings.env import get_env_vars
from typing import Dict, Optional
from amazonservice.dynamodb import put_item,update_item,query_item
from settings.configuration import DEVCLIENT_TABLE, DEVNOTIFICATION_TABLE
import json

notify=Signal()
# def put_item(table, item):
#         table.put_item(Item=item)


def save_notification_to_db(signal, **named):
    recipient = named.get('recipient')
    verb = named.get('verb')
    action = named.get('action')
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f') 
    item = {
        'email': recipient,
        'notification': action,  
        'is_active': True,
        'is_read': False,
        'message': verb,
        'timestamp': today
    }
    # dynamodb = boto3.resource('dynamodb')
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table= env_vars.get(NOTIFICATIONTABLE,'notification-featureZ24-274')
    if 'feature' in table:
        table= DEVNOTIFICATION_TABLE 
    # table = dynamodb.Table('notification-featureZ24-274')
    put_item(table,item)   
    print(f"Notification saved to DB: {item}")
notify.connect(save_notification_to_db)
    

def key_expire(email):
    # data = "Notice: Your API  is expiring soon. Please renew to continue using the API."
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table= env_vars.get(USERTABLE ,'client-subscriptions-featureZ24-274')
    if 'feature' in table:
        table= DEVCLIENT_TABLE 
    items = query_item(
        table=table,
        key='email',
        value=email
    )
    if not items:
        print("No data found")
        return
    for item in items:
        email = item.get('email')
        api_access_list = item.get('subscriptions', [])
        for api_access in api_access_list:
            api_name = api_access.get('api_name')
            expire_date = api_access.get('expired_at')
            name=api_access.get('name')
            # expire_date = "2024-08-10 16:30:22.619270"
            data = f"Notice: Your { name} API is expiring soon. Please renew to continue using the API."
            if api_name and expire_date:
                try:
                    today = datetime.now()
                    try:
                        expire_date = datetime.strptime(expire_date, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        try:
                            expire_date = datetime.strptime(expire_date, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            raise ValueError("Date format not recognized")
                    notify_date= abs(today.date()-expire_date.date())
                    if notify_date == timedelta(days=7):
                        id= get_next_notification_id(email)
                        notify.send(
                            recipient=email,
                            description='API key will Expire',
                            verb=data,
                            action=id
                        )
                        print(f"Notification sent to {email} for API '{api_name}' expiring within a week")
                except Exception as e:
                    print(f"Error': {e}")
            else:
                print(f"Missing 'api_name' or 'expired_at' in item: {api_access}")


def get_next_notification_id(email):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table= env_vars.get(NOTIFICATIONTABLE,'notification-featureZ24-274')
    if 'feature' in table:
        table = DEVNOTIFICATION_TABLE
    items = query_item(
        table=table,
        key='email',
        value=email
    )
    total_items = len(items)-1
    new_id = total_items + 1 
    return new_id


def key_expired(email):
    # data = "Your API key has expired. Please renew your subscription."
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table= env_vars.get(USERTABLE,'client-subscriptions-featureZ24-274')
    if 'feature' in table:
        table=DEVCLIENT_TABLE 
    items = query_item(
        table=table,
        key='email',
        value=email
    )
    if not items:
        print("No data found")
        return
    for item in items:
        email = item.get('email')
        api_access_list = item.get('subscriptions', [])
        for api_access in api_access_list:
            api_name = api_access.get('api_name')
            expire_date = api_access.get('expired_at')
            name=api_access.get('name')
            # expire_date = "2024-08-10 16:30:22.619270"
            data = f"Your {name} API  has expired. Please renew your subscription."
            if api_name and expire_date:
                try:
                    today = datetime.now().date()
                    try:
                        expire_date = datetime.strptime(expire_date, '%Y-%m-%d %H:%M:%S.%f').date()
                    except ValueError:
                        try:
                            expire_date = datetime.strptime(expire_date, '%Y-%m-%d %H:%M:%S').date()
                        except ValueError:
                            raise ValueError("Date format not recognized")
                    if today == expire_date+timedelta(days=1):
                        id= get_next_notification_id(email)
                        notify.send(
                            recipient=email,
                            description='API key will Expire',
                            verb=data,
                            action=id
                        )
                        print(f"Notification sent to {email} for API '{api_name}' expired")
                except Exception as e:
                    print(f"Error': {e}")
            else:
                print(f"Missing 'api_name' or 'expired_at' in item: {api_access}")



def get_notification(event: Dict, user: str, email: str, username: str) -> Dict:
    try:
        if event.get('queryparams'):
            queryparams = event.get('queryparams')
            notification_id = queryparams.get('notification')
            markas = queryparams.get('mark_as_read')
            if markas =='True' or markas == True:
                mark_as_read(email,notification_id,markas)
            if notification_id:
                notification_id=json.loads(notification_id)
                mark_as_read(email,notification_id,markas)
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        table= env_vars.get(NOTIFICATIONTABLE,'notification-featureZ24-274')
        if 'feature' in table:
             table = DEVNOTIFICATION_TABLE
        FilterExpression=Key('is_active').eq(True)
        total_notification = query_item(table,'email',email,expression=FilterExpression)

        unread= FilterExpression=Key('is_read').eq(False) & Key('is_active').eq(True) 
        notifications= query_item(table,'email',email,expression=unread)

        now = datetime.now()
        today= datetime.combine(now.date(), datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
        yesterday= datetime.combine(now.date() - timedelta(days=1), datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
        next= datetime.combine(now.date() + timedelta(days=1), datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')

   
        today_filter_exp = Key('timestamp').between(today, next) & Key('is_active').eq(True)
        today_notify= query_item(
            table=table,
            key='email',
            value=email,
            expression=today_filter_exp
        )

        yest_filter_exp=Key('timestamp').between(yesterday,today) & Key('is_active').eq(True)
        yest_notify =  query_item(
            table=table,
            key='email',
            value=email,
            expression=yest_filter_exp
        )
      
        old_filter_exp=Key('timestamp').lt(yesterday) & Key('is_active').eq(True)
        old_notify =query_item(
            table=table,
            key='email',
            value=email,
            expression=old_filter_exp
        )
       
        total_unread = len(notifications)
    
        total=len(total_notification)
        data = {
            'statusCode':200,
            'success': True,
            'today': today_notify,
            'yesterday': yest_notify,
            'others': old_notify,
            'total_unread': total_unread,
            'total':total
        }
        # for d in data['today']:
        #     d['notification'] = int(d['notification'])
        # for d in data['yesterday']:
        #     d['notification'] = int(d['notification'])
        # for d in data['others']:
        #     d['notification'] = int(d['notification'])
        return  data
    except Exception as e:
        print(f"Error in fetching notifications: {e}")
        return { 'statusCode': 500,'success': False, 'error': str(e)} 
 


def mark_as_read(email,n_id=None,markas=None):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table= env_vars.get(NOTIFICATIONTABLE,'notification-featureZ24-274')
    if 'feature' in table:
         table = DEVNOTIFICATION_TABLE 
    unread=Key('is_read').eq(False) & Key('is_active').eq(True)
    unread_notifications =  query_item(table,'email',email,expression=unread)
    if isinstance(n_id,list):
        for notification in unread_notifications:
            notification_id = notification.get('notification')
            if notification_id in  n_id:  
                key = {
                    'email': email,
                    'notification': notification_id  
                }
                update_expression = "SET #is_read = :r"
                update_values = {
                ':r': True }
                update_attribute= {
                    '#is_read': 'is_read'}
                response = update_item(
                    table,
                    key,
                    update_expression,
                    update_values,
                    update_attribute
                )
                print("Notification has been marked as read.")
    elif n_id is None or markas is True:
        unread=Key('is_read').eq(False) & Key('is_active').eq(True)
        unread_notifications = query_item(table,'email',email,expression=unread)
        for notification in unread_notifications:
            key = {
                'email': email,
                'notification': notification['notification']  
            }
            update_expression = "SET #is_read = :r"
            update_values = {':r': True}
            update_attribute = {
                    '#is_read': 'is_read'}

            response = update_item(
                table,
                key,
                update_expression,
                update_values,
                update_attribute
            )
        print("All notification marked as read")
    else:
        print("Invalid Id")



def credit_usage(user_email):
    # data = "You have used all your API credits. Please purchase additional credits."
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    table= env_vars.get(USERTABLE,'client-subscriptions-featureZ24-274')
    if 'feature' in table:
        table=DEVCLIENT_TABLE 
    items = query_item(
        table=table,
        key='email',
        value=user_email
    )
    print("ITEMS",items)
    if not items:
        print("No data found")
    for item in items:
        email = item.get('email')
        api_access_list = item.get('subscriptions', [])
        for api_access in api_access_list:
            api_name = api_access.get('api_name')
            access_count = api_access.get('access_count')
            name=api_access.get('name')
            data = f"Your API credits for {name} has been exhausted. Please purchase additional credits."
            if api_name:
                try:
                    if access_count == 0:
                        id= get_next_notification_id(email)
                        notify.send(
                            recipient=email,
                            description='Access',
                            verb=data,
                            action=id
                        )
                        print(f"Notification sent to notify access count used")
                except Exception as e:
                    print(f"Error': {e}")
            else:
                print(f"Missing api_name")


