# optimizer
optimizer = dict(type='Adadelta', lr=0.1)
optimizer_config = dict(grad_clip=dict(max_norm=0.5))
# learning policy
lr_config = dict(policy='step', step=[8, 14, 16])
total_epochs = 18

checkpoint_config = dict(interval=1)
# yapf:disable
log_config = dict(
    interval=5,
    hooks=[
        dict(type='TextLoggerHook')

    ])
# yapf:enable
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None
resume_from = None
workflow = [('train', 1)]

img_norm_cfg = dict(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
test_ann_file = 'data/cluener/dev.json'
train_ann_file = 'data/cluener/train.json'
vocab_file = 'data/cluener/vocab.txt'
map_file = 'data/cluener/map_file.json'

loader = dict(
    type='HardDiskLoader',
    repeat=1,
    parser=dict(type='LineJsonParser', keys=['text', 'label']))

test_pipeline = [
    dict(
        type='Collect',
        keys=['img'],
        meta_keys=[
            'texts', 'img', 'labels', 'input_ids', 'attention_mask',
            'token_type_ids'
        ])
]

# label2id_convertor=dict(
#     type='SegConvertor', dict_type='DICT36', with_unknown=True, lower=True)



train_pipeline = [
    # dict(
    #     type='OCRSegTargets',
    #     label_convertor=label2id_convertor,
    #     box_type='char_quads'),
    dict(
        type='Collect',
        keys=['img'],
        meta_keys=[
            'texts', 'img', 'labels', 'input_ids', 'attention_mask',
            'token_type_ids'
        ]),

]
dataset_type = 'NerDataset'
img_prefix = ''

train = dict(
    type=dataset_type,
    img_prefix=img_prefix,
    ann_file=train_ann_file,
    loader=loader,
    pipeline=train_pipeline,
    test_mode=False,
    vocab_file=vocab_file,
    map_file=map_file,
    max_len=128)

test = dict(
    type=dataset_type,
    img_prefix=img_prefix,
    ann_file=test_ann_file,
    loader=loader,
    pipeline=test_pipeline,
    test_mode=True,
    vocab_file=vocab_file,
    map_file=map_file,
    max_len=128)
data = dict(
    samples_per_gpu=8,
    workers_per_gpu=2,
    train=dict(type='ConcatDataset', datasets=[train]),
    val=dict(type='ConcatDataset', datasets=[test]),
    test=dict(type='ConcatDataset', datasets=[test]))

evaluation = dict(interval=1, metric='acc')

model = dict(
    type='NerClassifier',
    encoder=dict(
        type='BertEncoder',
        num_hidden_layers=12,
        initializer_range=0.02,
        vocab_size=21128,
        hidden_size=768,
        max_position_embeddings=128,
        type_vocab_size=2,
        layer_norm_eps=1e-12,
        hidden_dropout_prob=0.1,
        output_attentions=False,
        output_hidden_states=False,
        num_attention_heads=12,
        attention_probs_dropout_prob=0.1,
        intermediate_size=3072,
        hidden_act='gelu_new'),
    decoder=dict(
        type='FCDecoder',
        num_labels=34,
        hidden_dropout_prob=0.1,
        hidden_size=768),
    loss=dict(type='NerLoss', num_labels=34, loss_type='focal'))

test_cfg = None
