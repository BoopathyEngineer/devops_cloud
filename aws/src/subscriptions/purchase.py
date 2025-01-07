
from decimal import Decimal
from typing import Dict, Optional
from settings.configuration import DEVCLIENT_TABLE, DEVCONFIG_TABLE, SUBSCRIPTION_TABLE
from amazonservice.dynamodb import get_item, put_item, query_item, scan_item, update_item
from settings.constants import CONFIGTABLE, USERTABLE
from settings.env import get_env_vars
from datetime import datetime, timedelta
from subscriptions.views import ZitaPlan


'''
Inserting the values in Subscription Tables
'''
def Buy_Subscription(event: Dict, user: str, email: str, username: str) -> Dict:
    obj = {}
    statusCode = 400
    try:
        if event.get('queryparams'):
            queryparams = event.get('queryparams')
            if queryparams:
                plan = queryparams.get('plan')
                api_name = queryparams.get('api_name')
                env_vars :  Dict[str, Optional[str]] = get_env_vars()
                configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-featureZ24-274')
                usertable = env_vars.get(USERTABLE, 'client-subscriptions-featureZ24-274')
                if 'feature' in configtable:
                    configtable = DEVCONFIG_TABLE
                if 'feature' in usertable:
                    usertable = DEVCLIENT_TABLE
                if plan == None:
                    raise Exception('give me plan in queryparams')
                if api_name == None:
                    raise Exception('give me api_name in queryparams')
                if plan and api_name:
                    key = {'api_name':api_name}
                    userkey = {'email':email}
                    api_obj = get_item(configtable,key)
                    user_data = get_item(usertable,userkey)
                    if api_obj:
                        if isinstance(api_obj,dict):
                            if api_obj.get(plan):
                                plan_details = api_obj[plan]
                                if isinstance(plan_details,dict):
                                    feature_count = plan_details.get('credits')
                                    purchased_apiname_convertion = ZitaPlan.NameConvertion(api_name)
                                    if user_data:
                                        if user_data.get('subscriptions'):
                                            subscription_data = user_data.get('subscriptions',[])
                                            avail_api = [item.get('api_name','') for item in subscription_data]
                                            if isinstance(subscription_data,list):
                                                for i in subscription_data:
                                                    if api_name == i.get('api_name'):
                                                        i['access_count'] = i['access_count'] + feature_count
                                                        if plan == 'addon':
                                                            i['addon_count'] = feature_count
                                                        else:
                                                            i['feature_count'] = feature_count
                                                if api_name not in avail_api:
                                                    start_date = datetime.now()
                                                    end_date = start_date + timedelta(days=30)
                                                    feat_count = 0 
                                                    addon_count = 0 
                                                    purchased_apiname_convertion = ZitaPlan.NameConvertion(api_name)
                                                    if plan == 'addon':
                                                        addon_count = feature_count
                                                    else:
                                                        feat_count = feature_count
                                                    newobj = {'api_name':api_name,'access_count':feature_count,'feature_count':feat_count,'addon_count':addon_count,'purchased_at':str(start_date),'expired_at':str(end_date),'name':purchased_apiname_convertion,'sub_id':None,'invoice_id': None}
                                                    subscription_data.append(newobj)
                                    else:
                                        subscription_data = []
                                        start_date = datetime.now()
                                        end_date = start_date + timedelta(days=30)
                                        feat_count = 0 
                                        addon_count = 0 
                                        purchased_apiname_convertion = ZitaPlan.NameConvertion(api_name)
                                        if plan == 'addon':
                                            addon_count = feature_count
                                        else:
                                            feat_count = feature_count
                                        newobj = {'api_name':api_name,'access_count':feature_count,'feature_count':feat_count,'addon_count':addon_count,'purchased_at':str(start_date),'expired_at':str(end_date),'name':purchased_apiname_convertion,'sub_id':None,'invoice_id': None}
                                        subscription_data.append(newobj)

                                update_expression = 'SET #plan = :plan_obj'
                                attribute_names = {'#plan':'subscriptions'}
                                attribute_values = {':plan_obj':subscription_data}
                                table_updation = update_item(usertable,userkey,update_expression,attribute_values,attribute_names)    
                                obj['message'] = f'{purchased_apiname_convertion} API Purchased SuccessFully'
                                statusCode = 200
                                obj['success'] = True
                            else:
                                raise Exception('Plan Doesnot Exists')
                    else:
                        raise Exception('API is Not Found')   
    except Exception as e:
        obj['error'] = str(e)
    obj['statusCode'] = statusCode
    return obj



def user_details(email: str) -> Dict:
    obj = {}
    statusCode = 400
    try:
        env_vars :  Dict[str, Optional[str]] = get_env_vars()
        configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-featureZ24-274')
        usertable = env_vars.get(USERTABLE, 'client-subscriptions-featureZ24-274')
        if 'feature' in configtable:
            configtable = DEVCONFIG_TABLE
        if 'feature' in usertable:
            usertable = DEVCLIENT_TABLE
        data = scan_item(configtable)
        purchase_counts = {i.get('api_name'): 0 for i in data}   
        user_key = {'email':email}
        client_data = get_item(usertable,user_key)
        if client_data:
            subscription = client_data.get('subscriptions',[])
            for i in subscription:
                if i.get('api_name'):
                    api_name = i.get('api_name')
                    access_count = i.get('access_count')
                    if isinstance(purchase_counts.get(api_name),int):
                        purchase_counts[api_name] = access_count
        obj['success'] = True
        statusCode = 200
        obj["response"] = purchase_counts
    except Exception as e:
        obj['error'] = str(e)
    obj['statusCode'] = statusCode
    return obj
