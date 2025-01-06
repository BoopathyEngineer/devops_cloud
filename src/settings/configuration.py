SUPPORTED_FORMAT = [".txt", ".doc", ".docx", ".pdf"]  
RESUMES_FILE = ['resume','resume1','resume2']
JD_FILE = ['jd']
JD_FILESIZE = "5MB" 
JD_EXCEED = 5
RESUME_EXCEED = 2
RESUME_FILESIZE = "2MB"
INVALID_PATH = "Invalid Path"
INVALID_METHOD = "Invalid Method"
MIN_LENGTH  = 300
MAX_LENGTH = 5000
UNSUPPORTED_FILE_FORMAT = "The file format is not supported. Please upload a document in .txt, .doc, .docx, or .pdf format." 
UNSUPPORTED_TEXT_FORMAT = "The text format is not supported. Please provide proper text format." 
JD_FILESIZE_EXCEED = "The file size exceeds the maximum limit of 5MB.Please select a smaller file."
JD_MISSING = "Job description key is missing."#1
INSUFFICIENT_CHARACTERS_JD = "Job Description must contain minimum of 300 characters."
EXCESSIVE_CHARACTERS_JD = "Job Description should not exceed 2000 characters."
INSUFFICIENT_CHARACTERS_RESUME = "Resume must contain minimum of 300 characters."
EXCESSIVE_CHARACTERS_RESUME = "Resume should not exceed 2000 characters."
JD_PARSER_ERROR = "Parsing failed. Please check the document and try again."
RESUME_FILESIZE_EXCEED = "File size exceeds 2MB limit. Please select a smaller file."
RESUME_MISSING = "Resume key is missing"
RESUME_FORMAT = "Please upload the resume in file format"
RESUME_PARSER_ERROR = "Resume parsing failed. Please check the document and try again"
PROFILE_COMPATIBILITY = {
    'KEY': ["Skills","Technical Tools and Languages","Roles and Responsibilities","Soft Skills","Experience","Qualification"]
}
ENHANCED_COMPATIBILITY = {
    'KEY': ["Industry-Specific Experience","Domain Specific Experience","Location Alignment","Certification","Cultural Fit","References and Recommendation"]
}
VALID_INFO = "Please provide valid information."
PROCEED_CRIETRIA = "Please assign weightage for at least one criterion to proceed."
NO_CRITEIRA = "Please assign weightage for at least one criterion to proceed."#2
MISMATCH_PROFILE_COMPATIBILITY = "Total weightage for Profile Compatibility Criteria must sum to 100. Please adjust your criteria weightages."
MISMATCH_ENHANCED_COMPATIBILITY = "Total weightage for Enhanced Matching Criteria must sum to 100. Please adjust your criteria weightages."
INVALID_INPUT = "Invalid weightage input. Please enter a number between 0 and 100."
INVALID_COUNT_INPUT = "Invalid count input. Please enter a numerical value."
LEAST_LEVEL = "Please choose at least one difficulty level to proceed."
COUNTS_MISSING = "Please specify the number of questions for the chosen difficulty level."
TYPE_MISSING = "Difficulty level key is missing."
INVALID_COUNT = "Invalid Count. Provide the proper count."
INVALID_LEVEL = "Invalid Level. Provide the proper level."
INVALID_TYPE = "Invalid Type. Provide the proper type."
INVALID_TYPE_LEVEL = "Invalid Type and Level. Provide the proper level and type"
INVALID_TYPE_COUNT = "Invalid Type and Count. Provide the proper type and count"
INVALID_LEVEL_COUNT ="Invalid Level and Count. Provide the proper level and count"
INVALID_TYPE_LEVEL_COUNT = "Invalid Type, Level and Count. Provide the proper level, type and count"

SUMMARY_LENGTH = 150
SUMMARY_CHARACTERS = "Summary should not exceed 150 characters."
LEVEL_COUNT_MISSING = 'Both difficulty level and count keys are missing.'
WEIGHTAGE_MISSING = "Weightage Matching key is missing."
NO_DATA = "No Information Available"
QUESTION_LIMIT_FORMAT = "Question count must be between 1 and 15."
CRITERIA_FORMAT = "Provide the Proper Format for Criteria"
EMPTY_FIELD = "Please provide valid information."
LIST_FORMAT = "Invalid content was entered. Please specify the correct format"
REQUIRED = {
    "/matching" : ["jd","resume","profile_matching"],
    "/comparitive_analysis" : ["jd","resume1"],
    "/interview_questions":["jd","resume","role","criteria"],
    "/profile_summary":["resume"],
    "/jd_parser":["jd"],
    "/resume_parser":["resume"],
    "/jd_generation":["job_title","industry_type","min_experience","overview","skills"],
}

SUBSCRIPTION_PATH = ["/user_details"]

EXCEED_FILESIZE = {
    "/matching" : {
        "jd": JD_EXCEED,
        "resume": RESUME_EXCEED
    },
    "/comparitive_analysis" : {
        "jd": JD_EXCEED,
        "resume": RESUME_EXCEED
    },
    "/interview_questions":{
        "jd": JD_EXCEED,
        "resume": RESUME_EXCEED
    },
    "/profile_summary": {
        "jd": JD_EXCEED,
        "resume": RESUME_EXCEED
    },
    "/jd_parser": {
        "jd": JD_EXCEED,
        "resume": RESUME_FILESIZE
    },
    "/resume_parser":{
        "jd": JD_EXCEED,
        "resume": RESUME_FILESIZE
    },
    "/jd_generation":{
        "jd": JD_EXCEED,
        "resume": RESUME_FILESIZE
    },
}


############ TABLE ##############
CONFIG_TABLE = 'zita-config-staging'
SUBSCRIPTION_TABLE  = 'client-subscriptions-staging'

DEVCONFIG_TABLE = 'zitaconfig-dev'
DEVCLIENT_TABLE = 'client-subscriptions-dev'
DEVPURCHASE_TABLE = 'client-purchase-dev'
DEVAPI_TABLE = 'api-dev'
DEVINVOICE_TABLE = 'invoice-dev'
DEVNOTIFICATION_TABLE = 'notification-dev'
DEVCOUPONUSERSPECIFICTBALE='coupon-userspecific-dev'
DEVCOUPON_TABLE = 'coupon-dev'
DEVUSERCOUPON_TABLE = 'usercoupon-dev'
DEV_S3BUCKET = 'zita-dev'


########### STRIPE KEYS #########
DEV_STRIPE = 'dev'




###################################################
INVALID_WEIGHTAGE_INPUT  = 'Invalid weightage input. Please enter a number between 0 and 100.'


######## COMPARATIVE ###########

COMPARATIVE_CRITERIA = "No criteria selected. Please choose at least one criterion to proceed."
COMPARATIVE_MIN_INSUFFICIENT = "At least two resumes are required. Please upload additional resumes to proceed."
COMPARATIVE_MAX_EXCEED = "The maximum limit of 5 resumes is exceeded. Please upload no more than 5 resumes to proceed."
COMPARATIVE_DUPLICATE = "Duplicate resume found. Please upload a unique resume."
COMPARATIVE_COUNT = 5
COMPARATIVE_SCORE_ANALYSIS = {
    '0-3':""
}


FILE_COUNT_EXCEED = "Cannot proceed with one more files"


######## JD GENERATION ###########
VALID_JOB_TITLE = "Please provide a valid job title."
VALID_INDUSTRY_TYPE = "Please provide a valid industry type."
VALID_NUM_FORMAT = "Please enter a valid number."
NEGATIVE_NUM_FORMAT = "Please enter a positive number."
EXCEED_EXP_VALUE = "Please enter a realistic minimum experience requirement."
EXCEED_MAX_EXP_VALUE = 99 
MAX_MIN_EXP = "Maximum experience must be greater than the minimum experience."
COMPENTENCIES_MISSING = "Please provide valid competencies. Ensure entries are detailed and specific to the job requirements."
NICETOHAVE_MISSING = "Please provide relevant nice-to-have competencies. Ensure entries enhance the candidacy appropriately."
OVERVIEW_MISSING = "Please provide a brief overview of the main responsibilities and expected outcomes for the role."
INVALID_KEY="Unexpected key found"
INVALID_FORMAT="File format not supported"


######### SUBSCRIPTION #########
SUBSCRIPTION_EXPIRED = "Your subscription has expired. Please renew to regain access."
SUBSCRIPTION_CANCELLED = "Your subscription has been canceled. Access is no longer available."
INSUFFICIENT_CREDITS = "Insufficient credits. Please purchase more to continue usage."
CREDITS_EXPIRED = "Your credits have expired. Please purchase the credits"


########## AUTHENTICATION #########
INVALID_CREDENTIALS = 'Invalid username or password. Please check and try again.'
CREDENTIALS_MISSING = 'No authentication credentials provided.'
INVALID_APIKEY = 'Invalid API key. Please check your API key and try again.'
MISSING_APIKEY = 'No API key provided. Please include a valid API key.'



###################### headers ##################################
HEADERS= {
        "Access-Control-Allow-Origin":"*",
        "Access-Control-Allow-Headers":"Content-Type,Authorization",
        "Access-Control-Allow-Methods":"GET,POST,OPTIONS,PUT,PATCH",
    }










