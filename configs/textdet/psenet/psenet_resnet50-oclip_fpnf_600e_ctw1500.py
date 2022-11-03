_base_ = [
    'psenet_resnet50_fpnf_600e_ctw1500.py',
]

load_from = None

_base_.model.backbone = dict(
    type='CLIPResNet',
    init_cfg=dict(
        type='Pretrained',
        checkpoint=
        'https://download.openmmlab.com/mmocr/backbone/resnet50-oclip-7ba0c533.pth'  # noqa
    ))
