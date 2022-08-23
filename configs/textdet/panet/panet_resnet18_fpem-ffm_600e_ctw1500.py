_base_ = [
    '../../_base_/det_datasets/ctw1500.py',
    '../../_base_/textdet_default_runtime.py',
    '../../_base_/schedules/schedule_adam_600e.py',
    '_base_panet_resnet18_fpem-ffm.py',
]

model = dict(det_head=dict(module_loss=dict(shrink_ratio=(1, 0.7))))

default_hooks = dict(checkpoint=dict(type='CheckpointHook', interval=20), )

file_client_args = dict(backend='disk')
train_pipeline = [
    dict(
        type='LoadImageFromFile',
        file_client_args=file_client_args,
        color_type='color_ignore_orientation'),
    dict(
        type='LoadOCRAnnotations',
        with_polygon=True,
        with_bbox=True,
        with_label=True,
    ),
    dict(type='ShortScaleAspectJitter', short_size=640, scale_divisor=32),
    dict(type='RandomFlip', prob=0.5, direction='horizontal'),
    dict(type='RandomRotate', max_angle=10),
    dict(type='TextDetRandomCrop', target_size=(640, 640)),
    dict(type='Pad', size=(640, 640)),
    dict(
        type='TorchVisionWrapper',
        op='ColorJitter',
        brightness=32.0 / 255,
        saturation=0.5),
    dict(
        type='PackTextDetInputs',
        meta_keys=('img_path', 'ori_shape', 'img_shape', 'scale_factor'))
]

test_pipeline = [
    dict(
        type='LoadImageFromFile',
        file_client_args=file_client_args,
        color_type='color_ignore_orientation'),
    # TODO Replace with mmcv.RescaleToShort when it's ready
    dict(
        type='ShortScaleAspectJitter',
        short_size=640,
        scale_divisor=1,
        ratio_range=(1.0, 1.0),
        aspect_ratio_range=(1.0, 1.0)),
    dict(
        type='LoadOCRAnnotations',
        with_polygon=True,
        with_bbox=True,
        with_label=True),
    dict(
        type='PackTextDetInputs',
        meta_keys=('img_path', 'ori_shape', 'img_shape', 'scale_factor'))
]

# dataset settings
ctw_det_train = _base_.ctw_det_train
ctw_det_test = _base_.ctw_det_test
# pipeline settings
ctw_det_train.pipeline = train_pipeline
ctw_det_test.pipeline = test_pipeline

train_dataloader = dict(
    batch_size=16,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    dataset=ctw_det_train)
val_dataloader = dict(
    batch_size=1,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=ctw_det_test)
test_dataloader = val_dataloader
