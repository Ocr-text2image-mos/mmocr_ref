# Copyright (c) OpenMMLab. All rights reserved.
import torch
import torch.nn as nn

from mmocr.models.builder import LOSSES
from .ce_loss import CELoss


@LOSSES.register_module()
class ABILoss(nn.Module):
    """Implementation of ABINet multiloss that allows mixing different types of
    losses with weights.

    Args:
        enc_weight (float): The weight of encoder loss. Defaults to 1.0.
        dec_weight (float): The weight of decoder loss. Defaults to 1.0.
        fusion_weight (float): The weight of fuser (aligner) loss.
            Defaults to 1.0.
        ignore_index (int): Specifies a target label that is ignored and
            does not contribute to the input gradient.

    Returns:
        A dictionary whose key/value pairs are the losses of three modules.
    """

    def __init__(self,
                 enc_weight=1.0,
                 dec_weight=1.0,
                 fusion_weight=1.0,
                 ignore_index=-100,
                 **kwargs):
        assert isinstance(enc_weight, float) or isinstance(enc_weight, int)
        assert isinstance(dec_weight, float) or isinstance(dec_weight, int)
        assert isinstance(fusion_weight, float) or \
            isinstance(fusion_weight, int)
        super().__init__()
        self.ce = CELoss(
            reduction='mean',
            ignore_index=ignore_index,
            ignore_first_char=True)
        self.enc_weight = enc_weight
        self.dec_weight = dec_weight
        self.fusion_weight = fusion_weight

    def _loss_over_iters(self, outputs, targets_dict):
        """
        Args:
            outputs (list[Tensor]): Each tensor has shape (N, T, C) where N is
                the batch size, T is the sequence length and C is the number of
                classes.
            targets_dicts (dict): The dictionary with at least `padded_targets`
                defined.
        """
        iter_num = len(outputs)
        dec_outputs = torch.cat(outputs, dim=0)
        new_targets_dict = dict(
            padded_targets=targets_dict['padded_targets'].repeat(iter_num, 1))
        return self.ce(dec_outputs, new_targets_dict)

    def forward(self, outputs, targets_dict, img_metas=None):
        """
        Args:
            outputs (dict[dict[dict]]): A dictionary with at least one of
                `out_enc`, `out_decs` and `out_fusers` keys, each with `logits`
                of shape :math:`(N, T, C)`. In particular, `out_decs` is a list
                of dict representing the intermediate features computed at each
                language model iteration step.
            targets_dict (dict): Target dict with key `padded_targets`.

        Returns:
            dict: The loss dict with key `loss_visual`, `loss_lang` and
            `loss_fusion`.
        """
        enc_loss = self.ce(outputs['out_enc']['logits'],
                           targets_dict)['loss_ce'] * self.enc_weight
        dec_logits = [o['logits'] for o in outputs['out_decs']]
        dec_loss = self._loss_over_iters(
            dec_logits, targets_dict)['loss_ce'] * self.dec_weight
        fusion_logits = [o['logits'] for o in outputs['out_fusers']]
        fusion_loss = self._loss_over_iters(
            fusion_logits, targets_dict)['loss_ce'] * self.fusion_weight
        losses = dict(
            loss_visual=enc_loss, loss_lang=dec_loss, loss_fusion=fusion_loss)
        return losses
