import os
from typing import Optional

from huggingface_hub import constants, HfApi

from pycsghub.utils import get_default_cache_dir, get_xnet_endpoint

class CsgXnetApi(HfApi):
    def __init__(self, token: Optional[str] = None, endpoint: Optional[str] = None):
        endpoint = get_xnet_endpoint(endpoint=endpoint)
        os.environ["HF_ENDPOINT"] = endpoint
        os.environ["HF_HOME"] = str(get_default_cache_dir())
        constants.ENDPOINT = endpoint
        constants.HUGGINGFACE_CO_URL_TEMPLATE = endpoint + "/{repo_id}/resolve/{revision}/{filename}"
        
        self._token = token
        self._endpoint = endpoint
        super().__init__(endpoint=endpoint, token=token)
