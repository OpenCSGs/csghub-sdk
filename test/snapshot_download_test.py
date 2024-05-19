import unittest
from snapshot_download import snapshot_download


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_snapshot_download(self):
        token = "f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9" + \
                "b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf"
        endpoint = "https://hub-stg.opencsg.com"
        repo_id = 'wayne0019/lwfmodel'
        cache_dir = '/home/test'
        result = snapshot_download(repo_id,
                                   cache_dir=cache_dir,
                                   endpoint=endpoint,
                                   token=token)
        print(result)



if __name__ == '__main__':
    unittest.main()
