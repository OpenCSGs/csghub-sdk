import unittest
from pycsghub.snapshot_download import snapshot_download
from pycsghub.file_download import file_download
from pycsghub.errors import InvalidParameter


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_snapshot_download(self):
        token = ("your_access_token")
        endpoint = "https://hub.opencsg.com"
        repo_id = 'OpenCSG/csg-wukong-1B'
        cache_dir = '/home/test4'
        result = snapshot_download(repo_id,
                                   cache_dir=cache_dir,
                                   endpoint=endpoint,
                                   token=token)
        print(result)

    def test_singlefile_download(self):
        token = ("your_access_token")
        endpoint = "https://hub.opencsg.com"
        repo_id = 'wayne0019/lwfmodel'
        cache_dir = '/home/test6'
        result = file_download(repo_id,
                               file_name="README.md",
                               cache_dir=cache_dir,
                               endpoint=endpoint,
                               token=token)
        print(result)

    def test_singlefile_download_not_exist(self):
        token = ("your_access_token")
        endpoint = "https://hub.opencsg.com"
        repo_id = 'OpenCSG/csg-wukong-1B'
        cache_dir = '/home/test5'
        try:
            file_download(repo_id,
                          file_name="wolegequ.hehe",
                          cache_dir=cache_dir,
                          endpoint=endpoint,
                          token=token)
        except InvalidParameter as e:
            self.assertEqual(str(e), "file wolegequ.hehe not in repo wayne0019/lwfmodel")

    def test_snapshot_download(self):
        token = ("your_access_token")
        endpoint = "https://hub.opencsg.com"
        repo_id = 'AIWizards/tmmluplus'
        cache_dir = '~/Downloads/'
        result = snapshot_download(repo_id,
                                   repo_type="dataset",
                                   cache_dir=cache_dir,
                                   endpoint=endpoint,
                                   token=token)
        print(result)


if __name__ == '__main__':
    unittest.main()
