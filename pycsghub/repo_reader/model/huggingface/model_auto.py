import transformers
from pycsghub.snapshot_download import snapshot_download

@classmethod
def from_pretrained(cls, pretrained_model_name_or_path, *model_args, **model_kwargs):
    # first step download model
    path = snapshot_download(pretrained_model_name_or_path)
    # second step load model
    model = cls.from_pretrained(path, *model_args, **model_kwargs)
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
            'from_pretrained_cache': getattr(
                getattr(transformers, i),
                'from_pretrained'
            ),
            'from_pretrained': from_pretrained
        })
    except AttributeError as e:
        print(e)




