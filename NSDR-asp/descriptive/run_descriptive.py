import json
import os

from tqdm import tqdm
import argparse

from executor import Executor
from simulation import Simulation
from counterfactual_to_ASP import write_n_run


parser = argparse.ArgumentParser()

parser.add_argument('--ALL', action='store_true', help = "Use all components.")
parser.add_argument('--IOD', action='store_true', help = "Use IOD.")
parser.add_argument('--ASP_PE', action='store_true', help = "Use ASP program executor")
args= parser.parse_args()

if args.ALL:
    args.IOD=True
    args.ASP_PE=True
if args.IOD:
    motion_dir = '../data/converted/'
    v_th = .283
    program_path = '../question_parser/oe_val_core.json'
else:
    motion_dir = '../data/propnet_preds/with_edge_supervision_old'
    program_path = '../data/parsed_programs/oe_1000pg_val_new.json'
    v_th = .1

question_path = '../data/questions/validation.json'

with open(question_path) as f:
    anns = json.load(f)
with open(program_path) as f:
    parsed_pgs = json.load(f)

total, correct = 0, 0

pbar = tqdm(range(5000))
for idx in pbar:
    question_scene = anns[idx]
    file_idx = idx + 10000
    ann_path = os.path.join(motion_dir, f'sim_{idx + 10000:05}.json')

    sim = Simulation(ann_path, moving_v_th=v_th)
    exe = Executor(sim)

    for q_idx, q in enumerate(question_scene['questions']):
        q_type = q['question_type']

        if q_type != 'descriptive':
            continue
        question = q['question']
        program = parsed_pgs[str(file_idx)]['questions'][q_idx]['program']
        if args.ASP_PE:
            asp,_ = write_n_run(sim, question, args)
            if isinstance(asp,int):
                asp=str(asp)
            pred=asp
        else:
            pred = exe.run(program, debug=False)
        


        ans = q['answer']

        if pred == ans:
            correct += 1

        total += 1

    pbar.set_description(f'Acc {correct * 100 / total:.2f}%')
