import json
import os

from tqdm import tqdm
import argparse

from executor import Executor
from simulation import Simulation
from simulator_to_ASP import write_n_run


parser = argparse.ArgumentParser()

parser.add_argument('--ALL', action='store_true', help = "Use all components.")
parser.add_argument('--ASP_PE', action='store_true', help = "Use ASP program executor.")
parser.add_argument('--IOD', action='store_true', help = "Use improved object detection (IOD).")
args= parser.parse_args()


if args.ALL:
    args.IOD=True
    args.ASP_PE=True

question_path = '../data/questions/validation.json'
program_path = '../question_parser/mc_val_core.json'

if args.IOD:
    motion_dir = '../data/converted/'
else:
    motion_dir = '../data/propnet_preds/with_edge_supervision_old'



with open(question_path) as f:
    anns = json.load(f)
with open(program_path) as f:
    parsed_pgs = json.load(f)

total_c, correct_c = 0, 0
total_q, correct_q = 0, 0

pred_map = {'yes': 'correct', 'no': 'wrong', 'error': 'error'}

pbar = tqdm(range(0, 5000))

for idx in pbar:

    question_scene = anns[idx]
    ann_path = os.path.join(motion_dir, f'sim_{idx + 10000:05}.json')
    file_idx = idx + 10000
    sim = Simulation(ann_path)
    exe = Executor(sim)
    valid_q_idx = 0
    for q_idx, q in enumerate(question_scene['questions']):
        q_type = q['question_type']

        if q_type != 'explanatory':
            continue
        q_ann = parsed_pgs[str(file_idx)]['questions'][valid_q_idx]
        correct_question = True
        choices = list()
        for c_idx, c in enumerate(q['choices']):
            for t_idx, t_choice in enumerate(q_ann['choices']):
                if t_choice['program'] == c['program']:
                    choices.append(c['choice'])
                    break
        if args.ASP_PE:
            all_lines = write_n_run(sim,
                                      q_ann['question_program'], q_ann['choices'][t_idx]['program'],
                                      q_ann['question'], c['choice'], choices,
                                      args)
    
            answer_facts = [fact for fact in list(all_lines[0]) if 'answer' in fact]
            answer_facts = [(int(ans[1][0][-1]), ans[1][1]) for ans in answer_facts]
            answer_facts = {item[0]: pred_map[item[1]] for item in answer_facts}

        for c_idx, c in enumerate(q['choices']):
            if args.ASP_PE:
                pred = answer_facts[c_idx]
            else:
                full_pg=q_ann['choices'][c_idx]['program']+q_ann['question_program']
                pred = exe.run(full_pg, debug=False)
                pred=pred_map[pred]
            ans = c['answer']

            if ans == pred:
                correct_c += 1
            else:
                correct_question = False
            total_c += 1

        if correct_question:
            correct_q += 1

        total_q += 1
        valid_q_idx += 1
    pbar.set_description(f'Choice {correct_c * 100 / total_c:.2f}%, Question {correct_q * 100 / total_q:.2f}%')
