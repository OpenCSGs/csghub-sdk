from http import HTTPStatus

import requests

from pycsghub.errors import NotExistError, InvalidParameter
from utils import get_endpoint
import os
from pycsghub.utils import ModelFile
import shutil
import re
from typing import Dict, List, Tuple, Optional
from gitwrapper import GitCommandWrapper

class CsgHubApi:
    '''
    csghub API wrapper class
    will implement them in June 2024
    '''

    def __init__(self):
        self.session = requests.Session()
        self.headers = {}
        self.endpoint = get_endpoint()
        pass

    def login(self, username, password):
        pass


    def get_model_url(self, model_id, revision):
        endpoint = self.endpoint
        path = (
            f"{endpoint}/hf/api/models/{model_id}/revision/main"
            if revision is None
            else f"{endpoint}/hf/api/models/{model_id}/revision/{quote(revision, safe='')}"
        )
        pass


    def get_model(self, model_id, revision):
        url = self.get_model_url(model_id)
        if revision:
            url += '?revision=' + str(revision)
        else:
            url += '?revision=' + str('main')
        r = self.session.get(url=url, headers=self.headers,)
        r.raise_for_status()
        if r.status_code == HTTPStatus.OK:
            if is_ok(r.json()): # todo 状态检查待补充
                return r.json()
            else:
                raise NotExistError(r.json()[])
        else:
            raise_for_http_status(r) #todo 待补充
        pass
    def create_model(self,
                     model_id: str,
                     visibility: Optional[int] = ModelVisibility.PUBLIC,
                     license: Optional[str] = Licenses.APACHE_V2,
):
        pass

    def push_model(self,
                    model_dir,
                    revision,
                    model_id,
                   ignore_file_pattern,
                   commit_message,
                   visibility,
                   license):

        if model_id is None:
            raise InvalidParameter('model_id cannot be empty!')
        if model_dir is None:
            raise InvalidParameter('model_dir cannot be empty!')
        if not os.path.exists(model_dir) or os.path.isfile(model_dir):
            raise InvalidParameter('model_dir must be a valid directory.')
        cfg_file = os.path.join(model_dir, ModelFile.CONFIGURATION)
        if not os.path.exists(cfg_file):
            raise ValueError(f'{model_dir} must contain a configuration.json.')
        # todo cookies to login?
        files_to_save = os.listdir(model_dir)
        if ignore_file_pattern is None:
            ignore_file_pattern = []
        if isinstance(ignore_file_pattern, str):
            ignore_file_pattern = [ignore_file_pattern]
        try:
            self.get_model(model_id=model_id, revision=revision)
        except Exception:
            # todo validate if visibility and license is ready to use?
            # if visibility is None or license is None:
            #     raise InvalidParameter(
            #         'visibility and license cannot be empty if want to create new repo'
            #     )
            # logger.info('Create new model %s' % model_id)
            self.create_model(
                model_id=model_id,
                visibility=visibility,
                license=license)
        tmp_dir = tempfile.mkdtemp()
        git_wrapper = GitCommandWrapper()
        try:
            repo = Repository(model_dir=tmp_dir, clone_from=model_id)
            branches = git_wrapper.get_remote_branches(tmp_dir)
            if revision not in branches:
                # logger.info('Create new branch %s' % revision)
                git_wrapper.new_branch(tmp_dir, revision)
            git_wrapper.checkout(tmp_dir, revision)
            files_in_repo = os.listdir(tmp_dir)
            for f in files_in_repo:
                if f[0] != '.':
                    src = os.path.join(tmp_dir, f)
                    if os.path.isfile(src):
                        os.remove(src)
                    else:
                        shutil.rmtree(src, ignore_errors=True)
            for f in files_to_save:
                if f[0] != '.':
                    if any([re.search(pattern, f) is not None for pattern in ignore_file_pattern]):
                        continue
                    src = os.path.join(model_dir, f)
                    if os.path.isdir(src):
                        shutil.copytree(src, os.path.join(tmp_dir, f))
                    else:
                        shutil.copy(src, tmp_dir)
            if not commit_message:
                date = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
                commit_message = '[automsg] push model %s to hub at %s' % (
                    model_id, date)
            if lfs_suffix is not None:
                lfs_suffix_list = [lfs_suffix] if isinstance(lfs_suffix, str) else lfs_suffix
                for suffix in lfs_suffix_list:
                    repo.add_lfs_type(suffix)

            # todo implement git wrapper
            git_wrapper.push(
                tmp_dir,
                commit_message=commit_message,
                local_branch=revision,
                remote_branch=revision)
            # if tag is not None:
            #     repo.tag_and_push(tag, tag)
        except Exception:
            raise
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


