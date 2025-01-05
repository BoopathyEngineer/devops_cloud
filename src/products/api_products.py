from typing import Dict, Optional
from boto3.dynamodb.conditions import Key, Attr
from settings.constants import APIGATEWAY, CONFIGTABLE, INVOICETABLE, USERTABLE,CLIENTPURCHASETABLE
from settings.env import get_env_vars
from amazonservice.dynamodb import convert_float_to_decimal, get_item, put_item, query_item, scan_item
from settings.configuration import DEVCLIENT_TABLE, DEVCONFIG_TABLE, DEVINVOICE_TABLE,DEVPURCHASE_TABLE
from datetime import datetime, timedelta
from amazonservice.gateway import get_api_base_url

def get_api_products(event: Dict, user: str, email: str, username: str) -> Dict:
    obj = {}
    data = []
    try:
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        configtable = env_vars.get(CONFIGTABLE,'zitaconfig-featureZ24-277')
        usertable = env_vars.get(USERTABLE,'client-subscriptions-featureZ24-277')
        purchasetable = env_vars.get(CLIENTPURCHASETABLE,'client-purchase-feature309')
        if 'feature' in configtable:
            configtable = DEVCONFIG_TABLE
        if 'feature' in usertable:
            usertable = DEVCLIENT_TABLE
        if 'feature' in purchasetable:
            purchasetable = DEVPURCHASE_TABLE
        queryparams = None
        userkey = {'email':email}
        user_data = get_item(usertable,userkey)
        expression=None
        purchase_data = query_item(purchasetable,'email',email,expression=expression)
        if len(purchase_data) == 0 and user_data:
            client_purchase_table_updation(email,user_data)
            purchase_data = query_item(purchasetable,'email',email,expression=expression)
        purchased_api = []
        if user_data:
            user_data = user_data.get('subscriptions')
            purchased_api = [item.get('api_name','') for item in user_data]
        if event.get('queryparams'):
            queryparams = event.get('queryparams')
            apiname = queryparams.get('api_name')
            if apiname:
                key = {'api_name':apiname}
                data = get_item(configtable,key)
            else:
                data = scan_item(configtable,expression=expression)
        else:
            data = scan_item(configtable,expression=expression)
        if isinstance(data,dict):
            new_data = []
            new_data.append(data)
            data = new_data
        removed_api  = []
        if isinstance(data,list):
            for i in data:
                if i.get('api_name') in purchased_api and i.get('api_name'):
                    ##### GET Purchased API of Details Has been in Purchase Table
                    expired_api = True
                    purchase_item = next((item for item in purchase_data if item['api_name'] == i.get('api_name')), None)
                    if purchase_item and purchase_item.get('Active'):
                        if user_data:
                            ##### Extract the API Details If the User Plan has been purchased If Expired It Will Shown The Config Table
                            expired_api = next((item for item in user_data if item['api_name'] == i.get('api_name')), None)
                            if expired_api:
                                expired_api = date_exceed_checking(expired_api['expired_at'],datetime.now())         
                        if purchase_item and expired_api == False:
                            ##### Here Will Replace the Purchase Table Obj
                            i.update(purchase_item)
                    else:
                        removed_api.append(i.get('api_name'))
                ###### Handling The Colour & Expired Date 
                billing_id = billing_invoie_number(email,i.get('api_name'))
                i['billing_no'] = billing_id
                i['colour'] = 'grey'
                i['validation'] = None
                user_item = {}
                if user_data:
                    user_item = next((item for item in user_data if item['api_name'] == i.get('api_name')), None)
                if user_item:
                    colour,colour_date = handle_expired_date(user_item)
                    i['colour'] = colour
                    i['validation'] = colour_date
            #### Removed User Cancelled Or InActive API
            data = [api for api in data if api.get('api_name') not in removed_api]
            obj["response"] = data
            obj["statusCode"] = 200
            obj["success"] = True
    except Exception as e:
        obj["error"] = str(e)
        obj["statusCode"] = 400
    return obj
        

##: Here its Documentation API
def get_api_documentation(event: Dict, user: str, email: str, username: str) -> Dict:
    obj = {}
    try:
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        configtable = env_vars.get(CONFIGTABLE,'zitaconfig-featureZ24-277')
        gateway_id = env_vars.get(APIGATEWAY,None)
        access_url = get_api_base_url(gateway_id)
        if 'feature' in configtable:
            configtable = DEVCONFIG_TABLE
        expression=Attr('Active').eq(True)
        data = scan_item(configtable,expression=expression)
        response_data = []
        for i in data:
            if isinstance(i,dict):
                api_obj = {'name':i.get('name'),'description':i.get('description'),'url':i.get('url')}
                response_data.append(api_obj)
        obj['url'] = access_url
        obj["response"] = response_data
        obj["statusCode"] = 200
        obj["success"] = True
    except Exception as e:
        obj["error"] = str(e)
        obj["statusCode"] = 400
    return obj
        



def handle_expired_date(obj : Dict):
    color = 'grey'
    color_date = None
    if isinstance(obj,dict):
        current_time = datetime.now()
        if obj.get('expired_at'):
            date1 = obj.get('expired_at')
            isValid = date_exceed_checking(date1,current_time)
            if isValid:
                color = 'red'
                color_date = handle_dateFormat(obj.get('expired_at'))
            else:
                yet_to_exipre = one_week_checking(date1,7)
                yet_to_exipre_valid = equal_date_checking(yet_to_exipre,current_time)
                if yet_to_exipre_valid:
                    color = 'yellow'
                    color_date = handle_dateFormat(obj.get('expired_at'))
                elif obj.get('purchased_at'):
                    color = 'green'
                    color_date = handle_dateFormat(obj.get('purchased_at'))
    return color,color_date


def handle_dateFormat(date_str):
    if date_str != 'Product Duration' and date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
        except:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        formatted_date = date_obj.strftime('%d-%m-%Y')
        return formatted_date
    return None


def date_exceed_checking(date1_str, date2_str):
    if date1_str != 'Product Duration' and date1_str:
        date1 = datetime.fromisoformat(str(date1_str))
        date2 = datetime.fromisoformat(str(date2_str))
        # Compare the dates
        if date2 > date1:
            return True
        elif date2 == date1:
            return True
        else:
            return False

def equal_date_checking(date1_str, date2_str):
    if date1_str != 'Product Duration' and date1_str:
        date1 = datetime.fromisoformat(str(date1_str))
        date2 = datetime.fromisoformat(str(date2_str))
        ## Compare the dates
        if date2.date() > date1.date():
            return True
        elif date2.date() == date1.date():
            return True
        else:
            return False
    
def one_week_checking(date, days):
    if date != 'Product Duration' and date:
        date = datetime.fromisoformat(str(date))
        next_week = date - timedelta(days=int(days))
        return next_week


def billing_invoie_number(email,api_name):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    invoicetable = env_vars.get(INVOICETABLE,'zitaconfig-featureZ24-277')
    if 'feature' in invoicetable:
        invoicetable = DEVINVOICE_TABLE
    invoice_id = None
    if api_name and email:
        expression=Attr('api_name').eq(api_name) & Attr('type').eq('API service')
        key = 'email'
        response = query_item(invoicetable,key,email,expression=expression)
        if response:
            last_item = response[-1]
            invoice_id = last_item.get('invoice', None)
    return invoice_id


def client_purchase_table_updation(email,data):
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    purchasetable = env_vars.get(CLIENTPURCHASETABLE,'client-purchase-feature309')
    configtable = env_vars.get(CONFIGTABLE,'zitaconfig-featureZ24-277')
    usertable = env_vars.get(USERTABLE,'client-subscriptions-featureZ24-277')
    if 'feature' in configtable:
        configtable = DEVCONFIG_TABLE
    if 'feature' in usertable:
        usertable = DEVCLIENT_TABLE
    if 'feature' in purchasetable:
        purchasetable = DEVPURCHASE_TABLE
    if email and data:
        if isinstance(data,dict):
            subscriptions = data.get('subscriptions')
            purchased_api = [item.get('api_name','') for item in subscriptions]
            for i in purchased_api:
                api_name  = {'api_name':i}
                api_details = get_item(configtable,api_name)
                if api_details:
                    api_details = convert_float_to_decimal(api_details)
                    api_details['email'] = email
                    put_api_details = put_item(purchasetable,api_details)
    return None
    