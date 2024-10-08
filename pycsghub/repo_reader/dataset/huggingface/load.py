from typing import Dict, Mapping, Optional, Sequence, Union
import datasets
from datasets.splits import Split
from datasets.features import Features
from datasets.download.download_config import DownloadConfig
from datasets.download.download_manager import DownloadMode
from datasets.utils.info_utils import VerificationMode
from datasets.utils.version import Version
from datasets.iterable_dataset import IterableDataset
from datasets.dataset_dict import DatasetDict, IterableDatasetDict
from datasets.arrow_dataset import Dataset
from pycsghub.snapshot_download import snapshot_download
from pycsghub.utils import get_token_to_send
from pycsghub.constants import REPO_TYPE_DATASET

def load_dataset(
    path: str,
    name: Optional[str] = None,
    data_dir: Optional[str] = None,
    data_files: Optional[Union[str, Sequence[str], Mapping[str, Union[str, Sequence[str]]]]] = None,
    split: Optional[Union[str, Split]] = None,
    cache_dir: Optional[str] = None,
    features: Optional[Features] = None,
    download_config: Optional[DownloadConfig] = None,
    download_mode: Optional[Union[DownloadMode, str]] = None,
    verification_mode: Optional[Union[VerificationMode, str]] = None,
    ignore_verifications="deprecated",
    keep_in_memory: Optional[bool] = None,
    save_infos: bool = False,
    revision: Optional[Union[str, Version]] = None,
    token: Optional[Union[bool, str]] = None,
    use_auth_token="deprecated",
    task="deprecated",
    streaming: bool = False,
    num_proc: Optional[int] = None,
    storage_options: Optional[Dict] = None,
    trust_remote_code: bool = None,
    **config_kwargs,
) -> Union[DatasetDict, Dataset, IterableDatasetDict, IterableDataset]:
    if token is None:
        try:
            token = get_token_to_send(None)
        except Exception:
            pass
    localPath = snapshot_download(path, repo_type=REPO_TYPE_DATASET, cache_dir=cache_dir, token=token)
    return datasets.load.load_dataset(
        path=localPath,
        name=name,
        data_dir=data_dir,
        data_files=data_files,
        split=split,
        cache_dir=cache_dir,
        features=features,
        download_config=download_config,
        download_mode=download_mode,
        verification_mode=verification_mode,
        ignore_verifications=ignore_verifications,
        keep_in_memory=keep_in_memory,
        save_infos=save_infos,
        revision=revision,
        token=token,
        use_auth_token=use_auth_token,
        task=task,
        streaming=streaming,
        num_proc=num_proc,
        storage_options=storage_options,
        trust_remote_code=trust_remote_code,
        **config_kwargs
    )