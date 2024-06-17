import unittest
from pycsghub.snapshot_download import snapshot_download
from pycsghub.file_download import file_download
from pycsghub.errors import InvalidParameter


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_snapshot_download(self):
        token = ("4e5b97a59c1f8a954954971bf1cdbf3ce61a35sd5")
        endpoint = "https://hub.opencsg.com"
        repo_id = 'OpenCSG/csg-wukong-1B'
        cache_dir = '/home/test4'
        result = snapshot_download(repo_id,
                                   cache_dir=cache_dir,
                                   endpoint=endpoint,
                                   token=token)
        print(result)


    def test_singlefile_download(self):
        token = ("f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f"
                 "9b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf")
        endpoint = "https://hub-stg.opencsg.com"
        repo_id = 'wayne0019/lwfmodel'
        cache_dir = '/home/test6'
        result = file_download(repo_id,
                               file_name="README.md",
                               cache_dir=cache_dir,
                               endpoint=endpoint,
                               token=token)
        print(result)

    def test_singlefile_download_not_exist(self):
        token = ("4e5b97a59c1f8a954954971bf1cdbf3ce61a35d5")
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




if __name__ == '__main__':
    unittest.main()
