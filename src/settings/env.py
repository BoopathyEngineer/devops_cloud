import os
from typing import Dict, Any, Optional

from dotenv import dotenv_values




def get_env_vars(path=None) -> Dict[str, Any]:
    # path = r'/Users/dianahealthdev/Documents/iris/src/scripts/local_test.env' #for testing purpose
    env_vars = dotenv_values()
    if not env_vars:
        env_vars = os.environ
    return env_vars
