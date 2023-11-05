# coding=utf-8
"""
Utils for preprocessing the CLEVRER dataset.
"""

import collections
import json
import os
import string
from typing import Any, Dict, List, Tuple

from absl import logging

from tensorflow.compat.v1.io import gfile


def load_dataset(path):
    logging.info(f'Reading json from {path} into memory...')
    with gfile.GFile(path) as f:
        raw_data = json.load(f)
    filtered_data = list()
    for data in raw_data:
        for question in data['questions']:
            temp = dict()
            temp['question'] = question['question']
            temp['program'] = question['program'] if 'program' in question else []
            filtered_data.append(temp)
            if 'choices' in question:
                for choice in question['choices']:
                    temp = dict()
                    temp['question'] = choice['choice']
                    temp['program'] = choice['program'] if 'program' in choice else []
                    filtered_data.append(temp)
    logging.info(f'Successfully loaded json data from {path} into memory.')
    return filtered_data


def tokenize_punctuation(text):
    text = map(lambda c: f' {c} ' if c in string.punctuation else c, text)
    return ' '.join(''.join(text).split())


def get_encode_decode_pair(sample):
    # Apply some simple preprocessing on the tokenizaton, which improves the
    # performance of the models significantly.
    encode_text = tokenize_punctuation(sample['question'])
    decode_text = ' '.join(sample['program'])
    return (encode_text.lower(), decode_text.lower())


def get_dataset(path):
    dataset = collections.defaultdict(list)
    split_names = ['train', 'validation', 'test']
    for split_name in split_names:
        samples = load_dataset(os.path.join(path, (split_name + '.json')))
        for sample in samples:
            dataset[split_name].append(get_encode_decode_pair(sample))
    size_str = ', '.join(f'{s}={len(dataset[s])}' for s in split_names)
    logging.info(f'Finished retrieving splits. Size: {size_str}')
    return dataset


def write_dataset(dataset, save_path):
    """Saves the given dataset into the given location."""
    if not dataset:
        logging.info('No dataset to write.')
        return
    logging.info(f'Writing dataset to {save_path}')
    for split_name, list_of_input_output_pairs in dataset.items():
        folder_name = os.path.join(save_path, split_name)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        encode_name = os.path.join(folder_name, f'{split_name}_encode.txt')
        decode_name = os.path.join(folder_name, f'{split_name}_decode.txt')
        if split_name == 'test':
            with gfile.GFile(encode_name, 'w') as encode_f:
                for pair in list_of_input_output_pairs:
                    encode_f.write(pair[0] + '\n')
        else:
            with gfile.GFile(encode_name, 'w') as encode_f, gfile.GFile(decode_name, 'w') as decode_f:
                for pair in list_of_input_output_pairs:
                    encode_f.write(pair[0] + '\n')
                    decode_f.write(pair[1] + '\n')
    logging.info(f'Dataset written to {save_path}')


def write_token_vocab(words,
                      save_path,
                      problem='clevrer'):
    """"Writes token vocabulary from @words to @save_path."""
    # Sort tokens by frequency and then lexically to break ties.
    words_with_counts = words.most_common()
    words_with_counts.sort(key=lambda x: (x[1], x[0]), reverse=True)
    vocab_path = os.path.join(save_path, f'vocab.{problem}.tokens')

    with gfile.GFile(vocab_path, 'w') as f:
        # Tensor2tensor needs these additional tokens.
        f.write('<pad>\n<EOS>\n<OOV>\n')
        for word, _ in words_with_counts:
            f.write(f'{word}\n')
    logging.info(f'Token vocabulary written to {vocab_path} ({len(words)} distinct tokens).')


def get_lines(path, filename):
    with gfile.GFile(os.path.join(path, 'train', filename)) as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return lines


def get_token_vocab(path):
    words = collections.Counter()
    lines = get_lines(path, 'train_encode.txt')
    lines.extend(get_lines(path, 'train_decode.txt'))
    for line in lines:
        words.update(line.split(' '))
    return words
