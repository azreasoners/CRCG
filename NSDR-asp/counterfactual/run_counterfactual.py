import os
import random
import json

from tqdm import tqdm
import argparse

from physics_module import Physics
from counterfactual_to_ASP import write_n_run
from counterfactual_to_ASP_PE import write_n_run as write_n_run2
from executor_counterfactual_ASP import Executor
from simulation_counterfactual import Simulation

parser = argparse.ArgumentParser()
parser.add_argument('--ALL', action='store_true', help = "Use all components.")
parser.add_argument('--ASP_CRCG', action='store_true', help = "Use ASP-CR.") 
parser.add_argument('--ASP_PE', action='store_true', help = "Use ASP program executor.") 
parser.add_argument('--IOD', action='store_true', help = "Use improved object detection (IOD).") 
parser.add_argument('--SPS', action='store_true', help = "Use simple physics simulator (SPS).") 
parser.add_argument('--AC', action='store_true', help = "Use answer constraint (AC).")
args= parser.parse_args()

assert not (args.ASP_CRCG ==False and args.SPS==True), 'SPS requires ASP_CRCG, use --ASP_CRCG'

if args.ALL:
    args.IOD=True
    args.SPS=True
    args.ASP_CRCG=True
    args.ASP_PE=True
    # args.AC=True

if args.IOD:
    frame_params={'HIT_THRESHOLD':23.0, 'PREDICT_END':160, 'VIDEO_END':126, 'TIME_DIFF':1}
else:
    frame_params={'HIT_THRESHOLD':10.5, 'PREDICT_END':33, 'VIDEO_END':26, 'TIME_DIFF':5}

random.seed(195839127)

raw_motion_dir = '../data/propnet_preds/with_edge_supervision_old'
question_path = '../data/questions/validation.json'
program_path = '../question_parser/mc_val_core.json'

with open(question_path) as f:
    anns = json.load(f)
with open(program_path) as f:
    parsed_pgs = json.load(f)

total, correct = 0, 0
total_per_q, correct_per_q = 0, 0
total_coun, correct_coun = 0, 0
total_coun_per_q, correct_coun_per_q = 0, 0

pred_map = {'yes': 'correct', 'no': 'wrong', 'error': 'error', 'tbd': 'tbd'}
pbar = tqdm(range(0,5000))
log=list()
for ann_idx in pbar:
    question_scene = anns[ann_idx]
    file_idx = ann_idx + 10000
    ann_path = os.path.join(raw_motion_dir, 'sim_%05d.json' % file_idx)
    sim = Simulation(ann_path, frame_params, use_event_ann=1, use_IOD=args.IOD,use_PM=args.SPS)
    exe = Executor(sim)
    valid_q_idx = 0

    for q_idx, q in enumerate(question_scene['questions']):

        question = q['question']
        q_type = q['question_type']

        if q_type == 'descriptive':  # skip open-ended questions
            continue
        if q_type != 'counterfactual':  # skip explanatory and predictive
            valid_q_idx += 1
            continue

        q_ann = parsed_pgs[str(file_idx)]['questions'][valid_q_idx]
        correct_question = True
        choices = list()
        for c_idx, c in enumerate(q_ann['choices']):
            for t_idx, t_choice in enumerate(q['choices']):
                if t_choice['program'] == c['program']:
                    choices.append(t_choice['choice'])
                    break
        if args.ASP_CRCG:
            answer_facts, sims = write_n_run(sim, question, choices,args)
        else:
            answer_facts={i:'tbd' for i in range(10)}
        trajectory = sim.preds[0]['trajectory']
        scene_collisions = sim.collisions
        if args.SPS:
            for removed in [obj_attr['id'] for obj_attr in sim.objs]:
                physics=Physics(frame_params)
                new_cf_events, attr_to_idx, obj_motion_dict_rotated, predicted = physics.simulate(sim.objs, trajectory,
                                                                                          scene_collisions, frame_params, sims, removed)
                sim.cf_events[removed] = new_cf_events
            
        psave = []
        asave = []
        if args.ASP_PE:
            answer_facts_PE, _ = write_n_run2(sim, question, choices,args, False)
        for c_idx, c in enumerate(q_ann['choices']):
            full_pg = c['program'] + q_ann['question_program']
            ans = c['answer']

            for t_idx, t_choice in enumerate(q['choices']):
                if t_choice['program'] == c['program']:
                    choice_string = t_choice['choice']
            
            if answer_facts[c_idx] != 'tbd':
                pred = pred_map[answer_facts[c_idx]]
            else:
                if args.ASP_PE:
                    pred = pred_map[answer_facts_PE[c_idx]]
                else:
                    pred, _, program_information = exe.run(full_pg, {i:'tbd' for i in range(10)}, c_idx, debug=False)
                    pred = pred_map[pred]
            psave.append(pred)
            asave.append(ans)
        if args.AC:
            cnt = sum([p == 'correct' for p in psave])
            if cnt == 0 and len(psave) > 1:
                idx = random.randrange(0, 1000000) % len(psave)
                if psave[idx] == 'correct':
                    continue
                psave[idx] = 'correct'
                cnt = sum([p == 'correct' for p in psave])
            if cnt == len(psave) and len(psave) > 1:
                idx = random.randrange(0, 1000000) % len(psave)
                if psave[idx] == 'wrong':
                    continue
                psave[idx] = 'wrong'
                cnt = sum([p == 'correct' for p in psave])

        for c_idx, c in enumerate(q_ann['choices']):
            pred = psave[c_idx]
            ans = asave[c_idx]
            answer_changed = False

            if ans == pred:
                correct += 1
            else:
                correct_question = False
            log.append([ann_idx,q_idx,pred,ans])
            total += 1

            if q['question_type'].startswith('counterfactual'):
                if ans == pred:
                    correct_coun += 1
                total_coun += 1
                pass;
        if correct_question:
            correct_per_q += 1
        total_per_q += 1

        if q['question_type'].startswith('counterfactual'):
            if correct_question:
                correct_coun_per_q += 1
            total_coun_per_q += 1
        valid_q_idx += 1

    pbar.set_description('per choice {:f}, per questions {:f}'.format(float(correct) * 100 / total,
                                                                      float(correct_per_q) * 100 / total_per_q))

print('============ results ============')
print('counterfactual accuracy per option: %f %%' % (float(correct_coun) * 100.0 / total_coun))
print('counterfactual accuracy per question: %f %%' % (float(correct_coun_per_q) * 100.0 / total_coun_per_q))
print('============ results ============')

output_ann = {
    'total_options': total,
    'correct_options': correct,
    'total_questions': total_per_q,
    'correct_questions': correct_per_q,

    'total_counterfactual_options': total_coun,
    'correct_counterfactual_options': correct_coun,
    'total_counterfactual_questions': total_coun_per_q,
    'correct_counterfactual_questions': correct_coun_per_q,
}

output_file = 'result_mc.json'

with open(output_file, 'w') as fout:
    json.dump(output_ann, fout)
