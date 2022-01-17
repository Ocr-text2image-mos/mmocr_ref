# Copyright (c) OpenMMLab. All rights reserved.
from functools import partial

import numpy as np
import torch.nn as nn

# from mmocr.utils import check_argument


class BasePostprocessor:

    def __init__(self, text_repr_type='poly'):
        assert text_repr_type in ['poly', 'quad'
                                  ], f'Invalid text repr type {text_repr_type}'

        self.text_repr_type = text_repr_type

    def is_valid_instance(self, area, confidence, area_thresh,
                          confidence_thresh):

        return bool(area >= area_thresh and confidence > confidence_thresh)


class BaseTextDetPostProcessor(nn.Module):
    """the results must has the same format as.

    #polygon'size is batch_size * poly_num_per_img * point_num
    dict(polygon=list[list[list[float]]],
         polygon_score=list[list[float]])
    """

    def __init__(self, text_repr_type='poly'):
        assert text_repr_type in ['poly', 'quad']

    def __call__(self,
                 pred,
                 property=['polygon'],
                 scale_factor=None,
                 rescale=False,
                 filter_and_location=True,
                 reconstruct=True,
                 extra_property=None,
                 rescale_extra_property=False):
        if type(pred) is not dict:
            results = dict(detect_output=pred)
        if filter_and_location:
            results = self.filter_and_location(pred)

        if reconstruct:
            results = self.reconstruct_text_instance(results)

        if rescale:
            results = self.rescale_results(results, scale_factor, property)

        if rescale_extra_property and extra_property is not None:
            for key in extra_property:
                assert key in results
            results = self.rescale_results(results, scale_factor,
                                           extra_property)
        return results

    def rescale_results(self, results, scale_factor, property=None):
        """Rescale results via scale_factor."""
        assert isinstance(scale_factor, np.ndarray)
        assert scale_factor.shape[0] == 4
        for key in property:
            _rescale_single_result = partial(
                self._rescale_single_result, scale_factor=scale_factor)
            results[key] = list(map(_rescale_single_result, results[key]))
        return results

    def _rescale_single_result(self, polygon, scale_factor):
        point_num = len(polygon)
        assert point_num % 2 == 0
        polygon = (np.array(polygon) *
                   (np.tile(scale_factor[:2], int(point_num / 2)).reshape(
                       1, -1))).flatten().tolist()
        return polygon

    def filter_and_location(self, results):
        return results

    def reconstruct_text_instance(self, results):
        return results
