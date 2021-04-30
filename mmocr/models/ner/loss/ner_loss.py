import torch
from torch import nn
from torch.nn import CrossEntropyLoss

from mmdet.models.builder import LOSSES
from mmocr.models.common.losses.focal_loss import FocalLoss
from .label_smoothing import LabelSmoothingCrossEntropy


@LOSSES.register_module()
class NerLoss(nn.Module):
    """The implementation the loss of named entity recognizier."""

    def __init__(self, num_labels=None, loss_type=None, **kwargs):
        super().__init__()
        self.num_labels = num_labels
        self.loss_type = loss_type

    def forward(self, logits, img_metas, device):
        '''Loss forword.
        Args:
            logits: [N, C]
            img_metas (dict): A dict containing the following keys:
                    - img (list): This parameter is reserved and not used here.
                    - labels (list): []*max_len
                    - texts (list): []*max_len
                    - input_ids (list): []*max_len
                    - attention_mask (list): []*max_len
                    - token_type_ids (list): []*max_len
            device (str): cuda or cpu
        '''
        labels = []
        attention_masks = []
        for i,_ in enumerate(img_metas):
            label = torch.tensor(img_metas[i]['labels']).to(device)
            attention_mask = torch.tensor(
                img_metas[i]['attention_mask']).to(device)
            labels.append(label)
            attention_masks.append(attention_mask)
        labels = torch.stack(labels, 0)
        attention_mask = torch.stack(attention_masks, 0)

        assert self.loss_type in ['lsr', 'focal', 'ce']
        if self.loss_type == 'lsr':
            loss_fct = LabelSmoothingCrossEntropy(ignore_index=0)
        elif self.loss_type == 'focal':

            loss_fct = FocalLoss(ignore_index=0)
        else:
            loss_fct = CrossEntropyLoss(ignore_index=0)
        # Only keep active parts of the loss
        if attention_mask is not None:
            active_loss = attention_mask.view(-1) == 1
            active_logits = logits.view(-1, self.num_labels)[active_loss]
            active_labels = labels.view(-1)[active_loss]
            loss = loss_fct(active_logits, active_labels)
        else:
            loss = loss_fct(
                logits.view(-1, self.num_labels), labels.view(-1))
        return loss
