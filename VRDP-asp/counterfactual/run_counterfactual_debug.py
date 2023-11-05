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
parser.add_argument('--ASP_CR', action='store_true', help = "Use ASP-CR.") 
parser.add_argument('--ASP_SIM', action='store_true', help = "Use ASP_SIM.") 
parser.add_argument('--AC', action='store_true', help = "Use answer constraint (AC).")
args= parser.parse_args()

if args.ALL:
    args.ASP_CR = True
    args.ASP_SIM = True
    #args.AC=True
args.IOD=False


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


with open(question_path) as f:
    anns = json.load(f)
with open(program_path) as f:
    parsed_pgs = json.load(f)

total, correct = 0, 0
total_per_q, correct_per_q = 0, 0
total_coun, correct_coun = 0, 0
total_coun_per_q, correct_coun_per_q = 0, 0


branch1_correct=0; branch1_total=0
branch2_correct=0; branch2_total=0

pred_map = {'yes': 'correct', 'no': 'wrong', 'error': 'error', 'tbd': 'tbd'}
pbar = tqdm(range(0,5000))
log=list();
all_ann_indices = list()
all_sims_dict = dict()
tp,tn,fp,fn=0,0,0,0
all_sims_dict = json.load(open('../counterfactual/all_sims_dict.json'))

for ann_idx in pbar:
    question_scene = anns[ann_idx]
    
    file_idx = ann_idx + 10000
    object_dict = json.load(open(f'../data/object_dicts_with_physics/objects_{file_idx:05d}.json'))
    
    
    obj2idx= {k:idx  for idx,k in enumerate(object_dict.keys())}
    idx2obj = dict((v, k) for k, v in obj2idx.items())
    ann_path = os.path.join(raw_motion_dir, 'sim_%05d.json' % file_idx)
    vid_string= 'sim_%05d.json' % file_idx
    all_sims_dict[vid_string]=[]
    sim = Simulation(ann_path, frame_params, use_event_ann=1, use_IODP=False)
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
        
        if args.ASP_SIM:
            simulated_ASP = json.load(open(f'../data/ASP_SIM_results/simulatedASP_{file_idx:05d}_{sim_idx}.json'))
    
            if len(simulated_ASP)==1 and args.ASP_SIM: 
                simulated_ASP=simulated_ASP[0]
                sim_collisions_list = simulated_ASP['sim_ASP_col']
                sim_collisions = desc2idx(sim_collisions_list,object_dict)
                sim.cf_events[simulated_ASP['obj_removed'][0]]=sim_collisions
        q_ann = parsed_pgs[str(file_idx)]['questions'][valid_q_idx]
        correct_question = True
        choices = list()
        for c_idx, c in enumerate(q_ann['choices']):
            for t_idx, t_choice in enumerate(q['choices']):
                if t_choice['program'] == c['program']:
                    choices.append(t_choice['choice'])
                    break
        if args.ASP_CR:
            answer_facts, sims = write_n_run(sim, question, choices,args)
            trajectory = sim.preds[0]['trajectory']
            scene_collisions = sim.collisions
        else:
            answer_facts=['tbd']*10;sims=None;   
        
        removed= exe.get_removed(q_ann['choices'][0]['program']+q_ann['question_program'])
        removed_desc = idx2obj[removed]
        question_info_dict = {'question':question, 'q_idx':q_idx, 'obj_removed':[removed,removed_desc],'sim':sims}
        all_sims_dict[vid_string].append(question_info_dict)
        psave = []
        asave = []
        aspsave = []
        branch=list()
        for c_idx, c in enumerate(q_ann['choices']):
            full_pg = c['program'] + q_ann['question_program']
            ans = c['answer']

            for t_idx, t_choice in enumerate(q['choices']):
                if t_choice['program'] == c['program']:
                    choice_string = t_choice['choice']
            pred, counterfactual_answer, program_information = exe.run(full_pg, answer_facts, sims, c_idx, debug=False)
            exe.get_removed(full_pg)
            
            
            
            
            branch1=False;branch2=False
            if pred != None: 
                pred = pred_map[pred] #use program executor (branch 1)
                aspsave.append(False)
                branch.append(1)
            else:
                pred = pred_map[counterfactual_answer] #use branch 2
                aspsave.append(True)
                branch.append(2)
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
            log.append([ann_idx,q_idx,pred,ans, question,q['choices'][c_idx]['choice']])
            total += 1

            if q['question_type'].startswith('counterfactual'):
                if ans == pred:
                    correct_coun += 1
                    if pred=='correct':
                        tp+=1
                    elif pred=='wrong':
                        tn+=1
                    if branch[c_idx]==1:
                        branch1_correct+=1
                        branch1_total+=1
                    else:
                        branch2_correct+=1
                        branch2_total+=1
                else:
                    if pred == 'correct':
                        fp+=1
                    elif pred == 'wrong':
                        fn+=1
                    if branch[c_idx]==1:
                        branch1_total+=1
                    else:
                        branch2_total+=1
                total_coun += 1
                pass;
#            all_ann_indices.append([ann_idx, q_idx, c_idx, c,pred==ans,aspsave[c_idx]]) # debugging
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
    
