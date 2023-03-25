# Copyright (c) OpenMMLab. All rights reserved.
from typing import Dict, List, Optional

from mmocr.registry import CFG_GENERATORS
from .base import BaseDatasetConfigGenerator


@CFG_GENERATORS.register_module()
class SERConfigGenerator(BaseDatasetConfigGenerator):
    """Text detection config generator.

    Args:
        data_root (str): The root path of the dataset.
        dataset_name (str): The name of the dataset.
        overwrite_cfg (bool): Whether to overwrite the dataset config file if
            it already exists. If False, config generator will not generate new
            config for datasets whose configs are already in base.
        train_anns (List[Dict], optional): A list of train annotation files
            to appear in the base configs. Defaults to
            ``[dict(file='ser_train.json', dataset_postfix='')]``.
            Each element is typically a dict with the following fields:
            - ann_file (str): The path to the annotation file relative to
              data_root.
            - dataset_postfix (str, optional): Affects the postfix of the
              resulting variable in the generated config. If specified, the
              dataset variable will be named in the form of
              ``{dataset_name}_{dataset_postfix}_{task}_{split}``. Defaults to
              None.
        val_anns (List[Dict], optional): A list of val annotation files
            to appear in the base configs, similar to ``train_anns``. Defaults
            to [].
        test_anns (List[Dict], optional): A list of test annotation files
            to appear in the base configs, similar to ``train_anns``. Defaults
            to ``[dict(file='ser_test.json')]``.
        config_path (str): Path to the configs. Defaults to 'configs/'.
    """

    def __init__(
        self,
        data_root: str,
        dataset_name: str,
        overwrite_cfg: bool = False,
        train_anns: Optional[List[Dict]] = [
            dict(ann_file='ser_train.json', dataset_postfix='')
        ],
        val_anns: Optional[List[Dict]] = [],
        test_anns: Optional[List[Dict]] = [
            dict(ann_file='ser_test.json', dataset_postfix='')
        ],
        config_path: str = 'configs/',
    ) -> None:
        if '/' in dataset_name:
            dataset_name = '_'.join(dataset_name.split('/'))
        super().__init__(
            data_root=data_root,
            task='ser',
            overwrite_cfg=overwrite_cfg,
            dataset_name=dataset_name,
            train_anns=train_anns,
            val_anns=val_anns,
            test_anns=test_anns,
            config_path=config_path,
        )

    def _gen_dataset_config(self) -> str:
        """Generate a full dataset config based on the annotation file
        dictionary.

        Args:
            ann_dict (dict[str, dict(str, str)]): A nested dictionary that maps
                a config variable name (such as icdar2015_textrecog_train) to
                its corresponding annotation information dict. Each dict
                contains following keys:
                - ann_file (str): The path to the annotation file relative to
                  data_root.
                - dataset_postfix (str, optional): Affects the postfix of the
                  resulting variable in the generated config. If specified, the
                  dataset variable will be named in the form of
                  ``{dataset_name}_{dataset_postfix}_{task}_{split}``. Defaults
                  to None.
                - split (str): The split the annotation belongs to. Usually
                  it can be 'train', 'val' and 'test'.

        Returns:
            str: The generated dataset config.
        """
        cfg = ''
        for key_name, ann_dict in self.anns.items():
            cfg += f'\n{key_name} = dict(\n'
            cfg += '    type=\'SERDataset\',\n'
            cfg += '    data_root=' + f'{self.dataset_name}_{self.task}_data_root,\n'  # noqa: E501
            cfg += f'    ann_file=\'{ann_dict["ann_file"]}\',\n'
            if ann_dict['split'] == 'train':
                cfg += '    filter_cfg=dict(filter_empty_gt=True, min_size=32),\n'  # noqa: E501
            elif ann_dict['split'] in ['test', 'val']:
                cfg += '    test_mode=True,\n'
            cfg += '    pipeline=None)\n'
        return cfg
