# from datasets.load import load_dataset
from pycsghub.repo_reader import load_dataset

dsPath = "wanghh2000/glue"
dsName = "mrpc"

# access_token = "your_access_token"
access_token = None

raw_datasets = load_dataset(path=dsPath, name=dsName, token=access_token)
print('raw_datasets', raw_datasets)
