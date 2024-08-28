import unittest
from pycsghub.utils import model_info

class MyTestCase(unittest.TestCase):
    token = "your_access_token"
    endpoint = "https://hub.opencsg.com"
    repo_id = 'wayne0019/lwfmodel'
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_model_info(self):
        fetched_model_info = model_info(self.repo_id,
                                        endpoint=self.endpoint,
                                        token=self.token)
        print(fetched_model_info.sha)
        print(fetched_model_info.siblings)




if __name__ == '__main__':
    unittest.main()
