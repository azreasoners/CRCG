# coding=utf-8
"""
Preprocesses a specific split of the CLEVRER dataset.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from absl import app
from absl import flags

import preprocess as preprocessor

FLAGS = flags.FLAGS

flags.DEFINE_string('dataset_path', None, 'Path to the JSON file containing the dataset.')

flags.DEFINE_string('save_path', None, 'Path to the directory where to save the files to.')

flags.mark_flag_as_required('save_path')

flags.register_validator('dataset_path', os.path.exists, 'Dataset not found.')


def main(argv):
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')

    dataset = preprocessor.get_dataset(FLAGS.dataset_path)
    preprocessor.write_dataset(dataset, FLAGS.save_path)
    token_vocab = preprocessor.get_token_vocab(FLAGS.save_path)
    preprocessor.write_token_vocab(token_vocab, FLAGS.save_path)


if __name__ == '__main__':
    app.run(main)
