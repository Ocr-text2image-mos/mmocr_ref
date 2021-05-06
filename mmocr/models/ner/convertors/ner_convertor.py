from mmocr.models.builder import CONVERTORS


@CONVERTORS.register_module()
class NerConvertor:
    """Convert between text, index and tensor for NER pipeline.

    Args:
        annotation_type (str): BIO((B-begin, I-inside, O-outside)),
                    BIOES(B-begin，I-inside，O-outside，E-end，S-single)
        vocab_file (str): File to convert words to ids.
        map_file (str): File to get label2id_dict and word2ids_dict.
    """
    unknown_id = 100
    start_id = 101
    end_id = 102

    def __init__(self,
                 annotation_type='bio',
                 vocab_file=None,
                 categories=None,
                 max_len=None):
        self.annotation_type = annotation_type
        self.categories = categories
        self.word2ids = {}
        self.max_len = max_len
        assert self.max_len > 2
        assert self.annotation_type in ['bio', 'bioes']

        lines = open(vocab_file, encoding='utf-8').readlines()
        for i in range(len(lines)):
            self.word2ids.update({lines[i].rstrip(): i})

        if self.annotation_type == 'bio':
            self.label2id_dict, self.id2label, self.ignore_id = \
                self._generate_labelid_dict()
        elif self.annotation_type == 'bioes':
            raise NotImplementedError('Bioes format is not surpported now!')

        assert self.ignore_id is not None
        assert self.id2label is not None
        self.num_labels = len(self.id2label)

    def _generate_labelid_dict(self):
        """Generate a dictionary that maps input to ID and ID to output."""
        num_classes = len(self.categories)
        label2id_dict = {}
        ignore_id = 2 * num_classes + 1
        id2label_dict = {
            0: 'X',
            ignore_id: 'O',
            2 * num_classes + 2: '[START]',
            2 * num_classes + 3: '[END]'
        }

        for index, category in enumerate(self.categories):
            start_label = index + 1
            end_label = index + 1 + num_classes
            label2id_dict.update({category: [start_label, end_label]})
            id2label_dict.update({start_label: 'B-' + category})
            id2label_dict.update({end_label: 'I-' + category})

        return label2id_dict, id2label_dict, ignore_id

    def convert_text2id(self, text):
        """Convert characters to ids.

        If the input is uppercase,
            convert to lowercase first.
        Args:
            text (list[char]): Annotations of one paragraph.
        Returns:
            input_ids (list): Corresponding IDs after conversion.
        """
        ids = []
        for word in text.lower():
            if word in self.word2ids:
                ids.append(self.word2ids[word])
            else:
                ids.append(self.unknown_id)
        # Text that exceeds the maximum length is truncated.
        valid_len = min(len(text), self.max_len)
        input_ids = [0] * self.max_len
        input_ids[0] = self.start_id
        for i in range(1, valid_len + 1):
            input_ids[i] = ids[i - 1]
        input_ids[i + 1] = self.end_id

        return input_ids

    def conver_entity2label(self, label, text_len):
        """Convert labeled entities to ids.

        Args:
            label (dict): Labels of entities.
            text_len (int): The length of input text.
        Returns:
            labels (list): Label ids of an input text.
        """
        labels = [0] * self.max_len
        for j in range(min(text_len + 2, self.max_len)):
            labels[j] = self.ignore_id
        categorys = label
        for key in categorys:
            for text in categorys[key]:
                for place in categorys[key][text]:
                    # Remove the label position beyond the maximum length.
                    if place[0] + 1 < len(labels):
                        labels[place[0] + 1] = self.label2id_dict[key][0]
                        for i in range(place[0] + 1, place[1] + 1):
                            if i + 1 < len(labels):
                                labels[i + 1] = self.label2id_dict[key][1]
        return labels

    def convert_pred2entities(self, preds):
        """Gets entities from preds.

        Args:
            preds (list): Sequence of preds.
        Returns:
            pred_entities (list): List of [[[entity_type,
                                entity_start, entity_end]]].
        """

        pred_entities = []
        assert isinstance(preds, list)
        for pred in preds:
            entities = []
            entity = [-1, -1, -1]
            results = pred[1:]
            for index, tag in enumerate(results):
                if not isinstance(tag, str):
                    tag = self.id2label[tag]
                if self.annotation_type == 'bio':
                    if tag.startswith('B-'):
                        if entity[2] != -1:
                            entities.append(entity)
                        entity = [-1, -1, -1]
                        entity[1] = index
                        entity[0] = tag.split('-')[1]
                        entity[2] = index
                        if index == len(results) - 1:
                            entities.append(entity)
                    elif tag.startswith('I-') and entity[1] != -1:
                        _type = tag.split('-')[1]
                        if _type == entity[0]:
                            entity[2] = index

                        if index == len(results) - 1:
                            entities.append(entity)
                    else:
                        if entity[2] != -1:
                            entities.append(entity)
                        entity = [-1, -1, -1]
                else:
                    raise NotImplementedError(
                        'The data format is not surpported now!')
            pred_entities.append(entities)
        return pred_entities
