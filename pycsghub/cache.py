import hashlib
import os
import pickle
import tempfile
import threading
from shutil import move, rmtree
from typing import Dict, Union


class FileSystemCache(object):
    KEY_FILE_NAME = '.msc'
    MODEL_META_FILE_NAME = '.mdl'
    MODEL_META_MODEL_ID = 'id'
    MODEL_VERSION_FILE_NAME = '.mv'
    """Local file cache.
    """

    def __init__(
            self,
            cache_root_location: str,
            **kwargs,
    ):
        """Base file system cache interface.

        Args:
            cache_root_location (str): The root location to store files.
            kwargs(dict): The keyword arguments.
        """
        try:
            # 在Windows下检查路径长度
            if os.name == 'nt' and len(os.path.abspath(cache_root_location)) > 240:
                print(f"Warning: Cache path too long for Windows: {cache_root_location}")
                # 使用短路径或截断
                try:
                    import win32api
                    short_path = win32api.GetShortPathName(cache_root_location)
                    if len(short_path) <= 240:
                        cache_root_location = short_path
                except ImportError:
                    # 截断路径
                    parts = cache_root_location.split(os.sep)
                    while len(cache_root_location) > 240 and len(parts) > 1:
                        parts.pop(1)  # 保留根目录
                        cache_root_location = os.sep.join(parts)

            os.makedirs(cache_root_location, exist_ok=True)
            self.cache_root_location = cache_root_location
            self._lock = threading.RLock()  # 添加线程锁
            self.load_cache()
        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to initialize cache at {cache_root_location}: {e}")

    def get_root_location(self):
        return self.cache_root_location

    def load_cache(self):
        """Load cache metadata with error handling."""
        self.cached_files = []
        cache_keys_file_path = os.path.join(self.cache_root_location,
                                            FileSystemCache.KEY_FILE_NAME)
        if os.path.exists(cache_keys_file_path):
            try:
                with open(cache_keys_file_path, 'rb') as f:
                    self.cached_files = pickle.load(f)
            except (pickle.PickleError, IOError, EOFError) as e:
                # 如果缓存文件损坏，重新创建
                print(f"Warning: Cache file corrupted, recreating: {e}")
                self.cached_files = []
                # 删除损坏的缓存文件
                try:
                    os.remove(cache_keys_file_path)
                except OSError:
                    pass

    def save_cached_files(self):
        """Save cache metadata with atomic operation."""
        with self._lock:  # 添加线程安全
            cache_keys_file_path = os.path.join(self.cache_root_location,
                                                FileSystemCache.KEY_FILE_NAME)
            try:
                # 使用临时文件确保原子性
                # 在Windows下使用系统临时目录
                if os.name == 'nt':
                    temp_dir = tempfile.gettempdir()
                else:
                    temp_dir = self.cache_root_location

                fd, fn = tempfile.mkstemp(dir=temp_dir, suffix='.tmp')
                try:
                    with os.fdopen(fd, 'wb') as f:
                        pickle.dump(self.cached_files, f)
                    # 原子性移动
                    move(fn, cache_keys_file_path)
                except (IOError, OSError) as e:
                    # 清理临时文件
                    try:
                        os.remove(fn)
                    except OSError:
                        pass
                    raise RuntimeError(f"Failed to save cache metadata: {e}")
            except Exception as e:
                raise RuntimeError(f"Failed to save cache metadata: {e}")

    def get_file(self, key):
        """Check the key is in the cache, if exist, return the file, otherwise return None.

        Args:
            key(str): The cache key.

        Raises:
            None
        """
        pass

    def put_file(self, key, location):
        """Put file to the cache.

        Args:
            key (str): The cache key
            location (str): Location of the file, we will move the file to cache.

        Raises:
            None
        """
        pass

    def remove_key(self, key):
        """Remove cache key in index, The file is removed manually

        Args:
            key (dict): The cache key.
        """
        with self._lock:  # 添加线程安全
            if key in self.cached_files:
                self.cached_files.remove(key)
                self.save_cached_files()

    def exists(self, key):
        """Check if key exists in cache with exact match."""
        for cache_file in self.cached_files:
            if cache_file == key:
                return True
        return False

    def clear_cache(self):
        """Remove all files and metadata from the cache
        In the case of multiple cache locations, this clears only the last one,
        which is assumed to be the read/write one.
        """
        with self._lock:  # 添加线程安全
            try:
                rmtree(self.cache_root_location)
                os.makedirs(self.cache_root_location, exist_ok=True)
                self.load_cache()
            except (OSError, IOError) as e:
                raise RuntimeError(f"Failed to clear cache: {e}")

    def hash_name(self, key):
        return hashlib.sha256(key.encode()).hexdigest()


class ModelFileSystemCache(FileSystemCache):
    """Local cache file layout
       cache_root/owner/model_name/individual cached files and cache index file '.mcs'
       Save only one version for each file.
    """

    def __init__(self, cache_root, owner=None, name=None, local_dir: Union[str, None] = None):
        """Put file to the cache
        Args:
            cache_root(`str`): The csghub local cache root(default: current directory)
            owner(`str`): The model owner.
            name('str'): The name of the model
        Returns:
        Raises:
            None
        <Tip>
            model_id = {owner}/{name}
        </Tip>
        """
        try:
            if owner is None or name is None:
                # get model meta from
                super().__init__(os.path.join(cache_root))
                self.load_model_meta()
            else:
                # 在Windows下处理路径分隔符
                if os.name == 'nt':
                    # 替换Windows不允许的字符
                    invalid_chars = '<>:"|?*'
                    for char in invalid_chars:
                        owner = owner.replace(char, '_')
                        name = name.replace(char, '_')

                cache_path = os.path.join(cache_root, owner, name)
                super().__init__(cache_path)
                self.model_meta = {
                    FileSystemCache.MODEL_META_MODEL_ID: '%s/%s' % (owner, name)
                }
                self.save_model_meta()
            self.cached_model_revision = self.load_model_version()
            self.local_dir = local_dir
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ModelFileSystemCache: {e}")

    def get_root_location(self):
        if self.local_dir is not None:
            return self.local_dir
        else:
            return self.cache_root_location

    def load_model_meta(self):
        """Load model metadata with error handling."""
        meta_file_path = os.path.join(self.cache_root_location,
                                      FileSystemCache.MODEL_META_FILE_NAME)
        if os.path.exists(meta_file_path):
            try:
                with open(meta_file_path, 'rb') as f:
                    self.model_meta = pickle.load(f)
            except (pickle.PickleError, IOError, EOFError) as e:
                print(f"Warning: Model meta file corrupted, using default: {e}")
                self.model_meta = {FileSystemCache.MODEL_META_MODEL_ID: 'unknown'}
        else:
            self.model_meta = {FileSystemCache.MODEL_META_MODEL_ID: 'unknown'}

    def load_model_version(self):
        """Load model version with error handling."""
        model_version_file_path = os.path.join(
            self.cache_root_location, FileSystemCache.MODEL_VERSION_FILE_NAME)
        if os.path.exists(model_version_file_path):
            try:
                with open(model_version_file_path, 'r') as f:
                    return f.read().strip()
            except (IOError, UnicodeDecodeError) as e:
                print(f"Warning: Model version file corrupted: {e}")
                return None
        else:
            return None

    def save_model_version(self, revision_info: Dict):
        """Save model version with error handling."""
        try:
            model_version_file_path = os.path.join(
                self.cache_root_location, FileSystemCache.MODEL_VERSION_FILE_NAME)
            with open(model_version_file_path, 'w') as f:
                version_info_str = 'Revision:%s' % (
                    revision_info['Revision'])
                f.write(version_info_str)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save model version: {e}")

    def get_model_id(self):
        return self.model_meta[FileSystemCache.MODEL_META_MODEL_ID]

    def save_model_meta(self):
        """Save model metadata with error handling."""
        try:
            meta_file_path = os.path.join(self.cache_root_location,
                                          FileSystemCache.MODEL_META_FILE_NAME)
            with open(meta_file_path, 'wb') as f:
                pickle.dump(self.model_meta, f)
        except (IOError, OSError, pickle.PickleError) as e:
            raise RuntimeError(f"Failed to save model metadata: {e}")

    def get_file_by_path(self, file_path):
        """Retrieve the cache if there is file match the path.

        Args:
            file_path (str): The file path in the model.

        Returns:
            path: the full path of the file.
        """
        for cached_file in self.cached_files:
            if file_path == cached_file['Path']:
                cached_file_path = os.path.join(self.cache_root_location,
                                                cached_file['Path'])
                if os.path.exists(cached_file_path):
                    return cached_file_path
                else:
                    self.remove_key(cached_file)

        return None

    def get_file_by_path_and_commit_id(self, file_path, commit_id):
        """Retrieve the cache if there is file match the path.

        Args:
            file_path (str): The file path in the model.
            commit_id (str): The commit id of the file

        Returns:
            path: the full path of the file.
        """
        for cached_file in self.cached_files:
            if file_path == cached_file['Path'] and \
                    (cached_file['Revision'].startswith(commit_id) or commit_id.startswith(cached_file['Revision'])):
                cached_file_path = os.path.join(self.cache_root_location,
                                                cached_file['Path'])
                if os.path.exists(cached_file_path):
                    return cached_file_path
                else:
                    self.remove_key(cached_file)

        return None

    def get_file_by_info(self, model_file_info):
        """Check if exist cache file.

        Args:
            model_file_info (ModelFileInfo): The file information of the file.

        Returns:
            str: The file path.
        """
        cache_key = self.__get_cache_key(model_file_info)
        for cached_file in self.cached_files:
            if cached_file == cache_key:
                orig_path = os.path.join(self.cache_root_location,
                                         cached_file['Path'])
                if os.path.exists(orig_path):
                    return orig_path
                else:
                    self.remove_key(cached_file)
                    break

        return None

    def __get_cache_key(self, model_file_info):
        cache_key = {
            'Path': model_file_info['Path'],
            'Revision': model_file_info['Revision'],  # commit id
        }
        return cache_key

    def exists(self, model_file_info):
        """Check the file is cached or not with improved version matching.

        Args:
            model_file_info (CachedFileInfo): The cached file info

        Returns:
            bool: If exists return True otherwise False
        """
        key = self.__get_cache_key(model_file_info)
        is_exists = False

        # 改进版本匹配逻辑：使用精确匹配或前缀匹配
        for cached_key in self.cached_files:
            if cached_key['Path'] == key['Path']:
                # 精确匹配
                if cached_key['Revision'] == key['Revision']:
                    is_exists = True
                    break
                # 前缀匹配（但要求至少6个字符，避免误匹配）
                elif (len(cached_key['Revision']) >= 6 and
                      cached_key['Revision'].startswith(key['Revision'])) or \
                        (len(key['Revision']) >= 6 and
                         key['Revision'].startswith(cached_key['Revision'])):
                    is_exists = True
                    break

        file_path = os.path.join(self.cache_root_location, model_file_info['Path'])
        if self.local_dir is not None:
            file_path = os.path.join(self.local_dir, model_file_info['Path'])

        if is_exists:
            if os.path.exists(file_path):
                return True
            else:
                # 修复：传递正确的参数给remove_key
                for cached_file in self.cached_files:
                    if (cached_file['Path'] == key['Path'] and
                            cached_file['Revision'] == key['Revision']):
                        self.remove_key(cached_file)
                        break
        return False

    def remove_if_exists(self, model_file_info):
        """We in cache, remove it.

        Args:
            model_file_info (ModelFileInfo): The model file information from server.
        """
        key = self.__get_cache_key(model_file_info)
        for cached_file in self.cached_files:
            if cached_file['Path'] == model_file_info['Path']:
                self.remove_key(cached_file)
                file_path = os.path.join(self.cache_root_location, cached_file['Path'])
                if self.local_dir is not None:
                    file_path = os.path.join(self.local_dir, cached_file['Path'])
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Warning: Failed to remove cached file {file_path}: {e}")
                break

    def put_file(self, model_file_info, model_file_location):
        """Put model on model_file_location to cache, the model first download to /tmp, and move to cache.

        Args:
            model_file_info (str): The file description returned by get_model_files.
            model_file_location (str): The location of the temporary file.

        Returns:
            str: The location of the cached file.
        """
        try:
            self.remove_if_exists(model_file_info)
            cache_key = self.__get_cache_key(model_file_info)
            cache_full_path = os.path.join(self.cache_root_location, cache_key['Path'])
            if self.local_dir is not None:
                cache_full_path = os.path.join(self.local_dir, cache_key['Path'])

            # 在Windows下处理路径分隔符
            if os.name == 'nt':
                cache_full_path = cache_full_path.replace('/', os.sep)

            cache_file_dir = os.path.dirname(cache_full_path)
            if not os.path.exists(cache_file_dir):
                os.makedirs(cache_file_dir, exist_ok=True)

            # 检查源文件是否存在
            if not os.path.exists(model_file_location):
                raise RuntimeError(f"Source file does not exist: {model_file_location}")

            # 移动文件到缓存
            move(model_file_location, cache_full_path)
            self.cached_files.append(cache_key)
            self.save_cached_files()
            return cache_full_path
        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to put file to cache: {e}")
