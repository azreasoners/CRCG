import json
import pickle
import os
from tqdm import tqdm

from base_ASP import ASP_consolidated_3

import json

import openai
from keys import API_KEY,ORG_KEY

import time

import argparse

from helper_functions import *

parser = argparse.ArgumentParser()                                                                                                                                                                                                                                                                                                          

parser.add_argument('--GPT_model', type=str, default='GPT-3.5', help="GPT model to use. Options are GPT-3.5 or GPT-4 (requires API access).")
parser.add_argument('--ASP_CRCG', action='store_true', help = "Use CRCG.") 
parser.add_argument('--ASP_CRCG_GPT', action='store_true', help = "Use GPT-3 with CRCG guided prompting.") 
parser.add_argument('--hard', action='store_true', help = "Use hard split.") 

args= parser.parse_args()


assert not (args.ASP_CRCG ==True and args.ASP_CRCG_GPT==True), 'Can only choose "ASP_CRCG" or ASP_CRCG_GPT"'

openai.organization = ORG_KEY
openai.api_key = API_KEY

get_response_func = get_response_check_3p5 if (args.GPT_model == 'GPT-3.5') else get_response_check_4


f = open(r'annotations.json')
data = json.load(f)

keys = list(data.keys())

f = open(r'descriptions_generated.json')
generated_descriptions = json.load(f)

# =============================================================================
# Load previous GPT-x responses
# =============================================================================
prompt_cache_path = f'prompt_cache_{args.GPT_model}.pickle'
if prompt_cache_path in os.listdir():
    with open(prompt_cache_path, 'rb') as handle:
        prompt_cache = pickle.load(handle)
else:
    prompt_cache = dict()


obj_dict={}
pred_map = {'yes':'True','no':'False'}
num_map = {'one':1,'two':2,'three':3,'four':4,'five':5, 'six':6,'seven':7,'eight':8, 'nine':9,'ten':10}
GPT_queried=0
cache_used=0

difficulty = 'hard' if args.hard else 'easy'
data_split='test'

if args.hard:
    f = open(r'split_info_hard.json')
    diff_split=json.load(f)
else:
    f = open(r'split_info_random.json')
    diff_split=json.load(f)


split_data=dict()

for split in diff_split:
    diff_split[split]
    split_data[split]=[[]]


f = open(r'dataset_minimal.json')
dm=json.load(f)

words = set()
for dd in dm:
    words=words.union(set(dd['question'].split()))


included=list()
cf_count=0
cf_count_without_counts=0
perc_count=0

correct = 0 
total_filtered=0
total_unfiltered=0
in_description_filtered=0

start_idx = 0
end_idx = None
pbar = tqdm(dm[start_idx:end_idx])
for dd_idx,dd in enumerate(pbar):

    video_index=dd['video_index']
    question_index = dd['question_index']
    if dd['question_type']!='Counterfactual':
        continue
    if {'video_index':video_index, 'question_index':question_index} not in diff_split[data_split]:
        continue
    total_unfiltered+=1
    cf_types = ['0','1','3','4','6','7']
    cf_types = ['1']
    cf_type=dd['template_id'][-1]
    cf_type_int = int(cf_type)
    

    question=dd['question'].lower()

    if_index= question.index('if')
    
    if 'will' in question:
        will_index  = question.index('will the')
    elif 'how' in question:
        will_index = question.index('how')
    
    partial_if = question[if_index:]
    partial_will = question[will_index:]
    
    
    cf_obj_split = partial_if.split()
    cf_obj = ['any'] if 'any' in cf_obj_split else cf_obj_split[2:5]
    obj_split=partial_will.split()[2:5]

    desc,reduced_events = get_description(str(video_index).zfill(6),data,obj_dict,generated_descriptions)
    objects= get_objects(desc)
    collisions_string = get_collision_string(reduced_events, objects)
    q_string, c_string, perc_q, objects, desc_q_words = get_query_string(question,objects,cf_type)
    objects_string = get_objects_string(objects)
    ASP_program = ASP_consolidated_3 + '\n\n' + objects_string+collisions_string+q_string + c_string
    
    answer_fact = ASP_solve(ASP_program)
    pred = answer_fact
    answer = dd['answer']
    
    in_description=False
    for event in reduced_events:
        if event[1]!='Start' and event[1]!='End':
            obj1,event_name,obj2 =event
            if list(obj1) == obj_split:
                in_description=True
            if list(obj2) == obj_split:
                in_description=True
    if in_description:
        included.append(dd)
    ASP_pred_correct=-1
    if pred!='tbd':
        perc_count+=1; 
        if not args.ASP_CRCG:
            cf_gpt_correct=-1
            perc_gpt_correct=-1
            
            nl = '\n\n'
            
            GPT_prompt = get_GPT_prompt(cf_type, desc, desc_q_words, question, perc_q, args.ASP_CRCG_GPT)
            GPT_response, prompt_cache, GPT_used1 = get_response_func(GPT_prompt,prompt_cache)
            #response_text = GPT_response['choices'][0]['text'].strip()
            response_text = GPT_response['choices'][0]['message']['content'].strip()
            
            if cf_type in ['0','1','6','7']:
                pred = 'True' if 'yes' in response_text.lower() else 'False' if 'no' in response_text.lower() else 'tbd'
            elif cf_type in ['3','4']:
                pred = response_text.lower()
                
            if cf_type in ['0','1','6','7']:
                if pred == answer:
                    correct+=1
                    cf_gpt_correct=1
                else:
                    cf_gpt_correct=0
                    
            elif cf_type in ['3','4']:
                answer=int(answer)
                if any([True for p in pred if p.isdigit()]):
                    pred = int(''.join([p for p in pred if p.isdigit()]))
                elif any([True for p in pred if p in num_map]):
                    string_nums = [key_num for key_num in num_map if key_num in pred]
                    pred=num_map[string_nums[0]]
                else:
                    pred=0
                
                
                if pred == answer:
                    correct+=1
                    cf_gpt_correct=1
                else:
                    cf_gpt_correct=0
        else:
            if cf_type=='3' or cf_type=='4':
                answer=int(answer)
            else:
                pred=pred_map[pred]
                
            if in_description:
                in_description_filtered+=1
            if pred==answer:
                correct+=1
                
                ASP_pred_correct=1
            else:
                pass
        total_filtered+=1
        pbar.set_description('Acc: {0}'.format(100*correct/total_filtered))


with open(prompt_cache_path, 'wb') as handle:
    pickle.dump(prompt_cache, handle, protocol=pickle.HIGHEST_PROTOCOL)