from decimal import Decimal
import time
from settings.env import get_env_vars
from typing import Dict, Optional
from typing import Optional
from settings.constants import CONFIGTABLE
from amazonservice.dynamodb import get_item,scan_item
import json
from settings.configuration import DEVCONFIG_TABLE
from datetime import datetime, timedelta
from subscriptions.stripe_service import Invoice, Session, StripeFunction, Subscription



class ZitaPlan:
    def __init__(self):
        self.value = self

    @staticmethod
    def get_purchase_details(meta_data:dict):
        obj = {}
        if isinstance(meta_data,dict):
            plan = json.loads(meta_data.get('subscription_name'))
            quantity = json.loads(meta_data.get('quantity'))
            env_vars :  Dict[str, Optional[str]] = get_env_vars()
            configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-featureZ24-274')
            if 'feature' in configtable:
                configtable = DEVCONFIG_TABLE
            data = scan_item(configtable)
            for u in data:
                api = u.get('api_name')
                obj[api] = {}

            for i,y in zip(plan,quantity):
                plan_id,feat_id = ZitaPlan.float_convertion(i)
                plan_name = ZitaPlan.identify_apis(plan_id,feat_id)
                if plan_name.get('name'):
                    apiname = plan_name.get('name')
                    feat = plan_name.get('val')
                    if isinstance(obj.get(apiname),dict):
                        if obj[apiname].get(feat) == None:
                            obj[apiname][feat] = 0
                    for v in data:
                        if v.get('api_name') == apiname:
                            counts = v.get(feat)
                            if counts.get('requests'):
                                credits = int(counts["requests"]) * int(y)
                                if feat=="addon":
                                    credits = int(credits)
                                if isinstance(obj.get(apiname),dict):
                                    if obj[apiname].get(feat):
                                        obj[apiname][feat] = credits  
                                    else:
                                        obj[apiname][feat] = credits 
        return obj

    @staticmethod
    def identify_apis(num1:int,num2:int):
        val = ''
        name = ''
        if isinstance(num1,str):
           num1 = int(num1)
        if num1 == 1:
           val = ZitaPlan.identify_plans(num2)
           name = 'resume_parser'
        if num1 == 2:
           val = ZitaPlan.identify_plans(num2)
           name = 'jd_parser'
        if num1 == 3:
           val = ZitaPlan.identify_plans(num2)
           name = 'profile_summary'
        if num1 == 4:
           val = ZitaPlan.identify_plans(num2)
           name = 'jd_generation'
        if num1 == 5:
           val = ZitaPlan.identify_plans(num2)
           name = 'matching'
        if num1 == 6:
           val = ZitaPlan.identify_plans(num2)
           name = 'comparitive_analysis'
        if num1 == 7:
           val = ZitaPlan.identify_plans(num2)
           name = 'interview_questions'
        dataobj = {'name':name,'val':val}
        return dataobj
        
    @staticmethod
    def identify_plans(num1:int):
        if isinstance(num1,str):
           num1 = int(num1)
        if num1 == 1:
           return 'monthly'
        if num1 == 2:
           return 'yearly' 
        if num1 == 3:
           return 'addon'

    @staticmethod
    def float_convertion(id:float):
        num1 = None
        num2 = None
        if id:
            if isinstance(id,str):
                id = float(id)
            if isinstance(id,float):
                string = str(id)
                parts = string.split('.')
                num1, num2 = map(int, parts)
        return num1,num2
    
    @staticmethod
    def status_check(status : str):
        if status:
            if status == 'paid':
                return True
            else:
                return False
        else:
            return False
        
    @staticmethod
    def NameConvertion(api_name):
        convertion = None
        if api_name == 'resume_parser':
            convertion = 'Resume Parser'
        if api_name == 'jd_parser':
            convertion = 'JD Parser'
        if api_name == 'profile_summary':
            convertion = 'Profile Summary'
        if api_name == 'jd_generation':
            convertion = 'JD Assistance'
        if api_name == 'matching':
            convertion = 'Matching Analysis'
        if api_name == 'comparitive_analysis':
            convertion = 'Comparative Analysis'
        if api_name == 'interview_questions':
            convertion = 'Interview Question Generation'
        return convertion
    
    @staticmethod
    def DashBoardNameConvertion(api_name):
        convertion = None
        if api_name == 'resume_parser':
            convertion = 'Resume Parser'
        if api_name == 'jd_parser':
            convertion = 'JD Parser'
        if api_name == 'profile_summary':
            convertion = 'Profile Summary'
        if api_name == 'jd_generation':
            convertion = 'AI JD Assistance'
        if api_name == 'matching':
            convertion = 'AI Matching Analysis'
        if api_name == 'comparitive_analysis':
            convertion = 'Comparative Analysis'
        if api_name == 'interview_questions':
            convertion = 'AI Interview Question Generation'
        return convertion
    

    @staticmethod
    def determine_service(monthly=None, addon=None, yearly=None):
        if (monthly or yearly) and not addon:
            return 'API service'
        elif addon and not (monthly or yearly):
            return 'Add-on Credits'
        elif (monthly or yearly) and addon:
            return 'API service'
        else:
            return "Invalid configuration"
        
    @staticmethod
    def APIType_Convertion(api):
        if api:
            for k,v in api.items():
                if v and k: 
                    if isinstance(v,dict):
                        addon = v.get('addon')
                        month = v.get('monthly')
                        year = v.get('yearly')
                        return ZitaPlan.determine_service(monthly=month,addon= addon,yearly= year)

        return None
    

    @staticmethod
    def payment_mode(meta_data):
        mode = 'subscription'
        if isinstance(meta_data,dict):
            plan = json.loads(meta_data.get('subscription_name'))
            quantity = json.loads(meta_data.get('quantity'))
            if len(plan) == 1 and len(quantity) == 1:
                for i,y in zip(plan,quantity):
                    if ".3" in i:
                        mode = 'payment'
                    else:
                        mode = "subscription"
            elif len(plan) > 1 and len(quantity) > 1:
                mode = "subscription"
            return mode
        return mode

    @staticmethod
    def API_PurchaseLog_Description(api_name):
        convertion = None
        if api_name == 'resume_parser':
            convertion = 'Automates the extraction of important information from resumes for efficient candidate assessment'
        if api_name == 'jd_parser':
            convertion = 'Extracts essential details from job descriptions, easing the analysis process'
        if api_name == 'profile_summary':
            convertion = 'Provides a brief summary of key candidate details for quick evaluation'
        if api_name == 'jd_generation':
            convertion = 'Uses AI to create detailed, attractive job descriptions to attract the right candidates'
        if api_name == 'matching':
            convertion = 'Uses AI to match candidates with job descriptions based on skills and experiences'
        if api_name == 'comparitive_analysis':
            convertion = 'Compares candidates across various attributes to provide decision-making insights'
        if api_name == 'interview_questions':
            convertion = 'Automatically generates interview questions tailored to job specifics and candidate profiles'
        return convertion

    @staticmethod
    def find_subscription(user_data,api_obj):
        if isinstance(user_data,dict):
            user_data = user_data.get('subscriptions')
        final_api = None
        if api_obj and isinstance(api_obj,dict):
            for k,v in api_obj.items():
                if v:
                    final_api = k
        if user_data and final_api:
            for i in user_data:
                if i.get('api_name') == final_api:
                    return i.get('sub_id')
        return None
    
    @staticmethod
    def description_stripe_using_id(api_obj):
        if isinstance(api_obj,dict):
            for k,v in api_obj.items():
                if v:
                    final_api = ZitaPlan.API_PurchaseLog_Description(k)
                    return final_api
        
    
    @staticmethod
    def subs_convertion(meta_data,user_data,subscription,invoice,mode=None):
        inv_obj = {}
        if mode == 'payment' and invoice:
            latest_invoice = invoice
        print("subscription",subscription,mode,meta_data)
        if subscription:  ### Based on Subscription
            subscription_obj = Subscription.retrieve_subcription(subscription)
            latest_invoice = subscription_obj.get('latest_invoice','')
            start_date = StripeFunction.get_stripedate(subscription_obj.get('current_period_start'))
            end_date =  StripeFunction.get_stripedate(subscription_obj.get('current_period_end'))
            next_billing_date = end_date
        else:    ### Based on Add-on
            start_date = None
            end_date =  None
            next_billing_date = None
        new_userobj = []
        if isinstance(meta_data,dict):
            type_api = ZitaPlan.APIType_Convertion(meta_data)
            for k,v in meta_data.items():
                if v:
                    print("user_data/////",user_data,k)
                    if user_data:
                        if user_data.get('subscriptions'):
                            new_start_date = datetime.now()
                            subscription_data = user_data.get('subscriptions',[])
                            avail_api = [item.get('api_name','') for item in subscription_data]
                            for t in subscription_data:
                                if t.get('api_name') == k:
                                    purchased_api = k
                                    purchased_apiname_convertion = ZitaPlan.NameConvertion(k)
                                    access_count = t['access_count']
                                    addon_count = t['addon_count']
                                    feature_count = t['feature_count']
                                    print(f"2CURRENT_____AccessCount {access_count}, Feature Count {feature_count}, Addon Count {addon_count}")
                                    if v.get('addon'):
                                        addon_count = addon_count + v['addon']
                                    feature_month = 0
                                    feature_year = 0
                                    if v.get('monthly'):
                                        feature_month = v['monthly'] 
                                    if v.get('yearly'):
                                        feature_year = v['yearly']
                                    feat_count = feature_month  + feature_year
                                    if feature_count and feat_count != 0:
                                        feature_count = feature_count + feat_count
                                    if feature_count == 0 and feat_count != 0:
                                        feature_count = feature_count + feat_count
                                    access_count =  feature_count + addon_count
                                    start_date = start_date if start_date else t.get('purchased_at')
                                    end_date = str(end_date) if end_date else t.get('expired_at')
                                    print(f"AccessCount {access_count}, Feature Count {feature_count}, Addon Count {addon_count}")
                                    if subscription == None:
                                        subscription = t.get('sub_id')
                                    t['addon_count'] = addon_count
                                    t['feature_count'] = feature_count
                                    t['access_count'] = access_count
                                    t['purchased_at'] = str(start_date)
                                    t['expired_at'] = end_date
                                    t['sub_id'] = subscription
                                    t['invoice_id'] = latest_invoice
                                    t['name'] = purchased_apiname_convertion
                            if k not in avail_api:
                                purchased_api = k
                                purchased_apiname_convertion = ZitaPlan.NameConvertion(k)
                                addon_count = 0
                                if v.get('addon'):
                                    addon_count = v['addon']
                                feature_month = 0
                                feature_year = 0
                                if v.get('monthly'):
                                    feature_month = v['monthly'] 
                                if v.get('yearly'):
                                    feature_year = v['yearly']
                                feat_count = feature_month + feature_year
                                access_count =  feat_count + addon_count
                                start_date = start_date if start_date else new_start_date
                                end_date = str(end_date) if end_date else t.get('expired_at')
                                newobj = {'api_name':k,'access_count':access_count,'feature_count':feat_count,'addon_count':addon_count,'purchased_at':str(start_date),'expired_at':end_date,'name':purchased_apiname_convertion,'sub_id':subscription if subscription == None else subscription,'invoice_id': latest_invoice}
                                subscription_data.append(newobj)

                    else:
                        purchased_api = k
                        purchased_apiname_convertion = ZitaPlan.NameConvertion(k)
                        ####### TODO for Not Purchased USER
                        addon_count = 0
                        if v.get('addon'):
                            addon_count = v['addon']
                        feature_month = 0
                        feature_year = 0
                        if v.get('monthly'):
                            feature_month = v['monthly'] 
                        if v.get('yearly'):
                            feature_year = v['yearly']
                        feat_count = feature_month + feature_year
                        access_count =  feat_count + addon_count
                        newobj = {'api_name':k,'access_count':access_count,'feature_count':feat_count,'addon_count':addon_count,'purchased_at':str(start_date),'expired_at':str(end_date),'name':purchased_apiname_convertion,'sub_id':subscription,'invoice_id': latest_invoice}
                        new_userobj.append(newobj)

        if latest_invoice:
            invoice_obj = Invoice.retrieve_invoice(latest_invoice)
            invoice_pdf = invoice_obj.get('invoice_pdf')
            receipt_url = invoice_obj.get('hosted_invoice_url')
            invoice_number = invoice_obj.get('number')
            status = ZitaPlan.status_check(invoice_obj.get('status'))
            total_amount = StripeFunction.get_invoice_amount_paid(invoice_obj.get('amount_paid'))
            total_amount = Decimal(total_amount)
            total_amount = round(total_amount, 2)
            invoice_item = StripeFunction.get_invoiceitem(latest_invoice) 
            invoice_credits=ZitaPlan.credit_calc(meta_data)
            ## INVOICE TABLE UPDATION 
            if mode == "payment":
                start_date = datetime.now()
            if purchased_api and purchased_apiname_convertion and type_api:
                descriptions = [item.get('description','') for item in invoice_item]
                descriptions = ','.join(descriptions)
                descriptions = ZitaPlan.description_stripe_using_id(meta_data)
                inv_obj = {'invoice':invoice_number,'api_name':purchased_api,'name':purchased_apiname_convertion,'invoice_pdf':invoice_pdf,'receipt_url':receipt_url,
                'invoice_id':latest_invoice,
                'credits':invoice_credits,'description':descriptions,'expired_date': str(end_date) if type_api != 'Add-on Credits' else None,
                'payment_date':str(start_date),'type':type_api,
                'next_billing_date':str(next_billing_date) if next_billing_date else None,'paid':status,"total":total_amount,'invoice_item':invoice_item}
                
            

            if user_data == None:
                user_data = new_userobj
            else:
                if user_data.get('subscriptions'):
                    user_data = subscription_data
                else:
                    user_data = user_data.get('subscriptions',[])

            return user_data,inv_obj
        else:
            return [],{}



    @staticmethod
    def Purchased_Api(meta_data):
        if isinstance(meta_data,dict):
            for k,v in meta_data.items():
                if v:
                    return k
                
    @staticmethod
    def credit_calc(meta_data):
        sum1 = 0
        for k,v in meta_data.items():
            if v:
                for y,t in v.items():
                    sum1 += int(t)
                return sum1 
    
    @staticmethod
    def identify_api_id(name):
        valueslist = []
        if name == 'addon':
            valueslist = [ str(i + 0.3) for i in range(1, 8) ]
        if name == 'monthly':
            valueslist = [ str(i + 0.1) for i in range(1, 8) ]
        if name == 'yearly':
            valueslist = [ str(i + 0.2) for i in range(1, 8) ]
        if name == 'product':
            valueslist = [ str(i + 0.1) for i in range(1, 8) ]
        return valueslist
    
    @staticmethod
    def find_category_name(meta_data):
        name = 'Product'
        if isinstance(meta_data,dict):
            plan = json.loads(meta_data.get('subscription_name')) 
            if isinstance(plan,list):
                api_ids = ZitaPlan.identify_api_id('addon')
                exists = any(item in api_ids for item in plan)
                if len(plan) == 1 and exists:
                    name = 'Add on credit'
                elif len(plan) == 1 and exists == False:
                    name = 'Product'
                else:
                    name = 'Product'
        return name
    

    @staticmethod
    def session_update_status(session):
        session = Session.retrieve_session(session.id)
        # Start checking session status
        while True:
            session_status = session.get('status')  # Retrieve the current status
            invoice_status = session.get('invoice')
            if session_status == 'complete' and invoice_status is not None:       # Check if status is 'complete'
                break                              # Exit the loop if complete
            else:
                time.sleep(2)                      # Wait before checking again
                session = Session.retrieve_session(session.id)  # Refresh the session
        return session

