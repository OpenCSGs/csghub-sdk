import os
from typing import Optional

from huggingface_hub import HfApi,constants

from .api_client import CsghubApi
from .api_client_interface import HubApi
from .utils import disable_xnet, get_default_cache_dir, get_endpoint, get_token_to_send, get_xnet_endpoint


def get_csghub_api(token: Optional[str] = None, endpoint: Optional[str] = None) -> HubApi:
    token = get_token_to_send(token)
    endpoint = get_endpoint(endpoint=endpoint)
    if disable_xnet():
        return CsghubApi(token=token, endpoint=endpoint)
    else:
        endpoint = get_xnet_endpoint(endpoint=endpoint)
        os.environ["HF_ENDPOINT"] = endpoint
        os.environ["HF_HOME"] = str(get_default_cache_dir())
        constants.ENDPOINT = endpoint
        constants.HUGGINGFACE_CO_URL_TEMPLATE = endpoint + "/{repo_id}/resolve/{revision}/{filename}"
        return HfApi(endpoint=endpoint, token=token)
