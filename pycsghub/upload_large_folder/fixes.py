try:
    from requests import JSONDecodeError  # type: ignore  # noqa: F401
except ImportError:
    try:
        from simplejson import JSONDecodeError  # type: ignore # noqa: F401
    except ImportError:
        from json import JSONDecodeError  # type: ignore  # noqa: F401
import contextlib
import logging
import os
import shutil
import stat
import tempfile
from functools import partial
from pathlib import Path
from typing import Callable, Generator, Optional, Union

import yaml
from filelock import BaseFileLock, FileLock, SoftFileLock, Timeout

from . import consts

logger = logging.getLogger(__name__)

yaml_dump: Callable[..., str] = partial(yaml.dump, stream=None, allow_unicode=True)  # type: ignore


@contextlib.contextmanager
def SoftTemporaryDirectory(
        suffix: Optional[str] = None,
        prefix: Optional[str] = None,
        dir: Optional[Union[Path, str]] = None,
        **kwargs,
) -> Generator[Path, None, None]:
    tmpdir = tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix, dir=dir, **kwargs)
    yield Path(tmpdir.name).resolve()

    try:
        # First once with normal cleanup
        shutil.rmtree(tmpdir.name)
    except Exception:
        # If failed, try to set write permission and retry
        try:
            shutil.rmtree(tmpdir.name, onerror=_set_write_permission_and_retry)
        except Exception:
            pass

    # And finally, cleanup the tmpdir.
    # If it fails again, give up but do not throw error
    try:
        tmpdir.cleanup()
    except Exception:
        pass


def _set_write_permission_and_retry(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)


@contextlib.contextmanager
def WeakFileLock(lock_file: Union[str, Path]) -> Generator[BaseFileLock, None, None]:
    lock = FileLock(lock_file, timeout=consts.FILELOCK_LOG_EVERY_SECONDS)
    while True:
        try:
            lock.acquire()
        except Timeout:
            logger.info("still waiting to acquire lock on %s", lock_file)
        except NotImplementedError as e:
            if "use SoftFileLock instead" in str(e):
                logger.warning(
                    "FileSystem does not appear to support flock. Falling back to SoftFileLock for %s", lock_file
                )
                lock = SoftFileLock(lock_file, timeout=consts.FILELOCK_LOG_EVERY_SECONDS)
                continue
        else:
            break

    yield lock

    try:
        return lock.release()
    except OSError:
        try:
            Path(lock_file).unlink()
        except OSError:
            pass
