import argparse
import json
from functools import partial

import mmcv

from mmocr.utils import list_from_file, list_to_file


def convert(closeset_line, merge_bg_others=False):
    closeset_obj = json.loads(closeset_line)
    openset_obj = {
        'file_name': closeset_obj['file_name'],
        'height': closeset_obj['height'],
        'width': closeset_obj['width'],
        'annotations': []
    }

    edge_idx = 1
    label_to_edge = {}
    for anno in closeset_obj['annotations']:
        label = anno['label']
        if label == 0:
            anno['edge'] = edge_idx
            edge_idx += 1
        elif label == 25:
            if merge_bg_others:
                anno['label'] = 0
            else:
                anno['label'] = 3
            anno['edge'] = edge_idx
            edge_idx += 1
        else:
            edge = label_to_edge.get(label, None)
            if edge is not None:
                anno['edge'] = edge
                if label % 2 == 0:
                    anno['label'] = 1
                else:
                    anno['label'] = 2
            else:
                if label % 2 == 0:
                    edge_minus_1 = label_to_edge.get(label - 1, None)
                    if edge_minus_1 is not None:
                        anno['edge'] = edge_minus_1
                    else:
                        anno['edge'] = edge_idx
                        edge_idx += 1
                    anno['label'] = 1
                    label_to_edge[label] = anno['edge']
                else:
                    edge_plus_1 = label_to_edge.get(label + 1, None)
                    if edge_plus_1 is not None:
                        anno['edge'] = edge_plus_1
                    else:
                        anno['edge'] = edge_idx
                        edge_idx += 1
                    anno['label'] = 2
                    label_to_edge[label] = anno['edge']

    openset_obj['annotations'] = closeset_obj['annotations']

    return json.dumps(openset_obj, ensure_ascii=False)


def process(closeset_file, openset_file, merge_bg_others=False, n_proc=10):
    closeset_lines = list_from_file(closeset_file)

    convert_func = partial(convert, merge_bg_others=merge_bg_others)

    openset_lines = mmcv.track_parallel_progress(
        convert_func, closeset_lines, nproc=n_proc)

    list_to_file(openset_file, openset_lines)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', help='Annotation file for closeset.')
    parser.add_argument('out_file', help='Annotation file for openset.')
    parser.add_argument(
        '--merge',
        action='store_true',
        help='Merge "background" and "others" in closeset '
        'to one class in openset.')
    parser.add_argument(
        '--n_proc', type=int, default=10, help='Number of process.')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    process(args.in_file, args.out_file, args.merge, args.n_proc)

    print('finish')


if __name__ == '__main__':
    main()
