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

flags.DEFINE_string('inferred_output_path', None, 'Path to the test_inferred.json.')

flags.mark_flags_as_required(['inferred_output_path'])


def main(argv):
    with open(FLAGS.inferred_output_path) as f:
        data = json.load(f)

    oe_result = []
    mc_result = []
    for i, d in enumerate(data):
        programs = {
            'scene_index': d['scene_index'],
            'questions': []
        }
        oe_output = copy.deepcopy(programs)
        mc_output = programs

        for j, q in enumerate(d['questions']):
            program = {
                'question_id': q['question_id'],
                # 'question': q['question'],
                'program': postprocess(q['program'].split(" ")),
            }
            if q['question_type'] == 'descriptive':
                oe_output['questions'].append(program)
            else:
                choices = []
                for c in q['choices']:
                    choices.append({
                        'choice_id': c['choice_id'],
                        'program': postprocess(c['program'].split(" ")),
                    })
                program['choices'] = choices
                mc_output['questions'].append(program)

        oe_result.append(oe_output)
        mc_result.append(mc_output)

    with open('oe_test_core.json', 'w') as f:
        json.dump(oe_result, f)
    with open('mc_test_core.json', 'w') as f:
        json.dump(mc_result, f)

    print('test programs are generated!')


if __name__ == '__main__':
    app.run(main)
