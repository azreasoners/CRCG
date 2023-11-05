import openai
from toolz import unique
import time
from clyngor import ASP
from GPT_prompts import prompt, prompt2, prompt_additional2, prompt_additional


EXCLUDE_EVENTS= ('wall_l','wall_r','platform', 'ramp')

synonyms = {'big':'large',
            'floor':'ground',
            'container':'basket',
            'bucket':'basket',
            'tiny':'small',
            'block':'cube'}

sizes = ['small','large', 'big','tiny']
colors = ['gray','red','blue','green','brown','purple','cyan','yellow', 'black']
shapes=['cube','triangle','circle','block','ground', 'floor','basket','container','bucket', 'static_ball']

nl = '\n\n'



def get_GPT_prompt(cf_type, desc, desc_q_words, question, perc_q, default_GPT):
    """
    Returns ASP facts
    - args: cf_type(str), desc(str), desc_q_words(list), question(str), perc_q(str), default_GPT(bool)
    - return: GPT_prompt(str)
    """
    if not default_GPT:
        if cf_type in ['0','1', '6','7']:
            GPT_prompt = prompt  + desc + nl + question.capitalize() + ' (yes or no)\n' 
        if cf_type in ['3','4']:
            GPT_prompt = prompt  + desc + nl + question.capitalize() + ' (Answer with a number 1-8)\n'
    else:
        if cf_type in ['0','1','5','6','7']:
            GPT_prompt = prompt2 + desc + nl + 'According to the scene description, '+perc_q.lower()  +' (yes or no)\n' #(7)
        elif cf_type in ['3','4']:
            GPT_prompt = prompt2 + desc + nl + f'According to the scene description, ' +perc_q.lower()[:-1] +f', excluding the {" ".join(desc_q_words)}?'+  ' (Answer with a number 0-8)\n' #(7)
            if 'bucket' in question:
                GPT_prompt = prompt2 + desc.replace('basket', 'bucket') + nl + f'According to the scene description, ' +perc_q.lower()[:-1] +f', excluding the {" ".join(desc_q_words)}?'+  ' (Answer with a number 0-8)\n' #(7)
            elif 'container' in question:
                GPT_prompt = prompt2 + desc.replace('basket','container') + nl + f'According to the scene description, ' +perc_q.lower()[:-1] +f', excluding the {" ".join(desc_q_words)}?'+  ' (Answer with a number 0-8)\n' #(7)
            elif 'basket' in question:
                GPT_prompt = prompt2 + desc + nl + f'According to the scene description, ' +perc_q.lower()[:-1] +f', excluding the {" ".join(desc_q_words)}?'+  ' (Answer with a number 0-8)\n' #(7)
            
            if 'floor' in question:
                GPT_prompt = prompt2 + desc.replace('ground','floor') + nl + f'According to the scene description, ' +perc_q.lower()[:-1] +f', excluding the {" ".join(desc_q_words)}?'+  ' (Answer with a number 0-8)\n' #(7)
    
    return GPT_prompt




def ASP_solve(ASP_program):
    """
    Return answer set facts corresponding to answer/1
    - args:
    - return: answer_facts(list)
    """
    answers = ASP(ASP_program,nb_model=1,options = '--warn none')
    
    all_lines=[]
    for line in answers:
        all_lines.append(line)

    answer_facts=[fact for fact in list(all_lines[0]) if 'answer' in fact]
    if len(answer_facts)==0:
        answer_fact = 'tbd'
    else:
        answer_fact = answer_facts[0][1][0]

    return answer_fact


def get_response(prompt,temp=0.,max_tokens=30):
    return openai.Completion.create(engine="text-davinci-002", prompt=prompt, temperature=temp, max_tokens=max_tokens)

def get_response_check(prompt,prompt_cache,temp=0,max_tokens=30):
    if prompt in prompt_cache:
        return prompt_cache[prompt], prompt_cache, 0
    else:
        response = get_response(prompt,temp=temp,max_tokens=max_tokens)
        prompt_cache[prompt]=response
        time.sleep(2)
        return response, prompt_cache, 1




def get_response_3p5(prompt,temp=0.,max_tokens=30):
    
    passed = False; tries = 0 
    messages = [{'role': 'user', 'content': prompt}]
    while not passed:
        try:
            response = openai.ChatCompletion.create(
                messages=messages,
                model="gpt-3.5-turbo-0613", # 'gpt-3.5-turbo-0613' 'gpt-4-0613'
                temperature=0,
                max_tokens=1000)
            passed=True;tries+=1
            #prompt_cache[prompt] = response
        except:
            tries+=1
            if tries >=4:
                breakpoint()
            print(f'doing attempt number {tries +1}')

    return response


def get_response_check_3p5(prompt,prompt_cache,temp=0,max_tokens=30):
    if prompt in prompt_cache:
        return prompt_cache[prompt], prompt_cache, 0
    else:
        response = get_response_3p5(prompt, temp=temp,max_tokens=max_tokens)
        prompt_cache[prompt]=response
        time.sleep(2)
        return response, prompt_cache, 1


def get_response_4(prompt,temp=0.,max_tokens=30):
    
    passed = False; tries = 0 
    messages = [{'role': 'user', 'content': prompt}]
    while not passed:
        try:
            response = openai.ChatCompletion.create(
                messages=messages,
                model="gpt-4-0613", # 'gpt-3.5-turbo-0613' 'gpt-4-0613'
                temperature=0,
                max_tokens=1000)
            passed=True;tries+=1
            #prompt_cache[prompt] = response
        except:
            tries+=1
            if tries >=4:
                breakpoint()
            print(f'doing attempt number {tries +1}')

    return response


def get_response_check_4(prompt,prompt_cache,temp=0,max_tokens=30):
    if prompt in prompt_cache:
        return prompt_cache[prompt], prompt_cache, 0
    else:
        response = get_response_4(prompt, temp=temp,max_tokens=max_tokens)
        prompt_cache[prompt]=response
        time.sleep(2)
        return response, prompt_cache, 1


# =============================================================================
# Various functions for parsing text and generating ASP rules/facts
# =============================================================================


def get_query_string(query,objects,cf_type):
    if ',' in query:
        question_obj,choice_obj = query.split(', ')
    else:
        choice_obj,question_obj=query.split('if')
    objq_string, desc_q_words, negate_string, objects = get_question_string(question_obj, objects)
    
    objc_string, objects = get_choice_string(choice_obj, 0, objects)
    
    if cf_type in ['0','1', '3', '4', '6', '7']:
        perception_q = choice_obj.capitalize()
        perception_q = perception_q[:-1]+'?' if '?' not in perception_q else perception_q
        perception_q = perception_q.replace('Will','Did')
    
    return objq_string, objc_string, perception_q, objects, desc_q_words

def get_question_string(question_obj_string, objects):
    
    split_words=question_obj_string.split()
    split_words = [token if token not in synonyms else synonyms[token] for token in split_words]
    negate='not' in split_words
    negate_string='no' if negate else 'yes'
    objq_string=''
    temp_dict=dict()
    desc_words = list()
    for word in split_words:
        if word in colors:
            string='feature(qobj(1),{0}).\n'.format(word)
            temp_dict['color']=word
            desc_words.append(word)
        elif word in shapes:
            string='feature(qobj(1),{0}).\n'.format(word)
            temp_dict['shape']=word
            desc_words.append(word)
        elif word in sizes:
            string='feature(qobj(1),{0}).\n'.format(word)
            temp_dict['size']=word
            desc_words.append(word)
        else:
            continue
        objq_string+=string 
    
    if 'any' in question_obj_string:
        counterfact_string = 'counterfact(remove,any).\n'
    else:
        counterfact_string = 'counterfact(remove,qobj(1)).\n'
    
    objq_string= counterfact_string + objq_string+'\n'
     #check if object in query is a known object
    if temp_dict not in objects.values() and len(temp_dict)>0:
        objects[len(objects)-2]=temp_dict
    
    
    return objq_string, desc_words, negate_string, objects


def get_attr(feature):
    if feature in colors:
        return 'color'
    elif feature in sizes:
        return 'size'
    elif feature in shapes:
        return 'shape'
    else:
        print(feature)
        assert 1==0

def get_objects_string(objects):
    objects_string = ''
    for obj_idx,obj in objects.items():
        arg1,arg2,arg3 = obj['size'],obj['color'],obj['shape']
        args = [arg1,arg2,arg3]
        
        arg_attrs = [get_attr(arg) for arg in args]
        
        objects_string+=''.join([f"{arg_attrs[idx]}({obj_idx},{args[idx]})." for idx in range(3)])+'\n'
    
    
    return objects_string

def get_objects(desc):
    
    obj_set =set()
    obj_dict = dict()
    desc_list = desc.split('.')
    
    for sent in desc_list:
        shape_in = any([shape in sent for shape in shapes])
        if not shape_in:
            continue
        sent_words = sent.split()
        sent_shapes = [shape for shape in shapes if shape in sent_words]
        sent_shapes = [sent_shape for sent_shape in sent_shapes if (sent_shape!='basket' and sent_shape!='ground')]
        shape_indices=list()
        for shape in sent_shapes:
            for idx, word in enumerate(sent_words):
                if shape == word:
                    shape_indices.append(idx)
        for shape_ind in shape_indices:
            obj_size, obj_color, obj_shape = [word.lower() for word in sent_words[shape_ind-2:shape_ind+1]]
            obj_set.add((obj_size,obj_color,obj_shape))
        
    for obj_idx,obj in enumerate(obj_set):
        obj_dict[obj_idx]={'size':obj[0],'color':obj[1],'shape':obj[2]}
    
    obj_dict[95]={'size':'large','color':'black','shape':'ground'}
    obj_dict[97]={'size':'large','color':'black','shape':'basket'}
    
    return obj_dict


def get_obj_from_partial(feature,objects):
    for key,obj in objects.items():
        for feature_ in obj.values():
            if feature ==feature_:
                return obj

def get_choice_string(choice,choice_num,objects):
    tokens = choice.replace('?','').split()
    tokens = [token if token not in synonyms else synonyms[token] for token in tokens ]
    for idx,token in enumerate(tokens):
        if (token in colors) or (token in shapes) or (token in sizes) :
            start_idx = idx
            break
    
    choice_obj_features = tokens[start_idx:start_idx+3]
    
    for token in tokens:
        if token in ['ground', 'floor','basket','container','bucket']:
            other_obj_token = token
            break
    
    split1_words = choice_obj_features
    other_obj = get_obj_from_partial(other_obj_token,objects)
    
    
    split2_words =list(other_obj.values())

    obj1_string=''
    temp_dict=dict()
    for word in split1_words:
        if word in colors:
            string='feature(qobj(2),{0}).'.format(word)
            temp_dict['color']=word
        elif word in shapes:
            string='feature(qobj(2),{0}).'.format(word)
            temp_dict['shape']=word
        elif word in sizes:
            string='feature(qobj(2),{0}).'.format(word)
            temp_dict['size']=word
        else:
            continue
        obj1_string+= string
        
    if temp_dict not in objects.values() and len(temp_dict)==3:
        objects[len(objects)-2]=temp_dict
    
    obj2_string=''
    temp_dict=dict()
    for word in split2_words:
        if word in colors:
            string='feature(qobj(3),{0}).'.format(word)
            temp_dict['color']=word
        elif word in shapes:
            string='feature(qobj(3),{0}).'.format(word)
            temp_dict['shape']=word
        elif word in sizes:
            string='feature(qobj(3),{0}).'.format(word)
            temp_dict['size']=word
        else:
            continue
        obj2_string+=string
    
    if temp_dict not in objects.values() and len(temp_dict)==3:
        objects[len(objects)-2]=temp_dict

    if 'basket' in split2_words:
        if 'many' in choice:
            query_fact = 'query(enter(count,qobj(2))).'
        else:
            query_fact = 'query(enter(qobj(2),qobj(3))).' 
    else:
        if 'many' in choice:
            query_fact = 'query(collide(count,qobj(2))).'
        else:
            query_fact= 'query(collide(qobj(2),qobj(3))).'
    
    final_choice_string = query_fact + '\n' + obj1_string + '\n' + obj2_string
    
    return final_choice_string, objects

def get_obj_idx(obj_dict,objects):
    
    for key,obj in objects.items():
        if obj==obj_dict:
            return key
    print(obj_dict)
    assert 1==0
    
def get_attrs_idx(attr_tuple,objects):
    
        dict_attrs = {'size':attr_tuple[0],'color':attr_tuple[1],'shape':attr_tuple[2]}
        obj_idx = get_obj_idx(dict_attrs,objects)
        return dict_attrs, obj_idx


def get_collision_string(events,objects):
    time_idx=0
    col_string=''; enter_string = '';
    for event in events:
        arg1,event_name,arg2=event
        
        if event_name =='Collision':
            
            dict_attrs1, obj1_idx = get_attrs_idx(arg1,objects)
            

            dict_attrs2, obj2_idx = get_attrs_idx(arg2,objects)
            
            
            col_string += f'collision({obj1_idx},{obj2_idx},{time_idx}).\n'
            time_idx+=1
        elif event_name == 'ContainerEndUp':
            
            if 'basket' in arg1:
                pass
            elif 'basket' in arg2:
                arg2, _, arg1 = event
            dict_attrs1, obj1_idx = get_attrs_idx(arg1,objects)
            dict_attrs2, obj2_idx = get_attrs_idx(arg2,objects)
            
            
            enter_string+=f'enter({obj2_idx},{obj1_idx},{time_idx}).\n'
            time_idx+=1
            
            
    return col_string + enter_string


def create_collision_string(collision):
    
    obj1_initial,_,obj2_initial = collision
    
    if obj1_initial[2] in ['basket','container', 'bucket', 'floor','ground']:
        obj2,_,obj1 = collision
    else:
        obj1,_,obj2 = collision
    
    
    part1 = ' '.join(obj1)
    part1=part1[0].upper()+part1[1:]
    part2= ' collides with '
    if obj2[2] in ['basket','container', 'bucket', 'floor','ground']:
        part3= obj2[2]+'. ' #'basket. '
    else:
        part3 = ' '.join(obj2) +'. '
    
    final_string=part1+part2+part3
    return final_string

def create_basket_string(event):

    obj1_initial,_,obj2_initial = event
    
    if obj1_initial[2]=='basket':
        obj2,_,obj1 = event
    else:
        obj1,_,obj2 = event

    part1 = ' '.join(obj1)
    part1=part1[0].upper()+part1[1:]
    part2= ' enters '
    part3 = ' '.join(obj2) +'.'
    part3 = 'basket.'
    
    final_string=part1+part2+part3
    return final_string


def get_description(video_idx,data,obj_dict,generated_descriptions):
    sample=data[video_idx]
    for obj in sample['original_video_output']['scene_states'][1]['scene']['objects']:
        obj_id=obj['uniqueID']
        color=obj['color']
        size=obj['size']
        shape=obj['shape']
        
        obj_dict[obj_id]={'color':color,'size':size,'shape':shape}
        
    nodes= sample['original_video_output']['causal_graph']['nodes']
    edges= sample['original_video_output']['causal_graph']['edges']
    
    events = list()
    for node in nodes:
        event = node['type']
        
        if len(node['objects'])>0:
            obj1,obj2=node['objects']
        else:
            obj1,obj2=None,None
        
        if obj1 is not None:
            
            obj1_size = obj_dict[obj1]['size']
            obj1_color=obj_dict[obj1]['color']
            obj1_shape=obj_dict[obj1]['shape']
            
            obj2_size = obj_dict[obj2]['size']
            obj2_color=obj_dict[obj2]['color']
            obj2_shape=obj_dict[obj2]['shape']
            
            if (obj1_shape in EXCLUDE_EVENTS) or (obj2_shape in EXCLUDE_EVENTS):
                continue
            
            events.append([(obj1_size,obj1_color,obj1_shape),event,(obj2_size,obj2_color,obj2_shape)])
        else:
            events.append([obj1,event,obj2])

    res = map(list, unique(map(tuple, events)))
    reduced_events = list(res)
    
    desc_string = ''
    for e in reduced_events:
        if e[1]=='Start':
            desc_string+='Start. '
        elif e[1]=='End':
            desc_string+=' End.'
        elif e[1]=='Collision':
            desc_string+=create_collision_string(e)
        elif e[1]=='StartTouching':
            pass
        elif e[1]=='ContainerEndUp':
            desc_string+=create_basket_string(e)
            
    #reduced_events_no_touching=[red for red in reduced_events if 'Touching' not in red[1]]
    #return desc_string.replace('  ',' '),reduced_events_no_touching
    return generated_descriptions[str(video_idx)],parse_description(generated_descriptions[str(video_idx)])

def parse_description(desc):
    """
    Return parsed description
    - args: desc(str)
    - return: events(list)
    """
    events = []
    sentences=desc.split('.')
    for sent in sentences:
        event=''
        if 'Start' in sent:
            event = [None,'Start', None]
        elif 'End' in sent:
            event = [None,'End', None]
        elif 'collides' in sent:
            o1, o2 = sent.split('collides with')
            
            if any([True for obj in ['bucket','basket','container'] if obj in o1.split()]):
                o1_attrs = ['large','black','basket']
            elif any([True for obj in ['floor','ground'] if obj in o1.split()]):
                o1_attrs = ['large','black','ground']
            else:
                o1_attrs = [attr.lower() for attr in o1.split(' ') if attr!='']
            if any([True for obj in ['bucket','basket','container'] if obj in o2.split()]):
                    o2_attrs=['large','black','basket']
            elif any([True for obj in ['floor','ground'] if obj in o2.split()]):
                o2_attrs = ['large','black','ground']
            else:
                o2_attrs = [attr.lower() for attr in o2.split(' ') if attr!='']
                
            event = [tuple(o1_attrs), 'Collision', tuple(o2_attrs)]
        elif 'enters' in sent:
            o1, o2 = sent.split('enters ')
            o1_attrs = [attr.lower() for attr in o1.split(' ') if attr!='']

            event = [('large', 'black', 'basket'),'ContainerEndUp', tuple (o1_attrs)]
        if event!='':
            events.append(event)
    return events
