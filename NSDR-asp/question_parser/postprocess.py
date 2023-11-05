# coding=utf-8
"""
Utils for postprocessing the CLEVRER dataset.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import json

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('inferred_path', None, 'Path to the test_inferred.txt.')
flags.DEFINE_string('input_path', None, 'Path to the test.json.')
flags.DEFINE_string('output_path', None, 'Path to the directory where to save the files to.')

flags.mark_flags_as_required(['inferred_path', 'input_path', 'output_path'])


def main(argv):

    with open(FLAGS.input_path) as fr:
        raw_data = json.load(fr)
    with open(FLAGS.inferred_path) as fr:
        decode_lines = [line.strip() for line in fr]

    for data in raw_data:
        for question in data['questions']:
            question['program'] = decode_lines.pop(0)
            if 'choices' in question:
                for choice in question['choices']:
                    choice['program'] = decode_lines.pop(0)

    with open(FLAGS.output_path, 'w') as fw:
        json.dump(raw_data, fw)


if __name__ == '__main__':
    app.run(main)
