import unittest
from pycsghub.repo_reader import AutoModelForCausalLM
from pathlib import Path

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_something_else(self):
        a = AutoModelForCausalLM.from_pretrained('xzgan001/csg-wukong-1B')
        print(a)


if __name__ == '__main__':
    unittest.main()
