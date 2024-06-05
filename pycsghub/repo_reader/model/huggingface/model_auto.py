import transformers
from pycsghub.snapshot_download import snapshot_download
from pycsghub.utils import get_token_to_send
import os
from pathlib import Path

@classmethod
def from_pretrained(cls, pretrained_model_name_or_path,
                    *model_args, **model_kwargs):
    # first step download model
    try:
        token = get_token_to_send(None)
    except Exception:
        token = ("f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4"
                 "f9b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf")
    if os.path.isdir(pretrained_model_name_or_path):
        path = Path(pretrained_model_name_or_path)
    else:
        path = Path(snapshot_download(pretrained_model_name_or_path, token=token))
    # second step load model
    model = cls.from_pretrained_cached(path, *model_args, **model_kwargs)
    return model



class_names = []

for i in transformers.__all__:
    try:
        if (hasattr(getattr(transformers, i), 'from_pretrained')
                and i.startswith('Auto')):
            class_names.append(i)
    except:
        pass
for i in class_names:
    try:
        locals()[i] = type(i, (), {
            'from_pretrained_cached': getattr(
                getattr(transformers, i),
                'from_pretrained'
            ),
            'from_pretrained': from_pretrained
        })
    except AttributeError as e:
        print(e)




