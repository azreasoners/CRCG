import copy
import json

from absl import app
from absl import flags


def postprocess(ps):
    """Replace to the format of the program in the code"""
    result = []
    for k, p in enumerate(ps):
        if p == 'get_frame':
            result.append('query_frame')
        elif p == 'get_object':
            result.append('query_object')
        elif p == 'get_col_partner':
            result.append('query_collision_partner')
        elif p == 'get_counterfact':
            result.append('filter_counterfact')
        elif p == 'start':
            result.append('events')
            result.append('filter_start')
        elif p == 'end':
            result.append('events')
            result.append('filter_end')
        else:
            result.append(p)
    return result


FLAGS = flags.FLAGS

flags.DEFINE_string('inferred_output_path', None, 'Path to the validation_inferred.json.')
flags.DEFINE_string('golden_answers_path', None, 'Path to the validation.json.')

flags.mark_flags_as_required(['inferred_output_path', 'golden_answers_path'])


def main(argv):
    with open(FLAGS.inferred_output_path) as f:
        data = json.load(f)
    with open(FLAGS.golden_answers_path) as f:
        gt = json.load(f)

    oe_result = {}
    mc_result = {}
    for i, d in enumerate(data):
        programs = {
            'scene_index': d['scene_index'],
            'video_filename': f'sim_{10000 + i}.mp4',
            'questions': []
        }
        oe_output = copy.deepcopy(programs)
        mc_output = programs

        for j, q in enumerate(d['questions']):
            if q['question_type'] == 'descriptive':
                program = {
                    'question': q['question'],
                    'question_type': q['question_type'],
                    'program': postprocess(q['program'].split(" ")),
                    'program_gt': postprocess(gt[i]['questions'][j]['program']),
                    'answer': gt[i]['questions'][j]['answer'],
                }
                oe_output['questions'].append(program)
            else:
                program = {
                    'question': q['question'],
                    'question_type': q['question_type'],
                    # 'question_subtype': q['question_subtype'],
                    'question_program': postprocess(q['program'].split(" ")),
                    'program_gt': postprocess(gt[i]['questions'][j]['program']),
                }
                choices = []
                for c in q['choices']:
                    choices.append({
                        'program': postprocess(c['program'].split(" ")),
                        'answer': c['answer'],
                    })
                program['choices'] = choices
                mc_output['questions'].append(program)

        oe_result[10000 + i] = oe_output
        mc_result[10000 + i] = mc_output

    with open('oe_val_core.json', 'w') as f:
        json.dump(oe_result, f)
    with open('mc_val_core.json', 'w') as f:
        json.dump(mc_result, f)

    print('validation programs are generated!')


if __name__ == '__main__':
    app.run(main)
