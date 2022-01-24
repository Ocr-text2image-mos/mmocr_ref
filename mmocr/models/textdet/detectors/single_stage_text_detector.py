# Copyright (c) OpenMMLab. All rights reserved.

from mmocr.models.builder import DETECTORS
from mmocr.models.common.detectors import SingleStageDetector


@DETECTORS.register_module()
class SingleStageTextDetector(SingleStageDetector):
    """The class for implementing single stage text detector."""

    def __init__(self,
                 backbone,
                 neck,
                 bbox_head,
                 train_cfg=None,
                 test_cfg=None,
                 pretrained=None,
                 init_cfg=None):
        SingleStageDetector.__init__(self, backbone, neck, bbox_head,
                                     train_cfg, test_cfg, pretrained, init_cfg)

    def forward_train(self, img, img_metas, **kwargs):
        """
        Args:
            img (Tensor): Input images of shape (N, C, H, W).
                Typically these should be mean centered and std scaled.
            img_metas (list[dict]): A list of image info dict where each dict
                has: 'img_shape', 'scale_factor', 'flip', and may also contain
                'filename', 'ori_shape', 'pad_shape', and 'img_norm_cfg'.
                For details on the values of these keys, see
                :class:`mmdet.datasets.pipelines.Collect`.
        Returns:
            dict[str, Tensor]: A dictionary of loss components.
        """
        x = self.extract_feat(img)
        preds = self.bbox_head(x)
        losses = self.loss(preds, **kwargs)
        return losses

    def simple_test(self, img, img_metas, rescale=False):
        x = self.extract_feat(img)
        outs = self.bbox_head(x)
        results = self.postprocess(outs, img_metas)

        return results
