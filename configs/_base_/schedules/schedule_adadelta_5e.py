# optimizer
optimizer = dict(type='Adadelta', lr=1.0)
optimizer_config = dict(grad_clip=None)
# learning policy
lr_config = dict(policy='step', step=[3, 4])
total_epochs = 5
