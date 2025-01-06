from typing import Dict, Optional
from env import get_env_vars


env_vars: Dict[str, Optional[str]] = get_env_vars()


SUPPORT_FILES = [".txt", ".doc", ".docx", ".pdf"]
DUPLICATE_FILES = " This is Already Exists"
REGION = "us-east-1"

BUCKET_NAME = "dcqc-featuretesting"
FILES = "All Files"
BATCHES = "Batches"
SENDERINDOX = "Sender"
LOGFOLDER = "Logs"
FROM_ADDRESS = "dcqc@sense7ai.com"
TO_ADDRESS = "dcqc@yopmail.com"



# <---- DB Configuration ---->
DEV_USERTABLE = "user-featured6"
DEV_USERLOGTABLE = "userlog-featured6"
DEV_BATCHTABLE = "batch-status-featured6"
# <-------->

MAX_FILESIZE = 6

FILE_EXCEED = "The file is Too large Give a file below 6 Mb"
