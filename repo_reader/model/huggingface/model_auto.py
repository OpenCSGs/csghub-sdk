from abc import ABC, abstractmethod
import transformers

class _BaseAutoModelClass(ABC):

    @abstractmethod
    def from_pretrained(self, pretrained_model_name_or_path: str):
        raise NotImplementedError

    @abstractmethod
    def from_config(self, config_path: str):
        raise NotImplementedError


class_names = []

for i in transformers.__all__:
    try:
        if (hasattr(getattr(transformers, i), 'from_pretrained')
                and i.startswith('Auto')):
            class_names.append(i)
    except:
        pass
for i in class_names:
    locals()[i] = type(i, (
        _BaseAutoModelClass,
    ), {})


