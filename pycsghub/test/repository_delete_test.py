import unittest
import tempfile
import os
from pycsghub.repository import Repository


class RepositoryDeletionTest(unittest.TestCase):
    def test_apply_deletions_removes_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            # create files
            os.makedirs(os.path.join(tmp, "sub"), exist_ok=True)
            f1 = os.path.join(tmp, "a.txt")
            f2 = os.path.join(tmp, "sub", "b.log")
            with open(f1, "w") as fp:
                fp.write("x")
            with open(f2, "w") as fp:
                fp.write("y")

            r = Repository(
                repo_id="ns/name",
                upload_path=tmp,
                path_in_repo="",
                work_dir=tmp,
                repo_type="model",
                endpoint="https://hub.opencsg.com",
                auto_create=False,
                commit_message="test",
                delete_patterns=["*.txt", "sub/*.log"],
            )

            # apply deletions
            r.apply_deletions(work_dir=tmp)

            self.assertFalse(os.path.exists(f1))
            self.assertFalse(os.path.exists(f2))


if __name__ == '__main__':
    unittest.main()
