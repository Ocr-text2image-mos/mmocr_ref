_base_ = ['textdet.py']

_base_.train_preparer.obtainer = None
_base_.train_preparer.gatherer.img_dir = 'textdet_imgs/train'
_base_.train_preparer.packer.type = 'TextRecogCropPacker'

config_generator = dict(type='TextRecogConfigGenerator')
