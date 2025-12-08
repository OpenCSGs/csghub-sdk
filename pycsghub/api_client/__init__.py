from typing import Optional

from pycsghub.utils import disable_xnet, get_endpoint, get_token_to_send

from .api_client import CsghubApi
from .api_client_interface import HubApi
from .api_client_xet import CsgXnetApi


def get_csghub_api(token: Optional[str] = None, endpoint: Optional[str] = None) -> HubApi:
    token = get_token_to_send(token)
    endpoint = get_endpoint(endpoint=endpoint)
    return CsghubApi(token=token, endpoint=endpoint) if disable_xnet() else CsgXnetApi(token=token, endpoint=endpoint)
