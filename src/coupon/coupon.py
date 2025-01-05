from datetime import datetime, timedelta
from typing import Dict, Optional
import boto3
from amazonservice.ses import send_raw_mail
from amazonservice.dynamodb import convert_decimals, decimal_default, put_item, query_item, update_item,get_item,scan_item
from settings.env import get_env_vars
from amazonservice import dynamodb
from settings.constants import COUPONTABLE, COUPONUSERSPECIFICTABLE
from settings.configuration import DEVCOUPON_TABLE, DEVCOUPONUSERSPECIFICTBALE
from templates.coupon_email import COUPON_EMAIL
from settings.aws_service import cognito
from boto3.dynamodb.conditions import Key
client = cognito
from settings.aws_service import ses


def verify_email(email):
    try:
        response = ses.verify_email_identity(EmailAddress=email)
        print("Email verification mail send")
    except Exception as e:
        print("An Exception occured",e)


def send_coupon(event: Dict, user: str, email: str, username: str) -> Dict:
    env_vars :  Dict[str, Optional[str]] = get_env_vars()
    couponuserspecifictable=env_vars.get(COUPONUSERSPECIFICTABLE,'coupon-userspecific-featurecoupon-zita')
    coupontable = env_vars.get(COUPONTABLE, 'coupon-featurecoupon-zita')  
    if 'feature' in coupontable:
        coupontable = DEVCOUPON_TABLE
    if 'feature' in couponuserspecifictable:
        couponuserspecifictable=DEVCOUPONUSERSPECIFICTBALE
    queryparams = event.get('body')
    if not queryparams:
        return {'success': False, 'message': 'Query parameters are missing', 'statusCode': 200,'id':0}
    if queryparams == None:
        queryparams = event.get('queryparams')
    if queryparams:
        coupon_code = queryparams.get('coupon_code')
        email=queryparams.get('email') or email

    if coupon_code:
        coupon=query_item(coupontable,'coupon_code',coupon_code)
        if isinstance(coupon,list) and len(coupon) > 0:
            coupon=coupon[0]
    coupon_id=coupon.get('coupon_id')
    coupon_type=coupon.get('coupon_type')
    discount_type = coupon.get('discount_type')
    discount_value = coupon.get('discount_value')
    expiredate = coupon.get('expire_date')
    minvalue = coupon.get('min_purchase')
    expire_days=coupon.get('expire_days')
    claimed_at=datetime.now()
    if expire_days:
        expire_date=(claimed_at + timedelta(days=int(expire_days)))  
        expire_date_str=expire_date.strftime('%Y-%m-%d %H:%M:%S.%f') # For db
        expiredate = expire_date.strftime('%d-%m-%Y')  # For email
    else:
        expiredate=expiredate  # It takes from other table
    claimed_at = claimed_at.strftime(('%Y-%m-%d %H:%M:%S.%f'))  # Convert datetime to string(to store in dynamodb)
    used=None
    expired=None
    discount=discount_value
    if not email:
        res={'success':False,'statusCode':200,'message':'Email is required'}
        return res
    
    ''' To display in email '''
    if discount_type == 'percent':
        discount_value_str=f'{discount}%'
    elif discount_type == 'flat':
        discount_value_str=f'${discount}'
    try:
        email_body = COUPON_EMAIL.format(
            recipient=email,
            username=email,
            coupon_code=coupon_code,
            discount_value_str=discount_value_str,
            expiredate=expiredate,
            minvalue=minvalue
            )
        if discount_type == 'percent':
            email_obj = {
                'recipient': email,
                'subject': f'Exclusive Discount Inside: Use Code PromoAPI for {discount_value}% OFF!', 
                'body': email_body
            }
        elif discount_type == 'flat':
            email_obj = {
                'recipient': email,
                'subject': f'Exclusive Discount Inside: Use Code PromoAPI for ${discount_value} OFF!', 
                'body': email_body
            }
        email_success = send_raw_mail(email_obj)
        if email_success:
            res={'success':True,'statusCode':200,'message':'Coupon code email sent successfully'}
        else:
            res={'success':False,'statusCode':200,'message':'Coupon code email not sent'}
        if res['success']:
            item={'coupon_code':coupon_code,
                  'email':email,
                  'claimed_at':claimed_at,
                  'used':False,
                  'coupon_id':coupon_id,
                  'discount_type':discount_type,
                  'discount_value':discount_value,
                  'coupon_type':coupon_type,
                  'expired':False,
                  'expire_date':expire_date_str if expire_days else expiredate,
                  'min_purchase':minvalue}
            update_usercoupon=put_item(couponuserspecifictable,item)
            res={'success':True,'statusCode':200,'message':'Coupon details updated!'}

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        res={'statusCode':500,'message':'An internal server error occured.'}
    return res
