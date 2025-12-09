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
from pycsghub.cli import download, upload
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
                # Attempt to clean up common JSON syntax errors like trailing commas
                import re
                cleaned_json = re.sub(r',\s*\]', ']', cls.repos_json)
                cleaned_json = re.sub(r',\s*\}', '}', cleaned_json)
                cls.repos = json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in CSGHUB_TEST_REPOS: {e}")
                print(f"Raw content: {cls.repos_json}")
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
    
    def test_from_env_config(self):
        if not isinstance(self.repos, list):
             print("Skipping test_from_env_config: CSGHUB_TEST_REPOS is not a list")
             return

        print(f"\nLoaded {len(self.repos)} repos from env for testing.")
        
        for repo_config in self.repos:
            repo_id = repo_config.get("repo_id")
            type_str = repo_config.get("type")
            size_kb = repo_config.get("size_kb")
            disable_xnet = repo_config.get("disable_xnet", "false")
            
            if not repo_id or not type_str:
                print(f"Skipping invalid config: {repo_config}")
                continue
            
            size_kb = size_kb or 100
            # Map type string to RepoType enum
            unique_suffix = f"{size_kb}kb" 
            if type_str == "model":
                repo_type = RepoType.MODEL
                filename = f"test_model_small_{unique_suffix}.bin"
            elif type_str == "dataset":
                repo_type = RepoType.DATASET
                filename = f"test_dataset_{unique_suffix}.txt"
            elif type_str == "space":
                repo_type = RepoType.SPACE
                filename = f"test_space_{unique_suffix}.txt"
            else:
                print(f"Unknown repo type: {type_str}")
                continue
            

            # Toggle XNet
            original_disable_xnet = pycsghub.utils.disable_xnet()
            os.environ["CSGHUB_DISABLE_XNET"] = str(disable_xnet)
            print(f"\n>>> Testing {repo_id} ({type_str}) with XNet {'Disabled' if pycsghub.utils.disable_xnet() else 'Enabled'}")

            try:
                self._run_upload_download_cycle(
                    repo_type=repo_type, 
                    repo_id=repo_id, 
                    filename=filename, 
                    size_kb=size_kb, 
                    binary=False
                )
            finally:
                os.environ["CSGHUB_DISABLE_XNET"] = str(original_disable_xnet)
    
    def _run_upload_download_cycle(self, repo_type, repo_id, filename, size_kb, binary, expect_failure=False):
        local_path, original_content = self._create_test_file(filename, size_kb, binary)
        remote_path = f"integration_test/{filename}"
        
        print(f"Uploading {repo_type} {repo_id} file {filename} ({size_kb}KB)...")
        # 1. Upload
        try:
            upload(
                repo_id=repo_id,
                repo_type=repo_type,
                local_path=str(local_path),
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
            download(
                repo_id=repo_id,
                filenames=[remote_path], # CLI uses filenames list, mapped to allow_patterns or single file
                repo_type=repo_type,
                local_dir=str(download_dir),
                token=self.token,
                endpoint=self.endpoint,
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

        print(f"Downloading entire repo: {repo_type} {repo_id} ...")
        download(
            repo_id=repo_id,
            repo_type=repo_type,
            local_dir=str(download_dir),
            token=self.token,
            endpoint=self.endpoint,
            force_download=True 
        )     

if __name__ == '__main__':
    unittest.main()
