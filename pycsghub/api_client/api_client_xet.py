import os
from typing import Optional

from huggingface_hub import constants, HfApi

from pycsghub.utils import get_default_cache_dir, get_xnet_endpoint

class CsgXnetApi(HfApi):
    def __init__(self, token: Optional[str] = None, endpoint: Optional[str] = None, user_name: Optional[str] = None):
        endpoint = get_xnet_endpoint(endpoint=endpoint)
        os.environ["HF_ENDPOINT"] = endpoint
        os.environ["HF_HOME"] = str(get_default_cache_dir())
        
        self._token = token
        self._endpoint = endpoint
        self._user_name = user_name
        
        # Force update huggingface_hub constants if they were already loaded
        try:
            import huggingface_hub.constants
            import huggingface_hub.file_download
            
            if hasattr(huggingface_hub.constants, 'HF_ENDPOINT'):
                huggingface_hub.constants.HF_ENDPOINT = endpoint
            
            # Older versions or some contexts use ENDPOINT
            if hasattr(huggingface_hub.constants, 'ENDPOINT'):
                huggingface_hub.constants.ENDPOINT = endpoint

            template = endpoint + "/{repo_id}/resolve/{revision}/{filename}"
            if hasattr(huggingface_hub.constants, 'HUGGINGFACE_CO_URL_TEMPLATE'):
                 huggingface_hub.constants.HUGGINGFACE_CO_URL_TEMPLATE = template
            
            # Patch file_download local reference as it imports it from constants
            if hasattr(huggingface_hub.file_download, 'HUGGINGFACE_CO_URL_TEMPLATE'):
                 huggingface_hub.file_download.HUGGINGFACE_CO_URL_TEMPLATE = template
                 
        except ImportError:
            pass
            
        # Note: calling super().__init__ (HfApi) might use the default HF_ENDPOINT from huggingface_hub.constants
        # if it was imported before we set os.environ["HF_ENDPOINT"].
        # Explicitly passing endpoint ensures the instance uses our custom endpoint.
        super().__init__(endpoint=endpoint, token=token)
        
        # Also ensure instance .endpoint is set correctly (just in case super() didn't set it or overwrote it)
        self.endpoint = endpoint

    def hf_hub_download(self, *args, **kwargs):
        # Override hf_hub_download to ensure endpoint is passed if not present
        endpoint_arg = kwargs.pop('endpoint', None)
        if not endpoint_arg:
            endpoint_arg = self._endpoint
            
        # Ensure token is passed
        if 'token' not in kwargs and self._token:
             kwargs['token'] = self._token

        try:
             # Try passing endpoint if HfApi accepts it
             if endpoint_arg:
                 kwargs['endpoint'] = endpoint_arg
             return super().hf_hub_download(*args, **kwargs)
        except TypeError:
             pass
        except Exception:
             pass

        # If super() failed, fall back to functional call
        from huggingface_hub import hf_hub_download as origin_hf_hub_download
        if endpoint_arg:
             kwargs['endpoint'] = endpoint_arg
        
        # NOTE: hf_hub_download might default to HF_ENDPOINT constant if endpoint is not passed.
        # Even if we pass it, if the underlying implementation ignores it (unlikely) or if 
        # constants.HF_ENDPOINT is used somewhere else implicitly.
        
        # Force endpoint again just in case
        if 'endpoint' not in kwargs and self._endpoint:
             kwargs['endpoint'] = self._endpoint
             
        return origin_hf_hub_download(*args, **kwargs)

    def snapshot_download(self, *args, **kwargs):
        from huggingface_hub import snapshot_download as origin_snapshot_download
        
        # Ensure endpoint is passed
        if 'endpoint' not in kwargs:
            kwargs['endpoint'] = self._endpoint
            
        # Ensure token is passed
        if 'token' not in kwargs and self._token:
            kwargs['token'] = self._token
            
        return origin_snapshot_download(*args, **kwargs)
