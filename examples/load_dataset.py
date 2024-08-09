
# export HF_ENDPOINT=http://127.0.0.1:8080/hf
# export CSGHUB_DOMAIN=http://127.0.0.1:8080

# export HF_ENDPOINT="https://hub-stg.opencsg.com/hf"
# export CSGHUB_DOMAIN="https://hub-stg.opencsg.com"

from datasets.load import load_dataset
# from pycsghub.repo_reader import load_dataset

# dsPath = "nyu-mll/glue"
# dsName = "mrpc"

# dsPath = "wanghh2003/glue" # public
# dsName = "mrpc"

# dsPath = "wanghh2003/glue1"
# dsName = "mrpc"

# dsPath = "wanghh2003/datasset1"
# dsPath = "wanghh2003/myds1"
# dsName = None

dsPath = "wanghh2003/glue1"
dsName = "mrpc"

# access_token = "f9fd525960ed86c4024d7f73f955df3c8b416434"
access_token = None

raw_datasets = load_dataset(path=dsPath, name=dsName, token=access_token)
print('raw_datasets', raw_datasets)
