# Copyright (c) OpenMMLab. All rights reserved.
import argparse

from mmocr.utils import recog2lmdb


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('label_path', help='Path to label file')
    parser.add_argument('output', help='output lmdb path')
    parser.add_argument('--img-root', '-i', help='input imglist path')
    parser.add_argument(
        '--label-only',
        action='store_true',
        help='Only converter label to lmdb')
    parser.add_argument(
        '--label-format',
        '-f',
        default='txt',
        choices=['txt', 'jsonl'],
        help='The format of the label file, either txt or jsonl')
    parser.add_argument(
        '--batch_size',
        '-b',
        type=int,
        default=1000,
        help='processing batch size, default 10000')
    parser.add_argument(
        '--encoding',
        '-c',
        default='utf8',
        help='bytes coding scheme, default utf8')
    parser.add_argument(
        '--lmdb_map_size',
        '-m',
        type=int,
        default=109951162776,
        help='maximum size database may grow to , default 109951162776 bytes')
    opt = parser.parse_args()

    recog2lmdb(opt.img_root, opt.label_path, opt.output, opt.label_format,
               opt.label_only, opt.batch_size, opt.encoding, opt.lmdb_map_size)


if __name__ == '__main__':
    main()
