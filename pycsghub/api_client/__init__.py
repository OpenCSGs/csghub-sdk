from typing import Optional
import logging
from pycsghub.constants import REPO_TYPE_CODE, REPO_TYPE_MCPSERVER
from pycsghub.utils import disable_xnet, get_endpoint, get_token_to_send
from .api_client import CsghubApi
from .api_client_interface import HubApi
from .api_client_xet import CsgXnetApi
from pycsghub.cmd.repo_types import RepoType

logger = logging.getLogger(__name__)

def get_csghub_api(repo_type: Optional[RepoType] = None,
                   token: Optional[str] = None,
                   endpoint: Optional[str] = None,
                   user_name: Optional[str] = None) -> HubApi:
    token = get_token_to_send(token)
    endpoint = get_endpoint(endpoint=endpoint)

    if repo_type in [REPO_TYPE_CODE, REPO_TYPE_MCPSERVER]:
        logger.debug(f"Use CsghubApi for repo_type {repo_type}")
        return CsghubApi(token=token, endpoint=endpoint, user_name=user_name)

    if disable_xnet():
        logger.debug("xnet disabled")
        return CsghubApi(token=token, endpoint=endpoint, user_name=user_name)  
    else:
        logger.debug("xnet enabled")
        return CsgXnetApi(token=token, endpoint=endpoint, user_name=user_name)
