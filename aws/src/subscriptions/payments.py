from decimal import Decimal
from typing import Dict, Optional
from typing import Optional
from boto3.dynamodb.conditions import Key, Attr
from settings.constants import CLIENTPURCHASETABLE, CONFIGTABLE, COUPONUSERSPECIFICTABLE, INVOICETABLE, USERTABLE ,USERCOUPONTABLE,COUPONTABLE
from settings.env import get_env_vars
from amazonservice.dynamodb import convert_float_to_decimal, get_item, query_beginwith, query_item, querysort, querysort_item,update_item,put_item
from settings.configuration import *
from subscriptions.stripe_service import * 
import json
from datetime import datetime
from subscriptions.views import *
import time

class Payments:


    @staticmethod
    def __init__(self):
        self.value = self

    ##: Here Its Checkout Session initially Functions    
    def checkout_session(event: Dict,user:str,email: str,username: str) -> Dict:
        obj = {}
        statusCode = 400
        try: 
            env_vars :  Dict[str, Optional[str]] = get_env_vars()
            usertable = env_vars.get(USERTABLE, 'client-subscriptions-featurecoupon-code')
            if 'feature' in usertable:
                usertable = DEVCLIENT_TABLE
            userkey = {'email':email}
            user_data = get_item(usertable,userkey)
            if event.get('body'):
                queryparams = event.get('body')
                if queryparams:
                    stripe_id = queryparams.get('stripe')
                    quantity = queryparams.get('quantity')
                    plan_name = queryparams.get('plan_name')
                    coupon_code = queryparams.get('coupon_id')
                    check_out = queryparams.get('check_out')  # Only for coupon_validation API to retrieve the session 
                    if stripe_id:
                        if isinstance(stripe_id,str):
                            stripe_id = json.loads(stripe_id)
                    if quantity:
                        if isinstance(quantity,str):
                            quantity = json.loads(quantity)
                    if plan_name:
                        if isinstance(plan_name,str):
                            plan_name = json.loads(plan_name)

                    if not isinstance(stripe_id,list):
                        raise Exception('Give me a Stripe in Valid Format')
                    if not isinstance(quantity,list):
                        raise Exception('Give me a Quantity in Valid Format')
                    if isinstance(stripe_id,list) and isinstance(quantity,list):
                        result = []
                        result = [{"price": price, "quantity": int(count) if '.3' in plan_id else int(count)} for price, count,plan_id in zip(stripe_id, quantity,plan_name)]
                        # result = [{"price": price, "quantity": int(count)} for price, count in zip(stripe_id, quantity)]
                        
                        
                        customer_id = None
                        if user_data:
                            customer_id = user_data.get('customer_id')
                        
                        meta_data = {"subscription_name": json.dumps(plan_name),"quantity": json.dumps(quantity),'coupon_id':coupon_code}
                        mode = ZitaPlan.payment_mode(meta_data)
                        dataobj = {
                            'customer':customer_id,
                            'client_reference_id':user,
                            'line_items':result,
                            'meta_data':meta_data,
                            'customer_email':email,
                            'mode':mode,
                            'plan_name':plan_name,
                        }
                       
                        if coupon_code:
                            dataobj['discounts'] = [{'coupon': coupon_code}]                                     
                        checkout_session = Session.create_session(dataobj)
                        if check_out:
                            checkout=Session.create_session(dataobj)
                            return checkout
                        
                        obj['message'] = 'Session Created Successfully'
                        obj['session_id'] = checkout_session.get('id')
                        obj['url'] = checkout_session.get('url')
                        obj['statusCode'] = 200
                        obj['success'] = True
                        # obj['response'] = checkout_session
                    else:
                        raise Exception('give me stripe and quantity in Valid format')
            else:
                raise Exception('give me values in form-data')    
        except Exception as e:
            print("checkout Exception",str(e))
            obj['error'] = str(e)
            obj['message'] = 'Checkout Seassion Cannot Be Created'
            obj['statusCode'] = statusCode
        return obj


    ##: Here Its Retreive Session && Subsciptions Functions
    @staticmethod
    def retrive_session(event: Dict, user: str, email: str, username: str) -> Dict:
        obj = {}
        statusCode = 400
        try:
            
            if event.get('queryparams'):
                queryparams = event.get('queryparams')
            if event.get('body'):
                queryparams = event.get('body')

            if queryparams:
                session_id = queryparams.get('session_id')
                env_vars :  Dict[str, Optional[str]] = get_env_vars()
                invoicetable = env_vars.get(INVOICETABLE,'invoice-dev')
                usertable = env_vars.get(USERTABLE, 'client-subscriptions-dev')
                configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-dev')
                purchasetable = env_vars.get(CLIENTPURCHASETABLE,'client-purchase-feature309')    
                usercoupontable = env_vars.get(USERCOUPONTABLE,'usercoupon-featurecoupon-zita')  #No need
                coupontable = env_vars.get(COUPONTABLE,'coupon-featurecoupon-zita')
                couponuserspecifictable=env_vars.get(COUPONUSERSPECIFICTABLE,'coupon-userspecific-featurecoupon-zita')
                if 'feature' in usertable:
                    usertable = DEVCLIENT_TABLE
                if 'feature' in invoicetable:
                    invoicetable = DEVINVOICE_TABLE
                if 'feature' in configtable:
                    configtable = DEVCONFIG_TABLE
                if 'feature' in purchasetable:
                    purchasetable = DEVPURCHASE_TABLE
                if 'feature' in coupontable:
                    coupontable = DEVCOUPON_TABLE
                if 'feature' in usercoupontable:
                    usercoupontable = DEVUSERCOUPON_TABLE
                if 'feature' in couponuserspecifictable:
                    couponuserspecifictable=DEVCOUPONUSERSPECIFICTBALE

                userkey = {'email':email}
                user_data = get_item(usertable,userkey)
                if session_id:
                    session = Session.retrieve_session(session_id)
                    session = ZitaPlan.session_update_status(session)
                    coupon_id = session.get('metadata', {}).get('coupon_id')
                    if coupon_id:
                        expression=Attr('coupon_id').eq(coupon_id)
                        coupon=scan_item(coupontable,expression)
                        if coupon:
                            coupon=coupon[0]
                            coupon_code=coupon.get('coupon_code')
                            if coupon_code:
                                CouponCode.update_coupon_usage(couponuserspecifictable,coupon_code, email)
                    status = session.get('status')
                    if status == 'complete':
                        subscription = session.get('subscription')
                        invoice = session.get('invoice')
                        customer = session.get('customer')
                        meta_data = session.get('metadata')
                        mode = session.get('mode','')
                        if invoice and customer:
                            if meta_data:
                                find_category = ZitaPlan.find_category_name(meta_data)
                                meta_data = ZitaPlan.get_purchase_details(meta_data)
                                config_api = ZitaPlan.Purchased_Api(meta_data)
                                user_data,inv_obj = ZitaPlan.subs_convertion(meta_data,user_data,subscription,invoice,mode= mode)
                                inv_obj['email'] = email
                                print("user_data\n",user_data,"\ninv-obj\n",inv_obj,"meta_data",meta_data)
                                update_expression = 'SET #cust = :cust_val,#plan = :plan_obj'
                                attribute_names = {'#cust': 'customer_id','#plan':'subscriptions'}
                                attribute_values = {':cust_val': customer,':plan_obj':user_data}
                                table_updation = update_item(usertable,userkey,update_expression,attribute_values,attribute_names)
                                success = put_item(invoicetable,inv_obj) 
                                if config_api:
                                    apiname = {'api_name':config_api}
                                    config_data = get_item(configtable,apiname)
                                    if config_data:
                                        api_details = convert_float_to_decimal(config_data)
                                        api_details['email'] = email
                                        put_api_details = put_item(purchasetable,api_details)
                                obj['success'] = True
                                obj['statusCode'] = 200
                                obj['message'] = f'{find_category} purchased successfully!'
                        else:
                            raise Exception('Invoice Cannot Be Completed')
                    else:
                         raise Exception('Session cannot be compeleted')  
                else:
                    raise KeyError('session_id key is missing') 
            else:
                raise Exception('give me values in session_id') 
        except Exception as e:
            print("checkout Exception",str(e))
            obj['error'] = str(e)
            obj['statusCode'] = statusCode
            obj['message'] = f'{email} Subscription Purchased Unsuccessfully'
        return obj
    
    ##: Here Its billing Module
    @staticmethod
    def billing_portal(event: Dict, user: str, email: str, username: str) -> Dict:
        obj = {}
        statusCode = 400
        try:
            env_vars :  Dict[str, Optional[str]] = get_env_vars()
            usertable = env_vars.get(USERTABLE, 'client-subscriptions-featureZ24-277')
            if 'feature' in usertable:
                usertable = DEVCLIENT_TABLE
            url = None
            if event.get('queryparams'):
                queryparams = event.get('queryparams')
                url = queryparams.get('url')
            userkey = {'email':email}
            user_data = get_item(usertable,userkey)
            if user_data:
                if user_data.get('customer_id'):
                    customer = user_data.get('customer_id')
                    billing_portal = BillingPortal.create_billing_portal(customer,url)
                    obj['url'] = billing_portal.get('url')
                    obj['return_url'] = billing_portal.get('return_url')
                    obj['success'] = True
                    obj['statusCode'] = 200
                    obj['message'] = "The Customer Have The Billing Portal"
            else:
                raise Exception('The User Have No Payment and Info')
        except Exception as e:
            obj['error'] = str(e)
            obj['message'] = "The User Have No Payment and Info"
            obj['statusCode'] = statusCode
        return obj

    ##: Here Its Order Summary Functions
    @staticmethod
    def order_summary(event: Dict, user: str, email: str, username: str) -> Dict:
        obj = {}
        statusCode = 400
        try:
            if event.get('queryparams'):
                queryparams = event.get('queryparams')
                stripe_id = queryparams.get('stripe')
                if stripe_id:
                    if isinstance(stripe_id,str):
                        stripe_id = json.loads(stripe_id)
                quantity = queryparams.get('quantity')
                if quantity:
                    if isinstance(quantity,str):
                        quantity = json.loads(quantity)
                addon_plan = queryparams.get('addon_id')
                if addon_plan:
                    if isinstance(addon_plan,str):
                        addon_plan = json.loads(addon_plan)
                sub_plan = queryparams.get('plan_id')
                if sub_plan:
                    sub_plan = json.loads(sub_plan)
                env_vars :  Dict[str, Optional[str]] = get_env_vars()
                configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-featureZ24-274')
                usertable = env_vars.get(USERTABLE, 'client-subscriptions-featureZ24-274')
                if 'feature' in configtable:
                    configtable = DEVCONFIG_TABLE
                if 'feature' in usertable:
                    usertable = DEVCLIENT_TABLE
                config_data = scan_item(configtable)
                user_key = {'email':email}
                user_data = get_item(usertable,user_key)
                if not isinstance(stripe_id,list):
                    raise Exception('Give me a Stripe in Valid Format')
                if not isinstance(quantity,list):
                    raise Exception('Give me a Quantity in Valid Format')
                if addon_plan:
                    if not isinstance(addon_plan,list):
                        raise Exception('Give me a addon_plan in Valid Format')
                elif sub_plan:
                    if not isinstance(sub_plan,list):
                        raise Exception('Give me a subscription plan in Valid Format')
                
                result = [{"price": price, "quantity": int(count)} for price, count in zip(stripe_id, quantity)]
                #### PURCHASE ADDONS
                if addon_plan:
                    if isinstance(stripe_id,list) and isinstance(quantity,list) and isinstance(addon_plan,list):
                        meta_data = {'subscription_name':json.dumps(addon_plan),'quantity':json.dumps(quantity)}
                        meta_data = ZitaPlan.get_purchase_details(meta_data)
                        datalist = []
                        for k,v in meta_data.items():
                            if v:
                                for u in config_data:
                                    if u.get('api_name') == k:
                                        api_addon = u.get('addon')
                                        addon_value = v.get('addon')
                                        addon_credits = api_addon.get('credits')
                                        increased_cout = addon_value/api_addon.get('credits')
                                        print("addon_value",addon_value,"addon_credits",addon_credits,"increased_cout",increased_cout)
                                        addon_price = api_addon.get('price')
                                        if addon_price:
                                            if isinstance(addon_price,str):
                                                addon_price = int(addon_price)
                                            api_addon['price'] = addon_price * increased_cout
                                            api_addon['credits'] = api_addon.get('credits') * increased_cout
                                            api_addon['requests'] = api_addon.get('requests') * increased_cout
                                        datalist.append(api_addon)
                        obj['messsage'] = 'Addon Price Calculation has been done'
                        obj['datalist'] = datalist
                        obj['success'] = True
                        obj['statusCode'] = 200
                        return obj    

                ###### Update Subscriptions
                if sub_plan:   
                    if isinstance(stripe_id,list) and isinstance(quantity,list) and isinstance(sub_plan,list):
                        meta_data = {'subscription_name':json.dumps(sub_plan),'quantity':json.dumps(quantity)}
                        meta_data = ZitaPlan.get_purchase_details(meta_data)
                        datalist = []  
                        if user_data:
                            proration_date = int(time.time())
                            customer_id = user_data.get('customer_id')
                            find_sub = ZitaPlan.find_subscription(user_data,meta_data)
                            if find_sub:
                                subscription = stripe.Subscription.retrieve(find_sub)
                                items = [
                                    {"id": subscription["items"]["data"][0].id,
                                    "price": price, 
                                    "quantity": int(count)} 
                                    for price, count in zip(stripe_id, quantity)]
                                invoice = stripe.Invoice.upcoming(
                                    customer=customer_id,
                                    subscription=find_sub,
                                    subscription_items=items,
                                    subscription_proration_behavior="always_invoice",
                                    subscription_billing_cycle_anchor="now",
                                    # automatic_tax={
                                    #   "enabled": True,
                                    # },
                                    subscription_proration_date=proration_date,
                                )
                                un_used = invoice["lines"]["data"][0].amount / 100
                                new_price = invoice["lines"]["data"][-1].amount / 100
                                final = invoice["total"] / 100
                                subtotal = 0.00
                                if invoice.get("subtotal"):
                                    subtotal = invoice["subtotal"] / 100
                                tax_list = []
                                available_balance = 0
                                if final < 0:
                                    available_balance = final
                                stripe_balance = 0
                                stripe_bal = BalanceTransaction.list_customer_transaction(customer_id) ##cus_QaQI4ZBTuK2LQR
                                if stripe_bal.get('data'):
                                    stripe_bal = stripe_bal.get('data')
                                    if len(stripe_bal)>0:
                                        stripe_balance = (stripe_bal[0]["ending_balance"]) / 100
                                total_discount_amounts = 0
                                if invoice.get('total_discount_amounts'):
                                    total_amnt = invoice.get('total_discount_amounts')
                                    if len(total_amnt) > 0:
                                        total_discount_amounts = (total_amnt[0]["amount"] / 100)
                                if round(final) < 0 and stripe_balance != 0 and available_balance == 0:
                                    final = final - stripe_balance
                                else:
                                    final = final + stripe_balance
                                    # available_balance = 0
                                if final < 0:
                                    stripe_balance = subtotal
                                    final = "0.00"
                                else:
                                    available_balance = 0

                                obj['un_used'] = un_used
                                obj['final'] = final
                                obj['available_balance'] = available_balance
                                obj['stripe_balance'] = stripe_balance
                                obj['total_discount_amounts'] = total_discount_amounts
                                obj['new_price'] = new_price
                                obj['un_used'] = un_used
                                obj['success'] = True
                                obj['statusCode'] = 200
                                obj['message'] = "Customer Order Summary get Details Successfully"
                        if find_sub == None:
                            meta_data = {"subscription_name": json.dumps(sub_plan),"quantity": json.dumps(quantity)}
                            mode = ZitaPlan.payment_mode(meta_data)
                            dataobj = {
                                'customer':customer_id,
                                'client_reference_id':user,
                                'line_items':result,
                                'meta_data':meta_data,
                                'customer_email':email,
                                'mode':mode
                            }
                            checkout_session = Session.create_session(dataobj)
                            obj['message'] = 'Session Created Successfully'
                            obj['session_id'] = checkout_session.get('id')
                            obj['statusCode'] = 200
                            obj['url'] = checkout_session.get('url')
                
            else:
                raise Exception('give me values in queryparams')
        except Exception as e:
            obj['error'] = str(e)
            obj['statusCode'] = statusCode
        return obj
    
    ###: Here Its Order Summary Subscription Updation
    @staticmethod
    def subscription_update(event: Dict, user: str, email: str, username: str) -> Dict:
        obj = {}
        statusCode = 400
        try:
            if event.get('queryparams'):
                queryparams = event.get('queryparams')
                if queryparams:
                    stripe_id = queryparams.get('stripe')
                    if stripe_id:
                        if isinstance(stripe_id,str):
                            stripe_id = json.loads(stripe_id)
                    quantity = queryparams.get('quantity')
                    if quantity:
                        if isinstance(quantity,str):
                            quantity = json.loads(quantity)
                    plan_id = queryparams.get('plan_id')
                    if plan_id:
                        if isinstance(plan_id,str):
                            plan_id = json.loads(plan_id)
                    if stripe_id == None:
                        raise Exception('give me stripe_id in queryparams')
                    if quantity == None:
                        raise Exception('give me quantity in queryparams')
                    if plan_id == None:
                        raise Exception('give me plan_id in queryparams')
                    if stripe_id and plan_id and quantity:
                        if isinstance(stripe_id,list) and isinstance(quantity,list) and isinstance(plan_id,list):
                            result = [{"price": price, "quantity": int(count) * 10 if '.3' in plan_id else int(count)} for price, count,plan_id in zip(stripe_id, quantity,plan_id)]
                            # result = [{"price": price, "quantity": int(count)} for price, count in zip(stripe_id, quantity)]
                            meta_data_obj = {'subscription_name':json.dumps(plan_id),'quantity':json.dumps(quantity)}
                            meta_data = ZitaPlan.get_purchase_details(meta_data_obj)
                            env_vars :  Dict[str, Optional[str]] = get_env_vars()
                            configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-featureZ24-274')
                            usertable = env_vars.get(USERTABLE, 'client-subscriptions-featureZ24-274')
                            invoicetable = env_vars.get(INVOICETABLE, 'client-subscriptions-featureZ24-274')
                            if 'feature' in configtable:
                                configtable = DEVCONFIG_TABLE
                            if 'feature' in usertable:
                                usertable = DEVCLIENT_TABLE
                            if 'feature' in invoicetable:
                                invoicetable = DEVINVOICE_TABLE
                            userkey = {'email':email}
                            user_data = get_item(usertable,userkey)
                            find_sub = ZitaPlan.find_subscription(user_data,meta_data)
                            coupon = ''
                            proration_date = int(time.time())
                            if find_sub:
                                update_obj = {}
                                update_obj['proration_date'] = proration_date 
                                update_obj['coupon'] = coupon
                                update_obj['line_items'] = result
                                update_obj['meta_data'] =  meta_data_obj 
                                update_sub = Subscription.update_subscription(find_sub,update_obj)
                                # update_sub = Subscription.retrieve_subcription("sub_1Ppn5LJK7wwywY1KL5G3Nwcw")
                                customer = update_sub.get('customer','')
                                invoice = update_sub.latest_invoice
                                user_data,inv_obj = ZitaPlan.subs_convertion(meta_data,user_data,update_sub.id,invoice)
                                inv_obj['email'] = email
                                update_expression = 'SET #cust = :cust_val, #plan = :plan_obj'
                                attribute_names = {'#cust': 'customer_id','#plan':'subscriptions'}
                                attribute_values = {':cust_val': customer,':plan_obj':user_data}
                                table_updation = update_item(usertable,userkey,update_expression,attribute_values,attribute_names)
                                success = put_item(invoicetable,inv_obj) 
                                obj['success'] = True
                                statusCode = 200
                                obj['message'] = 'Subscription Purchased Successfully'
                            else:
                                obj['message'] = 'Subscription Not Found'
                                
            else:
                raise Exception('give me values in queryparams')
        except Exception as e:
            obj['error'] = str(e)
        obj['statusCode'] = statusCode
        return obj
    

    ##: Here Cancel Subscription Functions
    @staticmethod
    def cancel_subcription(event: Dict, user: str, email: str, username: str) -> Dict:
        statusCode = 400
        obj = {}
        try:
            if event.get('queryparams'):
                queryparams = event.get('queryparams')
                if queryparams:
                    sub_id = queryparams.get('subscription')
                    api_name = queryparams.get('api_name')
                    env_vars :  Dict[str, Optional[str]] = get_env_vars()
                    usertable = env_vars.get(USERTABLE, 'client-subscriptions-featureZ24-274')
                    if 'feature' in usertable:
                        usertable = DEVCLIENT_TABLE
                    if sub_id == None:
                        raise Exception('give me subscription in queryparams')
                    if api_name == None:
                        raise Exception('give me api_name in queryparams')
                    if sub_id and api_name:
                        cancel_subscription = Subscription.modify_cancel_subsription(sub_id)
                        userkey = {'email':email}
                        user_data = get_item(usertable,userkey)
                        if user_data:
                            sub_details = user_data.get("subscriptions",[])
                            for i in sub_details:
                                if i.get('api_name') == api_name:
                                    canceled_on = datetime.now()
                                    i['canceled_at'] = str(canceled_on)
                            update_expression = 'SET #plan = :plan_obj'
                            attribute_names = {'#plan':'subscriptions'}
                            attribute_values = {':plan_obj':sub_details}
                            table_updation = update_item(usertable,userkey,update_expression,attribute_values,attribute_names)
                            obj['message'] = "Cancel Subscription successFully"
                            statusCode = 200
                        else:
                            obj['message'] = 'User Subscription Not Found'
        except Exception as e:
            obj['error'] = str(e)
            obj['message'] = "Cancel Subscription UnsuccessFully"
        obj['statusCode'] = statusCode
        return obj

    ##: Here Its a Renew Subscriptions
    @staticmethod
    def renew_subcription(event: Dict, user: str, email: str, username: str) -> Dict:
        statusCode = 400
        obj = {}
        try:
            if event.get('queryparams'):
                queryparams = event.get('queryparams')
                if queryparams:
                    sub_id = queryparams.get('subscription')
                    api_name = queryparams.get('api_name')
                    env_vars :  Dict[str, Optional[str]] = get_env_vars()
                    configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-featureZ24-274')
                    usertable = env_vars.get(USERTABLE, 'client-subscriptions-featureZ24-274')
                    if 'feature' in configtable:
                        configtable = DEVCONFIG_TABLE
                    if 'feature' in usertable:
                        usertable = DEVCLIENT_TABLE
                    if sub_id == None:
                        raise Exception('give me subscription in queryparams')
                    if api_name == None:
                        raise Exception('give me api_name in queryparams')
                    if sub_id and api_name:
                        sub_details = Subscription.retrieve_subcription(sub_id)
                        key = {'api_name':api_name}
                        api_details = get_item(configtable,key)
                        if api_details:
                            if api_details.get('monthly'):
                                stripe_details = api_details["monthly"]
                                items=[{"id": sub_details["items"]["data"][0].id,"price": stripe_details["stripe_id"]}]
                                obj['line_items'] = items
                                renew_subscription = Subscription.renew_subscription(sub_id,obj)  
                                statusCode = 200
                                obj['messsge'] = 'Subscription Renewed Successfully'  
        except Exception as e:
            obj['error'] = str(e)
        obj['statusCode'] = statusCode
        return obj
    

    @staticmethod
    def coupon_code_api(event: Dict, user: str, email: str, username: str) -> Dict:
        obj ={}
        statusCode = 400
        try:
            if event.get('queryparams'):
                queryparams = event.get('queryparams')
                if queryparams:
                    coupon = queryparams.get('coupon_code')
                    api_name = queryparams.get('api_name')
                    api_id = queryparams.get('id')
                    env_vars :  Dict[str, Optional[str]] = get_env_vars()
                    configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-featureZ24-274')
                    usertable = env_vars.get(USERTABLE, 'client-subscriptions-featureZ24-274')
                    if 'feature' in configtable:
                        configtable = DEVCONFIG_TABLE
                    if 'feature' in usertable:
                        usertable = DEVCLIENT_TABLE
                    if coupon == None:
                        raise Exception('give me coupon code in queryparams')
                    if api_name == None:
                        raise Exception('give me api_name in queryparams')
                    if api_id == None:
                        raise Exception('give me api_name in queryparams')
                    if coupon and api_name and api_id:
                        key = {'api_name':api_name}
                        api_details = get_item(configtable,key)
                        if api_details:
                            num1,num2 = ZitaPlan.float_convertion(api_id)
                            api_package = ZitaPlan.identify_plans(num2)
                            if api_package:
                                if api_details.get(api_package):
                                    package_details = api_details[api_package]
                                    if package_details.get('code'):
                                        if coupon == package_details['code']:
                                            obj['valid'] = True
                                            obj['message'] = "Coupon Code is Valid"
                                        else:
                                            obj['valid'] = False
                                            obj['message'] = "Coupon Code is Valid"
                                    else:
                                        obj['message'] = 'Code is Not Found'
                                else:
                                    obj['message'] = 'API Package Details is Not Found'
                            else:
                                obj['message'] = 'API Package is Not Found'

        except Exception as e:
            obj['error'] = str(e)
        obj['statusCode'] = statusCode
        return obj

    ## Coupon Code Validation Function Handled
    @staticmethod
    def coupon_validation(event: Dict, user: str, email: str, username: str) -> Dict:
        coupon_code=None
        initial=None
        final=None
        discount=None
        queryparams = event.get('body')
        if not queryparams:
            return {'success': False, 'message': 'Query parameters are missing', 'statusCode': 200,'id':0}

        if queryparams == None:
            queryparams = event.get('queryparams')
        if queryparams:
            stripe_id = queryparams.get('stripe')
            quantity = queryparams.get('quantity')
            plan_name = queryparams.get('plan_name')
            coupon_code = queryparams.get('coupon_code')

            if isinstance(plan_name, str):
                plan_name=json.loads(plan_name)
            if isinstance(stripe_id, str):
                stripe_id=json.loads(stripe_id)
            if isinstance(quantity, str):
                quantity=json.loads(quantity)
            plan_list=plan_name[0] 
            find_api_id = None
            if len(plan_name)> 0:
                a = plan_name[0]
                current_plan = a.split('.')
                find_api_id = math.floor(int(current_plan[0]))
                find_api_id = str(find_api_id)
    
            env_vars :  Dict[str, Optional[str]] = get_env_vars()
            coupontable = env_vars.get(COUPONTABLE, 'coupon-featurecoupon-zita')
            usercoupontable = env_vars.get(USERCOUPONTABLE,'usercoupon-featurecoupon-zita')
            couponuserspecifictable=env_vars.get(COUPONUSERSPECIFICTABLE,'coupon-userspecific-featurecoupon-zita')
            configtable = env_vars.get(CONFIGTABLE, 'zitaconfig-dev')    
            if 'feature' in coupontable:
                coupontable = DEVCOUPON_TABLE
            if 'feature' in usercoupontable:
                usercoupontable = DEVUSERCOUPON_TABLE
            if 'feature' in configtable:
                configtable = DEVCONFIG_TABLE
            if 'feature' in couponuserspecifictable:
                couponuserspecifictable=DEVCOUPONUSERSPECIFICTBALE
            items = query_item(coupontable,'coupon_code',coupon_code)
            ''' Coupon Validation Starts Here'''

            '''#1#'''
            if isinstance(coupon_code, str) and len(coupon_code.split(",")) > 1:
                response = {'success': False, 'message': 'Only one coupon allowed per transaction.', 'statusCode': 200, 'id': 7}
                return response
            
            if isinstance(items,list) and len(items) == 0:  ### Invalid Code
                response={'success':False,'message':'Enter a valid coupon code.','statusCode':200,'id':1}
                return response
            
            
            if items:
                coupon_type = items[0]['coupon_type']
                if coupon_type == 'addon':
                    items = query_beginwith(coupontable,'coupon_code',coupon_code,'api_id',find_api_id)
                # if isinstance(items,list) and len(items) == 0:  ### Not Support to this plan
                #     response={'success':False,'message':'Coupon is Not Supported to this API SERVICE','statusCode':200,'id':3}
                #     return response
                if isinstance(items,list) and len(items) > 0:
                    items=items[0]
                    api_id=items.get('api_id')
                    plan_id=str(api_id)
                    discount_type=items.get('discount_type')
                    discount_value=items.get('discount_value')
                    min_purchase = items.get('min_purchase')
                    coupon_type=items.get('coupon_type')
                    coupon_id = items.get('coupon_id')
                    
                    ''' ## Expired Handling '''

                    #coupon expire 
                    expired_code= CouponCode.check_coupon_expired(coupontable,coupon_code,api_id) 
                    if expired_code.get('success',False):
                        response={'success':False,'message':'This coupon has expired.','statusCode':200,'id':2}
                        return response
                    
                    #coupon expire for specific user
                    coupon_expired = CouponCode.coupon_user_expired(couponuserspecifictable,coupon_code,email) 
                    if coupon_expired.get('success', False):
                        response={'success':False,'message':'This coupon has expired.','statusCode':200,'id':2}
                        return response

                    ''' ## Used Handling  '''
                    used = CouponCode.check_coupon_used(couponuserspecifictable,coupon_code,email) 
                    if used:
                        response={'success':False,'message':'This coupon has already been redeemed.','statusCode':200,'id':4}
                        return response
                    
                    api_ids = ZitaPlan.identify_api_id(coupon_type)
                    exists = any(item in api_ids for item in plan_name)

                    '''#2#'''
                    ''' Coupon Not Applicable to Current Cart '''
                    # if not exists:
                    #     response = {'success': False, 'message': 'Coupon not applicable to selected items.', 'statusCode': 200, 'id': 8}
                    #     return response

                    ''' While Apply the Coupon with Wrong Plan'''
                    if coupon_type == 'product' and exists == False:
                        response={'success': False, 'message': 'This coupon is valid for API products only.', 'statusCode': 200,'id':5}
                        return response
                    if coupon_type == 'addon' and exists == False:
                        response={'success': False, 'message': 'This coupon is valid for add-ons only.', 'statusCode': 200,'id':5}
                        return response

                    '''# Proceed with coupon application '''
                    if plan_id in ['0']:
                        res = {'success': True, 'message': 'Free promo code', 'coupon_type': coupon_type,'discount_type': discount_type,'discount_value': discount_value,'min_purchase': min_purchase, 'statusCode': 200}

                    elif plan_id in ['1', '2', '3', '4']:
                        res = {'success': True, 'message': 'product', 'coupon_type': coupon_type,'discount_type': discount_type, 'discount_value': discount_value,'min_purchase': min_purchase, 'statusCode': 200}

                    elif plan_id.split('.')[1] in ['1', '2']:
                        res = {'success': True, 'message': 'products coupon code', 'coupon_type': coupon_type,'discount_type': discount_type, 'discount_value': discount_value,'min_purchase': min_purchase, 'statusCode': 200}

                    elif plan_id.split('.')[1] == '3':
                        res = {'success': True, 'message': 'addon coupon code', 'coupon_type': coupon_type,'discount_type': discount_type, 'coupon_value': discount_value,'min_purchase': min_purchase, 'statusCode': 200}
                    
                    else:
                        response={'success':False,'message':'An error occured','statusCode':400,'id':0}
                        return response
                else:
                    response={'success':False,'message':'An error occured','statusCode':400,'id':0}
                    return response
            else:
                response={'success': False, 'message': 'An error occured', 'statusCode': 400,'id':0}
                return response


            ''' Coupon Validation End Here'''
            
            '''Keep if check to check if it is applicable for the user'''
            if coupon_code and email:
                coupon_user=querysort(couponuserspecifictable,'coupon_code',coupon_code,'email',email)
                if coupon_user:
                    response={'success':True,'message':'Valid for user','statusCode':200}
                else:
                    response={'success':False,'message':'Enter a valid coupon code.','statusCode':200}
                    return response

            ''' AMount Calculation Starts Here'''
            if items:
                if res['success'] :
                    coupon_id=items.get('coupon_id')
                    event = {
                        'body':{
                            'stripe':stripe_id,
                            'quantity':quantity,
                            'plan_name':plan_name,
                            'coupon_id':coupon_id,  
                            'check_out':1                         
                        }
                        }
                    checkout_session=Payments.checkout_session(event,user,email,username)
                    # if  checkout_session['error'] or 'error' in checkout_session:
                    #     response={'success':False,'message':'API Failed','statusCode':400,'id':0}
                    #     return response
                    initial = checkout_session['amount_subtotal']
                    final = checkout_session["amount_total"]
                    final = final/100
                    discount = checkout_session["total_details"]["amount_discount"]
                    discount= discount/100
                    expression=Attr('id').eq(int(find_api_id))
                    api_details = scan_item(configtable,expression=expression)

                    if api_details and isinstance(api_details,list):  # For products 
                        api_details = api_details[0]
                        prod_details = api_details.get('monthly')
                        addon_details = api_details.get('addon')
                        prod_initial_amount=int(prod_details.get('price'))
                        addon_initial_amount=int(addon_details.get('price'))
    
                    if coupon_type == 'product'  and len(plan_name) == 1:
                        addon_initial=0
                        prod_initial_amount=int(prod_details.get('price'))
                        initial=prod_initial_amount
                        i=initial

                    elif coupon_type == 'addon' and len(plan_name)==1:
                        initial=0
                        addon_initial_amount =int(addon_initial_amount)
                        addon_stripe_id=addon_details.get('stripe_id')
                        for price, count, plan_id in zip(addon_stripe_id, quantity, plan_name):
                            addon_initial_amount  = int(count) * addon_initial_amount
                        addon_initial=addon_initial_amount
                        i=addon_initial

                    elif len(plan_name)>1:
                        initial=int(prod_initial_amount)
                        addon_stripe_id=addon_details.get('stripe_id')
                        for price, count, plan_id in zip(addon_stripe_id, quantity, plan_name):
                            addon_initial_amount  = int(count) * addon_initial_amount
                        addon_initial=int(addon_initial_amount)
                        i=initial+addon_initial
        
                    if res['coupon_type']=="product":
                        coupon_type_id=0
                    elif res['coupon_type']=="addon":
                        coupon_type_id=1
                    coupon_obj  = {}
                        
                    coupon_obj = {
                        'success':True,
                        'statusCode': 200,
                        'plan_amount':initial,
                        'addon_amount':addon_initial,
                        'final':final,
                        'discount_amount':discount,
                        'coupon_type': coupon_type_id,
                        'code': coupon_id
                    }
                    if min_purchase and min_purchase > i:
                        return {'success': False, 'message': 'Minimum purchase required for this coupon.', 'statusCode': 200,'id':6}
                    return coupon_obj    
            else:
                response={'success':False,'message':'An error occured','statusCode':400,'id':0}
                return response
        else:
            response={'success':False,'message':'queryparams missing','statusCode':400,'id':0}
            return response
      
class CouponCode:

    @staticmethod
    def check_coupon_expired(table,coupon_code,sort_value):
        try:
            coupon = querysort(table,'coupon_code',coupon_code,'api_id',sort_value)
            if coupon and len(coupon) == 1:
                coupon = coupon[0]
                ex_date= coupon.get('expire_date')
                expire_date= datetime.strptime(ex_date, '%Y-%m-%d %H:%M:%S.%f').date()
                today=datetime.now().date()
                # if today >= expire_date+timedelta(days=1):
                if today > expire_date:
                    coupon_key = {'coupon_code': coupon_code,'api_id': sort_value}
                    update_expression = 'SET #plan = :plan_obj'
                    attribute_names = {'#plan' : 'expired'}
                    attribute_values = {':plan_obj' : True}
                    table_updation = update_item(table,coupon_key,update_expression,attribute_values,attribute_names)
                    response={'success':True,'message':'Coupon marked as expired!!','statusCode':200}
                    return response
                else:
                    response={'success':False,'message':'Coupon has not expired','statusCode':200}
                    return response
        except Exception as e:
            response={'success': False,'message': f'Error occurred: {str(e)}','statusCode': 500}
            return response
        
    @staticmethod
    def check_coupon_used(couponuserspecifictable,coupon_code,email):
        if couponuserspecifictable:
            items = querysort(couponuserspecifictable,'coupon_code',coupon_code,'email',email)
            if len(items) > 0:
                coupon = items[0]
                used = coupon.get('used')
                if used:
                    return used
                else:
                    return False
        return False
    
    @staticmethod
    def update_coupon_usage(usercoupontable,coupon_code,email):
        try:
            userkey = {'coupon_code':coupon_code,'email':email}
            update_expression = 'SET #plan = :plan_obj,#used_at = :used_at_value'
            attribute_names = {'#plan':'used','#used_at': 'used_at'}
            attribute_values = {':plan_obj':True,':used_at_value': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}
            table_updation = update_item(usercoupontable,userkey,update_expression,attribute_values,attribute_names)  
            print("Table updatation coupon is used by {email}",table_updation)
            # item={'coupon_code': coupon_code,'email': email,'used': True,'used_at': datetime.now().isoformat()}
            # response=put_item(usercoupontable,item)
            return True
        except Exception as e:
            print("update_coupon_usage Exception",e)
            return False
        
    '''to check coupon expired for specific user'''
    @staticmethod
    def coupon_user_expired(table,coupon_code,sort_value):
        try:
            coupon = querysort(table,'coupon_code',coupon_code,'email',sort_value)
            if coupon and len(coupon) == 1:
                coupon = coupon[0]
                ex_date= coupon.get('expire_date')
                if ex_date == None:
                    response = {'success':False,'message':'Coupon has not expired for this user','statusCode':200}
                    return response
                expire_date= datetime.strptime(ex_date, '%Y-%m-%d %H:%M:%S.%f').date()
                today=datetime.now().date()
                # if today > expire_date+timedelta(days=1):
                if today > expire_date:
                    coupon_key = {'coupon_code': coupon_code,'email': sort_value}
                    update_expression = 'SET #plan = :plan_obj'
                    attribute_names = {'#plan' : 'expired'}
                    attribute_values = {':plan_obj' : True}
                    table_updation = update_item(table,coupon_key,update_expression,attribute_values,attribute_names)
                    response={'success':True,'message':'Coupon marked as expired for this user!!','statusCode':200}
                    return response
                else:
                    response={'success':False,'message':'Coupon has not expired for this user','statusCode':200}
                    return response
            else:
                response={'success':False,'message':'Coupon doesnot exist for this user','statusCode':200}
                return response
        except Exception as e:
            response={'success': False,'message': f'Error occurred: {str(e)}','statusCode': 500}
            return response

        


