from ast import Dict
from typing import Optional
from amazonservice.dynamodb import get_item, query_item, querysort_betweendates, querysort_item,scan_item
from settings.aws_service import dynamodb
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
from helper import extract_date
from amazonservice.download import csv_download, csv_upload_to_s3_direct
from settings.env import get_env_vars
from settings.constants import BUCKETNAME, USERTABLE,CONFIGTABLE,APITABLE,INVOICETABLE
from settings.configuration import DEV_S3BUCKET, DEVAPI_TABLE, DEVCLIENT_TABLE, DEVINVOICE_TABLE,DEVCONFIG_TABLE
import math
from subscriptions.views import ZitaPlan
from datetime import datetime


''' Here its a Analysis API Function '''
def get_analytics(event: Dict, user: str, email: str, username: str) -> Dict:
    obj={}
    from_dates = None
    to_dates = None
    try:
        api_name = None
        from_dates = None
        to_dates = None
        from_purchased_date = None
        to_purchased_date = None
        download = False
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        client_sub= env_vars.get(USERTABLE,'client-subscriptions-featureZ24-277')
        AWS_BUCKET_NAME = env_vars.get(BUCKETNAME,'zita-featurez24-297')
        invoice_table = env_vars.get(INVOICETABLE,'invoice-featureZ24-277')
        if 'feature' in client_sub:
            client_sub = DEVCLIENT_TABLE
        if 'feature' in AWS_BUCKET_NAME:
            AWS_BUCKET_NAME = DEV_S3BUCKET
        if 'feature' in invoice_table:
            invoice_table = DEVINVOICE_TABLE
        
        if event.get("queryparams"):
            queryparams = event.get("queryparams")
            if queryparams:
                api_name = queryparams.get("api_name")
                from_dates=queryparams.get("from_date")
                to_dates=queryparams.get("to_date")
                download = queryparams.get('csv_download')
        
        key = {'email':email}
        client_data = get_item(client_sub,key)
        no_of_days = 30
        if api_name:
            client_date_filter = get_item(client_sub,key)
            no_of_days,from_purchased_date,to_purchased_date = date_filter(client_date_filter,api_name)
        days30 = get_purchase(email,30,api_name,from_dates,to_dates)
        dashboard_credits = get_purchase(email,30,api_name,from_purchased_date,to_purchased_date)
        api_logs = days30['analytics']
        subscription = []
        validarray = []
        if isinstance(client_data,dict):
            subscription = client_data.get('subscriptions',[])
        if days30.get('error') == None:
            if api_name:
                obj["total_requests"] = dashboard_credits["total_request"]
                obj["total_credits"]=dashboard_credits["credits"]
                obj["remaining_credits"] = days30["client_sub"]
                obj["error_rate"] = days30["error_rate"]
                obj["purchase_log"]=days30["purchase_log"]
                obj['weekly_api_usage'] = days30["weekly_api_calls"]
                obj['from_purchased_date'] = from_purchased_date
                obj['to_purchased_date'] = to_purchased_date
                obj['no_of_days'] = no_of_days
            if api_name == None:
                for t in subscription:
                    if t.get("api_name"):
                        api_name = t['api_name'] 
                        purchased_from = t.get('purchased_at')
                        purchased_to = t.get('expired_at')
                        total_days,from_purchased_date,to_purchased_date =  analytics_filter(purchased_from,purchased_to)
                        individual_api = get_purchase(email,30,api_name,from_purchased_date,to_purchased_date)
                        individual_api = individual_api.get('analytics')
                        if individual_api:
                            update_obj = individual_api.get(t['api_name'])
                            if update_obj.get('requests') != 0:
                                api_err_rate = update_obj.get('error_rate')
                                t['no_of_request'] = update_obj.get('requests')
                                t['credits_consumed'] = credits_calculation(update_obj.get('credits'))
                                t['remaining_credits']= t.get('access_count')
                                t['error_rate'] = api_err_rate
                                t['is_download'] = True
                        else:
                            t['no_of_request'] = api_logs.get(t['api_name'],0)
                            t['credits_consumed'] = api_logs.get(t['api_name'],0)
                            t['remaining_credits']= t.get('access_count')
                            t['error_rate'] =  api_logs.get(t['api_name'],0)
                            t['is_download'] = False
                        validarray.append(t['is_download'])
        
        print("validarray",validarray,any(validarray))
        if not any(validarray):
            subscription = []
        obj['response'] = subscription
        obj['success']=True
        obj['statusCode'] = 200
        if download == 'true':
            download_list = transform_data(days30["download_obj"], email,days30["client_sub"])
            if api_name:
                api_name = ZitaPlan.NameConvertion(api_name)
            now = datetime.now()
            formatted_date = now.strftime("%d.%m.%Y")
            filename = f"{api_name}_Report_{formatted_date}.csv"
            download_url = csv_upload_to_s3_direct(download_list, AWS_BUCKET_NAME, 'Reports', filename, email = email)
            obj["download_url"] = download_url  
    except Exception as e:
        obj['error'] = str(e)
        obj['statusCode'] = 400
    return obj

#########payment and expired date validate############

def date_filter(client_data,api_name):
    total_days = 0
    payment_date = None
    expired_date = None
    if client_data and client_data.get('subscriptions'):
        subscriptions = client_data.get('subscriptions')
        for i in subscriptions:
            if i.get('api_name') == api_name:
                payment_date = i.get("purchased_at")
                expired_date = i.get("expired_at")
                total_days,payment_date,expired_date =  analytics_filter(payment_date,expired_date)
    return total_days,payment_date,expired_date

            
def analytics_filter(payment_date,expired_date):
    total_days = 0
    if payment_date and expired_date:
        try:
            date_format = "%Y-%m-%d %H:%M:%S.%f"  # Format for the first date
            date1 = datetime.strptime(payment_date, date_format)
        except:
            date_format = "%Y-%m-%d %H:%M:%S"
            date1 = datetime.strptime(payment_date, date_format)
        try:
            date_format = "%Y-%m-%d %H:%M:%S.%f"  # Format for the second date
            date2 = datetime.strptime(expired_date, date_format_2)
        except:
            date_format_2 = "%Y-%m-%d %H:%M:%S"  # Format for the second date
            date2 = datetime.strptime(expired_date, date_format_2)
        payment_date = str(date1.date())
        expired_date = str(date2.date())
        date_difference = date2 - date1
        total_days = date_difference.days
    else:
        purchased_date = None
        expired_date = None
    return total_days,payment_date,expired_date


''' Here its a Reports API Function '''
def get_reports(event: Dict, user: str, email: str, username: str) -> Dict:
    obj = {}
    download= False
    api_name= None
    from_dates = None
    to_dates = None
    resume_parser= None
    comparitive_analysis = None
    jd_generation = None
    jd_parser= None
    matching = None
    profile_summary = None
    interview_questions = None

    try:
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        AWS_BUCKET_NAME = env_vars.get(BUCKETNAME,'zita-featurez24-297')
        configtable = env_vars.get(CONFIGTABLE,'zitaconfig-featureZ24-277')
        api_table= env_vars.get(APITABLE,'api-featureZ24-277')
        if 'feature' in AWS_BUCKET_NAME:
            AWS_BUCKET_NAME = DEV_S3BUCKET
        if 'feature' in configtable:
            configtable = DEVCONFIG_TABLE
        if 'feature' in api_table:
            api_table = DEVAPI_TABLE
                
        current_api = scan_item(configtable)
        current_api = [i.get('api_name') for i in current_api]

        if event.get("queryparams"):
            queryparams = event.get("queryparams")
            if queryparams:
                api_name = queryparams.get("api_name")
                download = queryparams.get("csv_download")
                from_dates=queryparams.get("from_date")
                to_dates=queryparams.get("to_date")

        days30 = get_purchase(email,30,api_name,from_dates,to_dates)
        for specific_api in current_api:
            find_api = get_purchase(email,30,specific_api,from_dates,to_dates)
            if specific_api == 'resume_parser':
                resume_parser = find_api.get("weekly_api_calls")
            if specific_api == 'matching':
                matching = find_api.get("weekly_api_calls")
            if specific_api == 'comparitive_analysis':
                comparitive_analysis = find_api.get("weekly_api_calls")
            if specific_api == 'jd_parser':
                jd_parser = find_api.get("weekly_api_calls")
            if specific_api == 'profile_summary':
                profile_summary = find_api.get("weekly_api_calls")
            if specific_api == 'interview_questions':
                interview_questions = find_api.get("weekly_api_calls")
            if specific_api == 'jd_generation':
                jd_generation = find_api.get("weekly_api_calls")

        ''' Calculate the Overall Request For This User FROm First'''    
        dashboard_credits = get_purchase(email,30,None,None,None)
        filterexpression = None
        credits_filter = query_item(api_table,'email',email,expression=filterexpression)
        no_of_days = credits_filter_first(credits_filter)
        dashboard_credits = get_purchase(email,no_of_days,None,None,None)
        
        if days30.get('error') == None:
            obj["statusCode"] = 200
            obj["error_rate"] = days30["error_rate"]
            obj["purchase_log"]=days30["purchase_log"]
            obj["total_requests"] = dashboard_credits["total_request"]
            obj["total_credits"]=dashboard_credits["credits"]
            obj["remaining_credits"] = days30["client_sub"]
            obj["purchase_data"]=days30["purchase_data"]
            obj['total_errate']=days30["total_errate"]
            obj["success"] = True
            obj['weekly_api_usage'] = days30["weekly_api_calls"]
            ###### Individual API Data #######
            obj['resume_parser'] = resume_parser
            obj['jd_parser'] = jd_parser
            obj['matching'] = matching
            obj['comparitive_analysis'] =comparitive_analysis 
            obj['interview_questions'] =interview_questions
            obj['jd_generation'] = jd_generation
            obj['profile_summary'] = profile_summary
            ##### ############# #######
            obj['from_date ']=from_dates
            obj['to_date']=to_dates
            
            if download == 'true':
                download_list = transform_data(days30["download_obj"],email,days30["client_sub"])
                now = datetime.now()
                formatted_date = now.strftime("%d.%m.%Y")
                filename = f"API_Activity_Report_{formatted_date }.csv"
                download_url = csv_upload_to_s3_direct(download_list,AWS_BUCKET_NAME,'Reports',filename,email = email)
                obj["download_url"]=download_url
        else:
            raise Exception(days30.get('error'))
    except Exception as e:
        obj['error'] = str(e)
    return obj

## Calculate For Total No_OF Days FRom First
def credits_filter_first(data):
    total_days = 0
    if data:
        for i in data:
            if i.get('date'):
                first_request_date = i.get("date")
                total_days =  calculate_days_between(first_request_date)
                break
    else:
        total_days = 30
    return total_days
    
'''Calculate the number of days between two dates.'''
def calculate_days_between(date_str1, date_str2=None):
    # Parse the first date
    try:
        date1 = datetime.strptime(date_str1, "%Y-%m-%d %H:%M:%S.%f").date()
        if date_str2 is None:
            date2 = datetime.now().date()
        else:
            date2 = datetime.strptime(date_str2, "%Y-%m-%d %H:%M:%S.%f").date()
        # Calculate the difference in days
        total_days = (date2 - date1).days
        
        # Ensure a minimum of 30 days
        if total_days < 30:
            total_days = 30
        
        return total_days
    except Exception as e:
        print("Calculate days Between Exceptions:", e)
        return 30
    


## Here its a Purchase Function  
def get_purchase(email,days,apiname,from_date=None,to_date=None):
    print("============",days,apiname,from_date,to_date)
    obj = {}
    obj["statusCode"] = 200
    try:

        #### TABLE #########
        env_vars: Dict[str, Optional[str]] = get_env_vars()
        client_sub= env_vars.get(USERTABLE,'client-subscriptions-featureZ24-277')
        if 'feature' in client_sub:
            client_sub = DEVCLIENT_TABLE
        invoice_table= env_vars.get(INVOICETABLE,'invoice-featureZ24-277')
        if 'feature' in invoice_table:
            invoice_table = DEVINVOICE_TABLE
        api_table= env_vars.get(APITABLE,'client-subscriptions-featureZ24-277')
        if 'feature' in api_table:
            api_table = DEVAPI_TABLE

        filterexpression = None
        error_data = []
        
        if apiname:
            filterexpression = Attr('api_name').eq(apiname)
        if days and from_date == None and to_date == None:
            sort_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            sort_date = str(sort_date)
            error_data = querysort_item(api_table,'email',email,'date',sort_date,expression=filterexpression)
        if days == 30 and from_date and to_date:
            error_data = querysort_betweendates(api_table,'email',email,'date',from_date,to_date,expression=filterexpression)
        invoice_data = query_item(invoice_table,'email',email,expression=filterexpression)
        for x in invoice_data:
            if x.get('expired_date'):
                x['expired_date'] = extract_date(x['expired_date'])
                x['next_billing_date'] = extract_date(x['next_billing_date'])
        
        key = {"email":email}
        client_sub = get_item(client_sub,key)

        ## GET Purchase Data or API by User
        purchase_data = purchased_data(email,client_sub,invoice_table,api_table)
                    
        result = []
        daily_totals = {}
        Error_data =[]
        credits_count = 0

        # Get today's date
        today = datetime.today()
        # Generate a dictionary for the past 7 days including today
        log_dates = {}
        credits_log = {}
        err_log = {}
        api_logs = {}
        download_obj = [] ##### for CSV
        overall_error_rate = 0

        if from_date and to_date and len(error_data)>0:
            start_date = datetime_convert(from_date)  # Example start date
            end_date = datetime_convert(to_date)   # Example end date
            # Generate dates between start_date and end_date
            log_dates = { (start_date + timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range((end_date - start_date).days + 1) }
            err_log = { (start_date + timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range((end_date - start_date).days + 1) }
            credits_log = { (start_date + timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range((end_date - start_date).days + 1) }
            # download_obj = { (start_date + timedelta(days=i)).strftime("%d-%m-%Y"): {} for i in range((end_date - start_date).days + 1) }
         

        elif days == 30 and len(error_data)>0 and from_date == None and to_date == None:
            log_dates = {(today - timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range(days)}       
            err_log = {(today - timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range(days)}       
            credits_log = {(today - timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range(days)}
            # download_obj = {(today - timedelta(days=i)).strftime("%d-%m-%Y"): {} for i in range(days)}
        
        elif days == 7 and len(error_data)>0 and from_date == None and to_date == None:
            log_dates = {(today - timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range(days)}       
            err_log = {(today - timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range(days)}       
            credits_log = {(today - timedelta(days=i)).strftime("%d-%m-%Y"): 0 for i in range(days)}
            # download_obj = {(today - timedelta(days=i)).strftime("%d-%m-%Y"): {} for i in range(days)}
        
        
        #: Main Calculation About reports
        for entry in error_data:
            request_calls=entry.get('request')
            nameofapi = entry.get('api_name')
            date = datetime.strptime(entry['date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%Y')
            digit = log_dates.get(date)
            status_code = 0
            if isinstance(digit,int):
                log_dates[date] += request_calls
            
            ### Credits Consumed Counts
            if entry['statuscode']!= "200":
                overall_error_rate = overall_error_rate + 1
                status_code = int(entry['statuscode'])
            else:
                credits_count += entry.get('credits')
                if isinstance(credits_log.get(date),int):
                    credits_log[date] += entry.get('credits')
            
            # ### Assign For Api Logs
            if isinstance(api_logs.get(nameofapi),dict):
                api_logs[nameofapi]['requests'] += request_calls
                api_logs[nameofapi]['credits'] += int(entry.get('credits'))
                if entry['statuscode']!= "200":
                    api_logs[nameofapi]['error_rate'] = int(api_logs[nameofapi]['error_rate']) + 1
            else:
                api_logs[nameofapi] = {}
                api_logs[nameofapi]['requests'] = int(request_calls)
                api_logs[nameofapi]['credits'] = int(entry.get('credits'))
                api_logs[nameofapi]['error_rate'] = 0
                if entry['statuscode']!= "200":
                    api_logs[nameofapi]['error_rate'] = 1

            ### Assign For Download Obj
            # if isinstance(download_obj[date].get(nameofapi),dict):
            #     download_obj[date][nameofapi]['requests'] += request_calls
            #     download_obj[date][nameofapi]['credits'] += int(entry.get('credits'))
            # else:
            #     download_obj[date][nameofapi] = {}
            #     download_obj[date][nameofapi]['requests'] = int(request_calls)
            #     download_obj[date][nameofapi]['credits'] = int(entry.get('credits'))
            download_obj.append(entry)
            
            if (date, status_code) not in daily_totals:
                if status_code != 0:
                    daily_totals[(date, status_code)] = 0
            if status_code != 0:
                daily_totals[(date, status_code)] += 1
            

        
        for (date, status_code), total in daily_totals.items():
            result.append([date, status_code, total])
        
        for row in result:
            if row[1] != 0:
                if isinstance(err_log.get(row[0]),int):
                    err_log[row[0]] += int(row[2])
                else:
                    if row[1] != 0:
                        err_log[row[0]] = int(row[2])
            if row[1] != 200:
                dataobj = {'date':row[0],'statuscode':row[1],'Count':row[2]}
                Error_data.append(dataobj)

        remaining_credits = 0
        subscription = []
        if client_sub:
            subscription = client_sub.get('subscriptions')
        if isinstance(subscription,list):
            if apiname:
                for t in subscription:
                    if apiname == t.get('api_name'):
                        remaining_credits = t.get('access_count')
            else:
                for t in subscription:
                    if t.get('access_count'):
                        remaining_credits += t.get('access_count')
        formatted_dates_keys = [datetime.strptime(date, '%d-%m-%Y').strftime('%d/%m') for date in log_dates.keys()]
        ############## ERROR RATE CALCULATION ###############
        t_req = list(log_dates.values())
        e_req = list(err_log.values())
        credits_log = list(credits_log.values())
        credits_log = [credits_calculation(x) for x in credits_log]
        err_rate = [ error_rate_calculation(u,y) for u,y in zip(e_req,t_req)]
        #########################error_rate_calculation
        logs  = {
            'lable':formatted_dates_keys ,
            'day':list(log_dates.values()),
            'api_cals':list(log_dates.values()),
            'error_rate':err_rate,
            'credits_log':credits_log
            }
        obj['success'] = True
        obj['error_rate'] = Error_data
        obj['total_request'] = len(error_data)
        obj['purchase_log']= invoice_data
        obj['credits']= credits_calculation(credits_count)
        obj['client_sub']= remaining_credits
        obj['weekly_api_calls'] = logs
        obj['analytics'] = api_logs
        obj['download_obj'] = download_obj
        obj['total_errate']=overall_error_rate
        obj['purchase_data']=purchase_data
    except Exception as e:
        print("Exceptions---->",str(e))
        obj['success'] = False
        obj["error"] = str(e)
        obj["statusCode"] = 500
    return obj


def error_rate_calculation(upper,lower):
    if upper != 0 and lower != 0:
        e_rate = (upper/lower) * 100
        e_rate = round(e_rate)
        return e_rate
    else:
        return 0
    
def user_purchased_api(data):
    api_access_dict = {item['api_name']: item['access_count'] for item in data}
    return api_access_dict

def transform_data(download_obj,email,remaining_credits):
    total_api = {}
    env_vars: Dict[str, Optional[str]] = get_env_vars()
    client_sub= env_vars.get(USERTABLE,'client-subscriptions-featureZ24-277')
    if 'feature' in client_sub:
        client_sub = DEVCLIENT_TABLE
    user_key={"email":email}
    user_data=get_item(client_sub,user_key)
    if user_data:
        if user_data.get('subscriptions'):
            total_api =  user_purchased_api(user_data.get('subscriptions'))
    

    ######## Download Report Final Set
    output = []
    if isinstance(download_obj,dict):
        for date, services in download_obj.items():
            for service_name, details in services.items():
                error_request = details.get('requests', 0) - details.get('credits', 0)
                error_rate = error_rate_calculation(error_request,details.get('requests', 0))
                
                if service_name in total_api:
                    entry = {
                        "User_ID": email,  # Assuming sequential user IDs
                        "DateTime": date,
                        "API Service": ZitaPlan.NameConvertion(service_name),
                        "Call Request": details.get('requests', 0),
                        "Credits consumed": credits_calculation(details.get('credits', 0)),
                        "Remaining credits": total_api.get(service_name,0),  # Example value, should be computed or obtained separately
                        "Error rates": error_rate # Example value, should be computed or obtained separately
                    }
                    output.append(entry)

    if isinstance(download_obj,list):
        for obj in download_obj:
            error_count = obj.get('request', 0) - obj.get('credits', 0)
            status_code = obj.get('statuscode',0)
            date = obj['date']
            obj['date'] = date.split('.')[0]
            if status_code == 0:
                status_code = 400 if error_count == 1 else 200
            if ZitaPlan.NameConvertion(obj['api_name']):
                entry = {
                    # "User_ID": email,  # Assuming sequential user IDs
                    "Date&Time (UTC)": obj['date'],
                    "API Service":ZitaPlan.NameConvertion(obj['api_name']),
                    "End Point" :f"/"+obj['api_name'],
                    "Call Request": obj.get('request', 0),
                    "Credits Consumed": obj.get('credits', 0),
                    # "Remaining Credits": obj.get('remaining_count', 0) if obj.get('remaining_count') else total_api.get(obj['api_name'],0) ,  # Example value, should be computed or obtained separately
                    "Error Rates": error_count,
                    "Status Code":status_code    # Example value, should be computed or obtained separately
                    }
                output.append(entry)
    return output
    


def datetime_convert(date_string : str):
    date_object = datetime.strptime(date_string, "%Y-%m-%d")
    return date_object

def credits_calculation(credits_count):
    if credits_count:
        remaining_creditss=math.floor(credits_count)
        return remaining_creditss
    return 0


def purchased_data(email,client_sub,invoice_table,api_table):
    purchase_data = []
    if client_sub:
        subscription = client_sub.get('subscriptions', [])
        for subscription in subscription:
            api_name=subscription['api_name']
            available_credit = subscription.get('access_count')
            addon_count = subscription.get('addon_count')
            purchased_at = extract_date(subscription.get('purchased_at'))
            expired_at = extract_date(subscription.get('expired_at'))
        
            if api_name:
                expression=Attr('api_name').eq(api_name)
                invoice_data = query_item(invoice_table,'email',email,expression=expression)
                expression=Attr('api_name').eq(api_name) & Attr('statuscode').eq('200')
                api_tab = query_item(api_table,'email',email,expression=expression)
                credit_used=math.floor(len(api_tab))
                total_credit = 0
                for invoice in invoice_data:
                    total_credit  = total_credit  + invoice['total']
                    
                
                purchase_data.append({
                    'api_name': ZitaPlan.DashBoardNameConvertion(api_name),
                    'total_credit':total_credit,
                    'credit_used':credit_used,
                    'available_credit':available_credit,
                    'payment_date': purchased_at,
                    'expired_date': expired_at,
                    'addon_count': addon_count

                })
    return purchase_data

     




