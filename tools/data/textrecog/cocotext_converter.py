# Copyright (c) OpenMMLab. All rights reserved.
import argparse
import json
import math
import os
import os.path as osp
from functools import partial

import mmcv

from mmocr.utils.fileio import list_to_file


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate training and validation set of COCO Text v2 ')
    parser.add_argument('root_path', help='Root dir path of COCO Text v2')
    parser.add_argument(
        '--nproc', default=1, type=int, help='Number of processes')
    parser.add_argument(
        '--format',
        default='jsonl',
        help='Use jsonl or string to format annotations',
        choices=['jsonl', 'txt'])
    args = parser.parse_args()
    return args


def process_img(args, src_image_root, dst_image_root, format):
    # Dirty hack for multi-processing
    img_idx, img_info, anns = args
    src_img = mmcv.imread(osp.join(src_image_root, img_info['file_name']))
    labels = []
    for ann_idx, ann in enumerate(anns):
        text_label = ann['utf8_string']

        # Ignore illegible or non-English words
        if ann['language'] == 'not english':
            continue
        if ann['legibility'] == 'illegible':
            continue

        x, y, w, h = ann['bbox']
        x, y = max(0, math.floor(x)), max(0, math.floor(y))
        w, h = math.ceil(w), math.ceil(h)
        dst_img = src_img[y:y + h, x:x + w]
        dst_img_name = f'img_{img_idx}_{ann_idx}.jpg'
        dst_img_path = osp.join(dst_image_root, dst_img_name)
        mmcv.imwrite(dst_img, dst_img_path)
        if format == 'txt':
            labels.append(f'{osp.basename(dst_image_root)}/{dst_img_name}'
                          f' {text_label}')
        elif format == 'jsonl':
            labels.append(
                json.dumps({
                    'filename':
                    f'{osp.basename(dst_image_root)}/{dst_img_name}',
                    'text': text_label
                }))
        else:
            raise NotImplementedError
    return labels


def convert_cocotext(root_path, split, format, nproc, img_start_idx=0):
    """Collect the annotation information and crop the images.

    The annotation format is as the following:
    {
        'anns':{
            '45346':{
                'mask': [468.9,286.7,468.9,295.2,493.0,295.8,493.0,287.2],
                'class': 'machine printed',
                'bbox': [468.9, 286.7, 24.1, 9.1], # x, y, w, h
                'image_id': 217925,
                'id': 45346,
                'language': 'english', # 'english' or 'not english'
                'area': 206.06,
                'utf8_string': 'New',
                'legibility': 'legible', # 'legible' or 'illegible'
            },
            ...
        }
        'imgs':{
            '540965':{
                'id': 540965,
                'set': 'train', # 'train' or 'val'
                'width': 640,
                'height': 360,
                'file_name': 'COCO_train2014_000000540965.jpg'
            },
            ...
        }
        'imgToAnns':{
            '540965': [],
            '260932': [63993, 63994, 63995, 63996, 63997, 63998, 63999],
            ...
        }
    }

    Args:
        root_path (str): Root path to the dataset
        src_image_path (str): Path to the source images
        split (str): Dataset split, which should be 'train' or 'val'
        format (str): Annotation format, should be either 'jsonl' or 'txt'
        nproc (int): Number of processes
        img_start_idx (int): Index of start image

    Returns:
        img_info (dict): The dict of the img and annotation information
    """

    annotation_path = osp.join(root_path, 'annotations/cocotext.v2.json')
    if not osp.exists(annotation_path):
        raise Exception(
            f'{annotation_path} not exists, please check and try again.')

    annotation = mmcv.load(annotation_path)
    # outputs
    dst_label_file = osp.join(root_path, f'{split}_label.{format}')
    dst_image_root = osp.join(root_path, 'crops', split)
    src_image_root = osp.join(root_path, 'imgs')
    os.makedirs(dst_image_root, exist_ok=True)

    process_img_with_path = partial(
        process_img,
        src_image_root=src_image_root,
        dst_image_root=dst_image_root,
        format=format)
    tasks = []
    for img_idx, img_info in enumerate(annotation['imgs'].values()):
        if img_info['set'] == split:
            ann_ids = annotation['imgToAnns'][str(img_info['id'])]
            anns = [annotation['anns'][str(ann_id)] for ann_id in ann_ids]
            tasks.append((img_idx + img_start_idx, img_info, anns))
    labels_list = mmcv.track_parallel_progress(
        process_img_with_path, tasks, keep_order=True, nproc=nproc)
    final_labels = []
    for label_list in labels_list:
        final_labels += label_list
    list_to_file(dst_label_file, final_labels)

    return len(annotation['imgs'])


def main():
    args = parse_args()
    root_path = args.root_path
    print('Processing training set...')
    num_train_imgs = convert_cocotext(
        root_path=root_path,
        split='train',
        format=args.format,
        nproc=args.nproc)
    print('Processing validation set...')
    convert_cocotext(
        root_path=root_path,
        split='val',
        format=args.format,
        nproc=args.nproc,
        img_start_idx=num_train_imgs)
    print('Finish')


if __name__ == '__main__':
    main()
