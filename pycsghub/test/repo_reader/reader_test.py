import unittest
from pycsghub.repo_reader import AutoModel

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_something_else(self):
        a = AutoModel()
        print(a)


if __name__ == '__main__':
    unittest.main()
