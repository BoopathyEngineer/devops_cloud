from datetime import datetime, timedelta
import re
import boto3
import phonenumbers
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from amazonservice.gateway import apikey_to_usageplan, create_apikey
from settings.validation import usage_identify
from settings.constants import COGNITO,CLIENT, COUPONTABLE, COUPONUSERSPECIFICTABLE, ENV
from settings.env import get_env_vars
from typing import Dict, Optional
from settings.aws_service import cognito
from Login.Reset_Password import Get_Username
from amazonservice.ses import send_raw_mail
from amazonservice.dynamodb import put_item, scan_item
from settings.configuration import DEVCOUPON_TABLE, DEVCOUPONUSERSPECIFICTBALE
from subscriptions.stripe_service import Find_Url
from templates.free_promo_code import FREE_PROMO,test_promo
client = cognito

env_vars: Dict[str, Optional[str]] = get_env_vars()
user_pool_id = env_vars.get(COGNITO,'us-east-1_sts6N2VIW')
client_id = env_vars.get(CLIENT,'vrvc7adabbtqsvheddjikvq8c')
env = env_vars.get(ENV, 'dev')

def Post_signup_api(event):
    obj = {}
    if event.get('body'):
        body = event.get('body')
        if body:
            email = body.get('email')
            password = body.get('password')
            phone_number = body.get('phoneNumber')
            first_name = body.get('firstName')
            last_name = body.get('lastName')
            organization_name = body.get('orgName')
            user_attributes = [
                {'Name': 'email_verified', 'Value': 'true'},
            ]

            phone_number = convert_phonenumber(phone_number)
            email_regex = r"[^@]+@[^@]+\.[^@]+"
            if not email:
                obj['message'] = 'Email Address is required.'
                return obj
            elif not re.match(email_regex, email):
                obj['message'] = 'Invalid email format.'
                obj['statusCode'] = 400
                return obj
            
            if first_name:
                user_attributes.append({'Name': 'custom:firstname', 'Value': first_name})
            else:
                obj['message'] = 'First Name is required.'
                obj['statusCode'] = 400
                return obj

            if last_name:
                user_attributes.append({'Name': 'custom:lastname', 'Value': last_name})
            else:
                obj['message'] = 'Last Name is required.'
                obj['statusCode'] = 400
                return obj

            if organization_name:
                user_attributes.append({'Name': 'custom:organisation', 'Value': organization_name})
            else:
                obj['message'] = 'Organisation Name is required.'
                obj['statusCode'] = 400
                return obj
            
            if phone_number:
                user_attributes.append({'Name': 'phone_number', 'Value': phone_number})
                user_attributes.append({'Name': 'phone_number_verified', 'Value': 'true'})
            else:
                obj['message'] = 'Phone Number is required.'
                obj['statusCode'] = 400
                return obj
            
            if not password:
                obj['message'] = 'Password is required.'
                obj['statusCode'] = 400
                return obj

            try:
                response = client.sign_up(
                    ClientId=client_id,
                    Username=email,
                    Password=password,
                    UserAttributes=[{'Name': 'email','Value': email}]
                )
                user_id = response.get('UserSub')
                response = client.admin_update_user_attributes(
                    UserPoolId=user_pool_id,
                    Username=email,
                    UserAttributes=user_attributes
                )
                obj['message'] = 'User created. Verify account with the code sent by email.'
                print(f"User created successfully.")
                print('verification code sended')
                if user_id:
                    environment = env_vars.get(ENV,'feature')
                    if "dev" in environment:
                        environment = "feature"
                    access = usage_identify(environment)
                
                    api_id, response = create_apikey(user_id, email)
                    usageplan = apikey_to_usageplan(api_id, access)
                obj['success'] = True
                obj['statusCode'] = 200

            except client.exceptions.UsernameExistsException as e:
                obj['statusCode'] = 409
                obj['message'] = 'Email already exist.'
                print(f"Error: {e.response['Error']['Message']}")
                
            except client.exceptions.InvalidParameterException as e:
                obj['statusCode'] = 400
                obj['message'] = 'Invalid parameters provided.'
                print(f"Error: {e.response['Error']['Message']}")
                
            except ClientError as e:
                obj['statusCode'] = 400
                obj['message'] = 'Error creating user.'
    return obj


# 
def Get_confirm_user_signup(event):
    obj = {}
    if event.get('queryparams'):
        queryparams = event.get('queryparams')
        if queryparams:
            email = queryparams.get('email')
            verification_code = queryparams.get('verificationCode')

            if not verification_code and not email:
                obj['message'] = 'Verification code and email are required.'
                obj['statusCode'] = 400
                return obj
            
            if not verification_code:
                obj['message'] = 'Verification code is required.'
                obj['statusCode'] = 400
                return obj
            
            if not email:
                obj['message'] = 'Email is required.'
                obj['statusCode'] = 400
                return obj

            user_status = client.admin_get_user(
                UserPoolId=user_pool_id, 
                Username=email
            )


            if user_status['UserStatus'] == 'CONFIRMED':
                obj['message'] = 'User Status already in confirmed'
                obj['statusCode'] = 400
                return obj
            else:
                try:
                # Confirm sign up using the provided verification code
                    response = client.confirm_sign_up(
                        ClientId=client_id,
                        Username=email,
                        ConfirmationCode=str(verification_code)
                    )
                    if response:
                        Free_promo_code(event)
                    else:
                        print('user not confirmed, so promo code not sended')
                    obj['message'] = 'User has been successfully verified.'
                    obj['statusCode'] = 200
                    obj['success'] = True
                    return obj

                except client.exceptions.UserNotFoundException:
                    obj['message'] = f"User {email} not found."
                    obj['statusCode'] = 404
                    obj['success'] = False
                    return obj

                except client.exceptions.CodeMismatchException:
                # Handle invalid confirmation code
                    obj['message'] = 'Invalid verification code provided.'
                    obj['statusCode'] = 400
                    return obj

                except client.exceptions.ExpiredCodeException:
                    # Handle expired confirmation code
                    obj['message'] = 'The verification code has expired. Please request a new one.'
                    obj['statusCode'] = 400
                    obj['success'] = False
                    return obj

                except ClientError as e:
                    # Handle other AWS Cognito client errors
                    error_message = e.response['Error']['Message']
                    print(f"Error confirming user: {error_message}")
                    obj['message'] = f"Failed to confirm user {email}. Error: {error_message}"
                    obj['statusCode'] = 400
                    return obj



def Get_resend_verification_code(event):
    obj = {}
    if event.get('queryparams'):
        queryparams = event.get('queryparams')
        if queryparams:
            email = queryparams.get('email')
            if not email:
                obj['message'] = 'Email is required to resend verification code.'
                return obj
            else:
                try:
                    # Resend the verification code to the user
                    response = client.resend_confirmation_code(
                        ClientId=client_id,
                        Username=email 
                    )
                    obj['message'] = f"Verification code resent to {email}."
                    obj['statusCode'] = 200
                    obj['success'] = True

                except client.exceptions.UserNotFoundException:
                    obj['message'] = f"User {email} not found."
                    obj['statusCode'] = 404
                    obj['success'] = False

                except ClientError as e:
                    obj['message'] = f"Failed to resend verification code for {email}. Reason: {e.response['Error']['Message']}"
                    obj['statusCode'] = 400
                    obj['success'] = False
                return obj

def Free_promo_code(event):
    env_vars :  Dict[str, Optional[str]] = get_env_vars()
    couponuserspecifictable=env_vars.get(COUPONUSERSPECIFICTABLE,'coupon-userspecific-featurecoupon-zita')
    coupontable = env_vars.get(COUPONTABLE, 'coupon-featurecoupon-zita')  
    if 'feature' in coupontable:
        coupontable = DEVCOUPON_TABLE
    if 'feature' in couponuserspecifictable:
        couponuserspecifictable=DEVCOUPONUSERSPECIFICTBALE
    res = {}
    if event:
        queryparams = event.get('queryparams', {})
        email = None
        if queryparams:
            email = queryparams.get('email')
        if not email:
            res={'statusCode':400,'message':'Email is required'}
            return res
        try:
            expression=Attr('api_id').eq("0")
            Coupon = scan_item(coupontable,expression = expression)
            if Coupon:
                for i in Coupon:
                    if i.get('coupon_code'):
                        coupon_id=i.get('coupon_id')
                        coupon_type=i.get('coupon_type')
                        discount_type = i.get('discount_type')
                        discount_value = i.get('discount_value')
                        expiredate = i.get('expire_date')
                        minvalue = i.get('min_purchase')
                        no_of_days=i.get('expire_days')
                        claimed_at=datetime.now()
                        if no_of_days:
                            expire_date=(claimed_at + timedelta(days=int(no_of_days)))  
                            expire_date_str=expire_date.strftime('%Y-%m-%d %H:%M:%S.%f') # For db
                            expiredate = expire_date.strftime('%d-%m-%Y')  # For email
                        else:
                            expiredate=expiredate  # It takes from other table
                        claimed_at = claimed_at.strftime(('%Y-%m-%d %H:%M:%S.%f'))
                        Coupon_code = i.get('coupon_code')
                        # no_of_days = i.get('no_of_days')
                        url = Find_Url(env)
                        link = url.get('success_url')
                   
                        email_body = FREE_PROMO.format(
                            recipient=email,
                            PROMOCODE=Coupon_code,
                            # EXPIRY_DATE=datetime.date.today() + datetime.timedelta(days=no_of_days),
                            NOOFDAYS = no_of_days,
                            LINK = link
                        )
                        email_obj = {
                            'recipient': email,
                            'subject': f'Your Free Gift as a Welcome to Standalone API Service!',
                            'body': email_body
                        }
                        email_success = send_raw_mail(email_obj)
                        if email_success:
                            print(f"Coupon code email sent successfully.")
                            res={'success':True,'statusCode':200,'message':'Free Promo code email sent successfully'}
                            item={'coupon_code':Coupon_code,
                                'email':email,
                                'claimed_at':claimed_at,
                                'used':False,
                                'coupon_id':coupon_id,
                                'discount_type':discount_type,
                                'discount_value':discount_value,
                                'coupon_type':coupon_type,
                                'expired':False,
                                'expire_date':expire_date_str if no_of_days else expiredate,
                                'min_purchase':minvalue}
                            put_item(couponuserspecifictable,item)
                            res={'success':True,'statusCode':200,'message':'Coupon details updated!'}
                        else:
                            res={'success':False,'statusCode':400,'message':'Free Promo code email not sent'}
 
   
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            res={'statusCode':500,'message':'An internal server error occured.'}
        return res


# Phone Number Convertion based on Country Code
def convert_phonenumber(num):
    num = str(num)
    try:
        parsed_number = phonenumbers.parse(num, None)
        country_code = parsed_number.country_code
        formatted_number = phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        formatted_number = re.sub(r"\D", "", formatted_number)
    except:
        country_code = num[:2]
        area_code = num[2:5]
        part1 = num[5:8]
        part2 = num[8:]
        formatted_number = f"{country_code} ({area_code}) {part1}-{part2}"
        formatted_number = re.sub(r"\D", "", formatted_number)
        formatted_number = f"{country_code}{formatted_number}"
    if "+" not in formatted_number:
        formatted_number= "+" + formatted_number
    return formatted_number