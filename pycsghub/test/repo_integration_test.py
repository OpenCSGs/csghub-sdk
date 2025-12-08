import json
import os
import random
import shutil
import string
import tempfile
import unittest
from pathlib import Path

from dotenv import load_dotenv

# Mock/Override disable_xnet for testing
import pycsghub.utils
from pycsghub.cmd.repo import download, upload_files
from pycsghub.cmd.repo_types import RepoType

class RepoIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load env from project root
        root_dir = Path(__file__).parents[2]
        load_dotenv(root_dir / ".env")
        
        cls.token = os.getenv("CSGHUB_TOKEN")
        # JSON config for repos: '{"model": "ns/model-repo", "dataset": "ns/dataset-repo", "space": "ns/space-repo"}'
        cls.repos_json = os.getenv("CSGHUB_TEST_REPOS")
        cls.endpoint = os.getenv("CSGHUB_DOMAIN", "https://hub.opencsg.com")
        
        if not cls.token or not cls.repos_json:
            print("Skipping RepoIntegrationTest: CSGHUB_TOKEN or CSGHUB_TEST_REPOS not found in .env")
            cls.skip_test = True
        else:
            cls.skip_test = False
            try:
                cls.repos = json.loads(cls.repos_json)
            except json.JSONDecodeError:
                print("Invalid JSON in CSGHUB_TEST_REPOS")
                cls.skip_test = True
                return
            
            # Use system temp dir for isolation
            cls.test_dir = Path(tempfile.mkdtemp(prefix="csghub_test_"))
    
    def setUp(self):
        if self.skip_test:
            self.skipTest("Missing credentials")
    
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'test_dir') and cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
    
    def _generate_random_content(self, size_kb=1, binary=False):
        if binary:
            return os.urandom(size_kb * 1024)
        else:
            chars = string.ascii_letters + string.digits + "\n"
            return "".join(random.choice(chars) for _ in range(size_kb * 1024)).encode('utf-8')
    
    def _create_test_file(self, filename, size_kb=1, binary=False):
        path = self.test_dir / filename
        content = self._generate_random_content(size_kb, binary)
        mode = 'wb' if binary else 'w'
        if binary:
            with open(path, 'wb') as f:
                f.write(content)
        else:
            with open(path, 'w') as f:
                f.write(content.decode('utf-8'))
        return path, content
    
    def _run_with_xnet_toggle(self, enable_xnet: bool):
        # Patch disable_xnet in utils
        # disable_xnet() returns True if we want to disable xnet (use CsghubApi)
        # disable_xnet() returns False if we want to enable xnet (use HfApi)
        
        original_disable_xnet = pycsghub.utils.disable_xnet
        pycsghub.utils.disable_xnet = lambda: not enable_xnet
        
        try:
            print(f"\n--- Running tests with XNet {'Enabled' if enable_xnet else 'Disabled'} ---")
            self._run_all_types_cycle(expect_failure=enable_xnet)
        finally:
            pycsghub.utils.disable_xnet = original_disable_xnet
    
    def test_xnet_disabled(self):
        self._run_with_xnet_toggle(enable_xnet=False)
    
    def test_xnet_enabled(self):
        self._run_with_xnet_toggle(enable_xnet=True)
    
    def _run_all_types_cycle(self, expect_failure=False):
        # Test Model
        if "model" in self.repos:
            self._run_upload_download_cycle(RepoType.MODEL, self.repos["model"], "test_model_small.txt", 1, False,
                                            expect_failure)
            self._run_upload_download_cycle(RepoType.MODEL, self.repos["model"], "test_model_large.bin", 500, True,
                                            expect_failure)
        
        # Test Dataset
        if "dataset" in self.repos:
            self._run_upload_download_cycle(RepoType.DATASET, self.repos["dataset"], "test_dataset.txt", 1, False,
                                            expect_failure)
        
        # Test Space
        if "space" in self.repos:
            self._run_upload_download_cycle(RepoType.SPACE, self.repos["space"], "test_space.txt", 1, False,
                                            expect_failure)
    
    def _run_upload_download_cycle(self, repo_type, repo_id, filename, size_kb, binary, expect_failure=False):
        local_path, original_content = self._create_test_file(filename, size_kb, binary)
        remote_path = f"integration_test/{filename}"
        
        print(f"Uploading {repo_type} {repo_id} file {filename} ({size_kb}KB)...")
        # 1. Upload
        try:
            upload_files(
                repo_id=repo_id,
                repo_type=repo_type.value,
                repo_file=str(local_path),
                path_in_repo=remote_path,
                token=self.token,
                endpoint=self.endpoint,
                commit_message=f"Test upload {filename}"
            )
        except Exception as e:
            self.fail(f"Upload failed for {repo_type} {filename}: {e}")
        
        # 2. Download
        print(f"Downloading {repo_type} {repo_id} file {filename} ({size_kb}KB)...")
        download_dir = self.test_dir / f"download_{filename}_{random.randint(0, 10000)}"
        
        try:
            # Inspect repo_info before download to see if file is there
            from pycsghub.utils import get_repo_info
            info = get_repo_info(repo_id, repo_type=repo_type.value, token=self.token, endpoint=self.endpoint)
            print(f"DEBUG: Repo siblings: {[s.rfilename for s in info.siblings]}")
            
            download(
                repo_id=repo_id,
                repo_type=repo_type.value,
                local_dir=download_dir,
                token=self.token,
                endpoint=self.endpoint,
                allow_patterns=None,
                force_download=True
            )
        except Exception as e:
            self.fail(f"Download failed for {repo_type} {filename}: {e}")
        
        # 3. Verify Content
        downloaded_file = download_dir / remote_path
        
        # Retry logic: maybe it's in a cache folder if using hf_hub_download under the hood?
        # But download() calls snapshot_download which respects local_dir.
        
        if not downloaded_file.exists():
            print(f"DEBUG: File not found at {downloaded_file}. Listing download_dir content:")
            for root, dirs, files in os.walk(download_dir):
                print(f"  {root}/")
                for f in files:
                    print(f"    {f}")
            
            # Try finding it recursively
            found_files = list(download_dir.rglob(filename))
            if found_files:
                print(f"DEBUG: Found file at {found_files[0]}")
                downloaded_file = found_files[0]
        
        self.assertTrue(downloaded_file.exists(), f"Downloaded file not found at {downloaded_file}")
        
        with open(downloaded_file, 'rb') as f:
            downloaded_content = f.read()
        
        if binary:
            self.assertEqual(len(original_content), len(downloaded_content), "Binary content length mismatch")
            self.assertEqual(original_content, downloaded_content, "Binary content mismatch")
        else:
            self.assertEqual(original_content, downloaded_content, "Text content mismatch")

if __name__ == '__main__':
    unittest.main()
