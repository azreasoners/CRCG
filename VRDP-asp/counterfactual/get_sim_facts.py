import os
import random
import json

from tqdm import tqdm
import argparse

from physics_module import Physics
from counterfactual_to_ASP import write_n_run
from executor_counterfactual_ASP import Executor
from simulation_counterfactual import Simulation

parser = argparse.ArgumentParser()

parser.add_argument('--ALL', action='store_true', help = "Use all components.")
parser.add_argument('--IODP', action='store_true', help = "Use improved object detection and prediction (IODP).") 
parser.add_argument('--AC', action='store_true', help = "Use answer constraint (AC).")
args= parser.parse_args()

if args.ALL:
    args.IODP=True
    args.AC=True


if args.IODP:
    frame_params={'HIT_THRESHOLD':23.0, 'PREDICT_END':160, 'VIDEO_END':126, 'TIME_DIFF':1} #threshold = 23.0
else:
    frame_params={'HIT_THRESHOLD':10.5, 'PREDICT_END':33, 'VIDEO_END':26, 'TIME_DIFF':5}

random.seed(195839127)

raw_motion_dir = '../data/object_updated_results'
question_path = '../../NSDR-asp/data/questions/validation.json'
program_path = '../../NSDR-asp/question_parser/mc_val_core.json'

def desc2idx(collisions,obj_dict):
    
    collision_inds = list()
    for col in collisions:
        obj_descs = list(obj_dict.keys())
        idxs=list()
        for obj in col['objects']:
            obj_desc = obj['color']+obj['material']+obj['shape']
            idxs.append([idx for idx,o in enumerate(obj_descs) if obj_desc==o][0])
        
        collision_inds.append({'type':'collision', 'object':[idxs[0],idxs[1]], 'frame': col['frame']})
    
    return collision_inds

# =============================================================================
# USE ASP
# =============================================================================

USE_ASP=True
with open(question_path) as f:
    anns = json.load(f)
with open(program_path) as f:
    parsed_pgs = json.load(f)
total, correct = 0, 0
total_per_q, correct_per_q = 0, 0
total_coun, correct_coun = 0, 0
total_coun_per_q, correct_coun_per_q = 0, 0

pred_map = {'yes': 'correct', 'no': 'wrong', 'error': 'error', 'unknown': 'unknown'}
pbar = tqdm(range(0,5000))
log=list();
all_ann_indices = list()
all_sims_dict = dict()
tp,tn,fp,fn=0,0,0,0

for ann_idx in pbar:
    question_scene = anns[ann_idx]
    
    file_idx = ann_idx + 10000
    object_dict = json.load(open(f'../data/object_dicts_with_physics/objects_{file_idx:05d}.json'))
    


    obj2idx= {k:idx  for idx,k in enumerate(object_dict.keys())}
    idx2obj = dict((v, k) for k, v in obj2idx.items())
    ann_path = os.path.join(raw_motion_dir, 'sim_%05d.json' % file_idx)
    vid_string= 'sim_%05d.json' % file_idx
    all_sims_dict[vid_string]=[]
    sim = Simulation(ann_path, frame_params, use_event_ann=1, use_IODP=args.IODP)
    exe = Executor(sim)
    valid_q_idx = 0
    
    sim_idx = -1
    for q_idx, q in enumerate(question_scene['questions']):
        
        question = q['question']
        q_type = q['question_type']

        if q_type == 'descriptive':  # skip open-ended questions
            continue
        if q_type != 'counterfactual':  # skip explanatory and predictive
            valid_q_idx += 1
            continue
        
        sim_idx+=1

        q_ann = parsed_pgs[str(file_idx)]['questions'][valid_q_idx]
        
        correct_question = True
        choices = list()
        for c_idx, c in enumerate(q_ann['choices']):
            for t_idx, t_choice in enumerate(q['choices']):
                if t_choice['program'] == c['program']:
                    choices.append(t_choice['choice'])
                    break

        if USE_ASP:
            answer_facts, sims = write_n_run(sim, question, choices,args)
            trajectory = sim.preds[0]['trajectory']
            scene_collisions = sim.collisions
        else:
            answer_facts=['unknown']*10;sims=None;   

        
        removed= exe.get_removed(q_ann['choices'][0]['program']+q_ann['question_program'])
        removed_desc = idx2obj[removed]

        question_info_dict = {'question':question, 'q_idx':q_idx, 'obj_removed':[removed,removed_desc],'sim':sims}
        all_sims_dict[vid_string].append(question_info_dict)



    
with open('all_sims_dict.json', 'w') as fout:
    json.dump(all_sims_dict, fout)
