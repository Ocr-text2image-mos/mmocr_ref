from mmdet.datasets.builder import PIPELINES
from mmocr.models.builder import build_convertor


@PIPELINES.register_module()
class NerTransform:
    """Ner transform ."""

    def __init__(self, label_convertor=None, max_len=None):
        assert label_convertor is not None
        self.label_convertor = build_convertor(label_convertor)
        self.max_len = max_len

    def __call__(self, results):
        texts = results['text']
        input_ids = self.label_convertor.convert_text2id(texts)
        labels = self.label_convertor.conver_entity2label(
            results['label'], len(texts))

        attention_mask = [0] * self.max_len
        token_type_ids = [0] * self.max_len
        # The beginning and end IDs are added to the ID,
        # so the mask length is increased by 2
        for i in range(len(texts) + 2):
            attention_mask[i] = 1
        ans = dict(
            img=input_ids,
            labels=labels,
            texts=texts,
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids)
        return ans
