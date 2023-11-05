import json
import os
import random

from tqdm import tqdm
import argparse

from executor_predictive_physics import Executor
from pred_utils import AC
from predictive_to_ASP_PE import write_n_run
from simulation_predictive_physics_VRDP import Simulation


parser = argparse.ArgumentParser()
parser.add_argument('--ALL', action='store_true', help = "Use all components.")
parser.add_argument('--ASP_PE', action='store_true', help = "Use ASP program executor.")
parser.add_argument('--SPS', action='store_true', help = "Use simple physics simulator (SPS).")
parser.add_argument('--AC', action='store_true', help = "Use answer constraint (AC).")
parser.add_argument('--IOD', action='store_true', help = "Use improved object detection (IOD).")
args= parser.parse_args()

if args.ALL:
    args.SPS = True
    args.ASP_PE = True
    #args.AC = True
    args.IOD = True

if args.AC and not args.SPS:
    raise Exception('AC requires SPS')

if args.IOD:
    frame_params={'HIT_THRESHOLD':10.5, 'PREDICT_END':33, 'VIDEO_END':24, 'TIME_DIFF':5}
else:
    frame_params={'HIT_THRESHOLD':10.5, 'PREDICT_END':33, 'VIDEO_END':26, 'TIME_DIFF':5}

random.seed(195839127)

raw_motion_dir = '../data/object_updated_results'

question_path = '../../NSDR-asp/data/questions/validation.json'
program_path = '../../NSDR-asp/question_parser/mc_val_core.json'


with open(question_path) as f:
    anns = json.load(f)
with open(program_path) as f:
    parsed_pgs = json.load(f)

total, correct = 0, 0
total_per_q, correct_per_q = 0, 0
total_pred, correct_pred = 0, 0
total_pred_per_q, correct_pred_per_q = 0, 0

pred_map = {'yes': 'correct', 'no': 'wrong', 'error': 'error'}
pbar = tqdm(range(5000))

wrong_ann_indices = list()

cnt1 = 0
cnt2 = 0
tp,tn,fp,fn=0,0,0,0
for ann_idx in pbar:
    question_scene = anns[ann_idx]
    file_idx = ann_idx + 10000
    ann_path = os.path.join(raw_motion_dir, 'sim_%05d.json' % file_idx)
    #breakpoint()
    sim = Simulation(ann_path, frame_params, use_event_ann=(1), use_IOD=args.IOD, use_PM=args.SPS)
    exe = Executor(sim)
    valid_q_idx = 0
    for q_idx, q in enumerate(question_scene['questions']):
        question = q['question']
        q_type = q['question_type']

        if q_type == 'descriptive':  # skip open-ended questions
            continue

        if q_type != 'predictive':
            valid_q_idx += 1
            continue

        q_ann = parsed_pgs[str(file_idx)]['questions'][valid_q_idx]

        c1_pred = None
        c2_pred = None
        c_reasoning = list()
        choices = list()
        for c_idx, c in enumerate(q_ann['choices']):

            q_program = q_ann['question_program']
            c_program = c['program']
            if args.AC:
                c_reasoning.append(AC(c_program,sim))
            for t_idx, t_choice in enumerate(q['choices']):
                if t_choice['program'] == c['program']:
                    choices.append(t_choice['choice'])
                    break
        if args.AC:
            c_ans = None
            if c_reasoning[0] == 0:
                if c_reasoning[1] == 1:
                    c_ans = 0
            if c_reasoning[1] == 0:
                if c_reasoning[0] == 1:
                    c_ans = 1

        correct_question = True
        if args.ASP_PE:
            answer_facts, _ = write_n_run(sim, question, choices,args, False)
        psave = []
        asave = []
        for c_idx, c in enumerate(q_ann['choices']):
            full_pg = c['program'] + q_ann['question_program']
            ans = c['answer']
            
            if args.ASP_PE:
                pred=pred_map[answer_facts[c_idx]]
            else:
                pred, program_information = exe.run(full_pg, debug=False)
                pred = pred_map[pred]
            
            if args.AC:
                if c_ans is not None:
                    if c_idx == 0:
                        pred = 'wrong' if c_ans == 0 else 'correct'
                    if c_idx == 1:
                        pred = 'wrong' if c_ans == 1 else 'correct'
            
            psave.append(pred)
            asave.append(ans)

        if args.AC:
            alpha = 2
            if psave[0] == psave[1]:

                idx = random.randrange(0, 1000000) % alpha
                idx = 1 if idx >= 1 else 0
                if psave[idx] == 'correct':
                    cnt1 += 1
                else:
                    cnt2 += 1
                psave[idx] = 'wrong' if psave[idx] == 'correct' else 'correct'

        for c_idx, c in enumerate(q_ann['choices']):
            pred = psave[c_idx]
            ans = asave[c_idx]

            if ans == pred:
                correct += 1
            else:
                correct_question = False
            total += 1

            if q['question_type'].startswith('predictive'):

                if ans == pred:
                    correct_pred += 1
                    if pred =='correct':
                        tp+=1
                    else:
                        tn+=1
                else:
                    wrong_ann_indices.append([ann_idx, q_idx, c_idx, c])
                    if pred == 'correct':
                        fp+=1
                    elif pred =='wrong':
                        fn+=1
                        
                total_pred += 1

        if correct_question:
            correct_per_q += 1
        total_per_q += 1

        if q['question_type'].startswith('predictive'):
            if correct_question:
                correct_pred_per_q += 1
            total_pred_per_q += 1

    pbar.set_description('per choice {:f}, per questions {:f}'.format(float(correct) * 100 / total,
                                                                      float(correct_per_q) * 100 / total_per_q))
