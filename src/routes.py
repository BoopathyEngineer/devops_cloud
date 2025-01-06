from matching_api.service import Lambda_Matching_API
from interview_questions_api.service import Lambda_Interview_Questions_API
from comparitive_analysis.service import Lambda_Comparitive_Analysis_API
from profile_summary_api.service import Lambda_Profile_Summary_API
from jd_parser_api.service import Lambda_Jd_Parser_API
from resume_parser_api.service import Lambda_Resume_Parser_API
from jd_generation_api.service import Jd_Generation_API
from settings.validation import apikey_function
from settings.account_settings import Get_Account_Settings, Patch_Account_Settings
from products.api_products import get_api_documentation, get_api_products
from settings.Change_Password import Put_Change_Password_Without_Otp
from Login.Forgot_Password import Get_Forgot_Password, Get_Send_Mail_For_Forgot_Password
# from Login.test import initiate_forgot_password, verify_code_and_reset_password
from settings.reports import get_analytics, get_reports
from Login.Reset_Password import initiate_forgot_password, verify_code_and_reset_password
from Login.Signup import Get_resend_verification_code, Post_signup_api, Get_confirm_user_signup
from Login.Signout import Get_admin_sign_out_user
from subscriptions.payments import *
from subscriptions.purchase import Buy_Subscription, user_details
from notification.signal import  get_notification,credit_usage
from Login.Signin import Get_signin_api
from billing.invoice import get_invoice
from coupon.coupon import send_coupon
from chat.chat import gpt_chat,retrieve_chat_list,delete_chat,update_chat,get_chat,share_chat,gpt_chat2
AUTH_ROUTES = {
    'POST': {
        '/matching': Lambda_Matching_API,
        '/interview_questions' : Lambda_Interview_Questions_API,
        '/comparitive_analysis': Lambda_Comparitive_Analysis_API,
        '/profile_summary': Lambda_Profile_Summary_API,
        '/jd_parser': Lambda_Jd_Parser_API,
        '/resume_parser': Lambda_Resume_Parser_API,
        '/jd_generation': Jd_Generation_API,
        '/user_details':user_details,
    }
}



APP_ROUTES = {
    'GET':{
        '/account_settings': Get_Account_Settings,
        '/reports': get_reports,
        '/analytics': get_analytics,
        '/apikey': apikey_function,
        '/get_notification': get_notification,
        '/apiproducts': get_api_products,
        '/documentation_api': get_api_documentation,
        '/retrieve_session':Payments.retrive_session,
        '/billing_portal':Payments.billing_portal,
        '/order_summary':Payments.order_summary,
        '/invoice': get_invoice,
        '/credit_usage':credit_usage,
        '/subscription_update':Payments.subscription_update,
        '/cancel_subscription':Payments.cancel_subcription,
        '/renew_subscription':Payments.renew_subcription,
        '/buy_subscription': Buy_Subscription,
        '/retrieve_chat_list':retrieve_chat_list,
        
    },
    'PUT':{
        '/account_settings': Patch_Account_Settings,
        # '/send_otp_change_pass' : Send_Otp_Change_Password,
        # '/confirm_code_change_pass' : Verify_Code_and_Change_Password,
        '/retrieve_session':Payments.retrive_session,
        '/change_password_without_otp':Put_Change_Password_Without_Otp,
    },
    'POST':{
        '/checkout_session': Payments.checkout_session,
        '/coupon_validation':Payments.coupon_validation,
        '/send_coupon': send_coupon,
        '/gpt_chat':gpt_chat,
         '/update_chat':update_chat,
         '/delete_chat':delete_chat,
         '/get_chat':get_chat,
         '/gpt_chat2':gpt_chat2
          
    }
}

SIGNIN_ROUTES = {
    'GET':{
        '/signin_api' : Get_signin_api,
        '/signout_api' : Get_admin_sign_out_user,
        # '/reset_password' : Get_Forgot_Password,
        # '/send_mail_forgot_password' : Get_Send_Mail_For_Forgot_Password,
        '/send_otp' : initiate_forgot_password,
        '/confirm_code_Reset_Pass' : verify_code_and_reset_password,
        '/verify_signup': Get_confirm_user_signup,
        '/resend_code' : Get_resend_verification_code,
        '/share_chat':share_chat
    },
    'POST':{
        '/signup_api'  : Post_signup_api
    }
}

