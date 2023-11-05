from nltk import word_tokenize as tokenize
from clyngor import solve,ASP
from ASP_PE import ASP_PE
import pickle

colors={'gray', 'red', 'blue', 'green', 'brown', 'cyan', 'purple', 'yellow'}
shapes={'cube', 'sphere', 'cylinder'}
materials={'metal', 'rubber'}
movements = {'moving','stationary'}
times = {'begin', 'end'}
orders = {'first', 'second', 'last', 'before', 'after'}
events = {'enter', 'exit', 'collide', 'collision'}
attr_types = {'color','shape','material'}


import openai

openai.api_type = "azure"
#openai.api_key = "1e243647f78d43acbaee95dc9443641f"
openai.api_key = "eee5674e74c2413ea53b77841ba62a5a"
openai.api_base = "https://aim.openai.azure.com/"
openai.api_version = "2022-03-01-preview"


class QueryParser():
    def __init__(
            self, load_file = 'prompt_cache.pickle'):
        if load_file:
            with open('prompt_cache.pickle', 'rb') as handle:
                prompt_cache = pickle.load(handle)
        else:
            prompt_cache = dict()
        self.prompt_cache=prompt_cache
    def get_response(self,prompt,temp=0.,max_tokens=30):
        return openai.Completion.create(engine="text-davinci-002", prompt=prompt, temperature=temp, max_tokens=max_tokens)
    def save(self,fname='prompt_cache.pickle'):
        with open(fname, 'wb') as handle:
            pickle.dump(self.prompt_cache, handle, protocol=pickle.HIGHEST_PROTOCOL)



def get_attr(sentence):
    
    
    attrs = {'static':[],'moving':[],'time':[]}
    static_attrs = []
    static_attrs+= [color for color in colors if color in sentence]
    static_attrs+= [shape for shape in shapes if shape in sentence]
    static_attrs+= [material for material in materials if material in sentence]
    
    attrs['static']=static_attrs
    
    attrs['moving'] =  [movement for movement in movements if movement in sentence]
    attrs['time'] =  [time for time in times if time in sentence]
    attrs['events'] = [event for event in events if event in sentence]
    attrs['attr_type'] = [attr_type for attr_type in attr_types if attr_type in sentence]
    attrs['orders'] = [order for order in orders if order in sentence]
    
    if 'collide' in sentence:
        attrs['collide']=True
    else:
        attrs['collide']=False

    return attrs 

def get_attrs(question):
    
    splitting_words = ['when', 'before', 'after']
    
    split_words = [word for word in splitting_words if word in question]
    
    split1,split2 = question.split(split_words[0]) if len(split_words)>0 else [question,'']
    
    if split2!='':
        split2 = split_words[0]+split2
    #breakpoint()
    
    attrs1 = get_attr(split1)
    attrs2 = get_attr(split2)
    
    return attrs1, attrs2


def attrs_to_string(q_subtype,attrs1,attrs2,question):
    #breakpoint()
    if q_subtype=='any':
        if len(attrs1['moving'])==1:
            #breakpoint()
            if len(attrs2['time'])==1:
                query_fact = f'query(any,{attrs1["moving"][0]})'
                when_fact = f'when({attrs2["time"][0]})'
                obj_desc1 = '.'.join([f'desc(1,{attr})' for attr in attrs1['static']])
                full_string = '.'.join(filter(None,[query_fact,obj_desc1,when_fact])) +'.'
                return full_string
            elif len(attrs2['events'])==1:
                query_fact = f'query(any,{attrs1["moving"][0]})'
                obj_desc1 = '.'.join([f'desc(1,{attr})' for attr in attrs1['static']])
                obj_desc2 = '.'.join([f'desc(2,{attr})' for attr in attrs2['static']])
                events= f'action({attrs2["events"][0]})'
                full_string = '.'.join(filter(None,[query_fact,obj_desc1, obj_desc2, events])) +'.'
                return full_string
            else:
                query_fact = f'query(any,{attrs1["moving"][0]})'
                obj_desc1 = '.'.join([f'desc(1,{attr})' for attr in attrs1['static']])
                full_string = '.'.join(filter(None,[query_fact,obj_desc1])) +'.'
                return full_string
        elif len(attrs1['events'])==1:
            if len(attrs2['events'])==1:
                query_fact = f'query(any,{attrs1["events"][0]})'
                obj_desc1 = '.'.join([f'desc(1,{attr})' for attr in attrs1['static']])
                obj_desc2 = '.'.join([f'desc(2,{attr})' for attr in attrs2['static']])
                events1= f'action({attrs1["events"][0]})' 
                events2= f'action({attrs2["events"][0]})'
                order= f'order({attrs2["orders"][0]})'
                full_string = '.'.join(filter(None,[query_fact,obj_desc1,obj_desc2, events1, events2, order])) +'.'
                return full_string
            else:
                #attrs1['events'][0]=='enter':
                query_fact = f'query(any,{attrs1["events"][0]})'
                obj_desc1 = '.'.join([f'desc(1,{attr})' for attr in attrs1['static']])
                full_string = '.'.join(filter(None,[query_fact,obj_desc1])) +'.'
                return full_string
    if q_subtype=='howMany':
        if len(attrs1['moving'])==1:
            query_fact = f'query(howMany,{attrs1["moving"][0]})'
            obj_facts1= [f'desc(1,{attr})' for attr in attrs1['static']]
            obj_facts2 = [f'desc(2,{attr})' for attr in attrs2['static']]
            if len(attrs2['time'])==1:
                when_fact = f'when({attrs2["time"][0]})'
                obj_facts2+= [when_fact]
            if len(attrs2['events'])==1:
                events= f'action({attrs2["events"][0]})'
                obj_facts2+=[events]
            obj_desc1 = '.'.join(obj_facts1)
            obj_desc2 = '.'.join(obj_facts2)
            full_string = '.'.join(filter(None,[query_fact,obj_desc1,obj_desc2])) + '.'
            return full_string
        elif len(attrs1['events'])==1:
            query_fact = f'query(howMany,{attrs1["events"][0]})'
            obj_facts1= [f'desc(1,{attr})' for attr in attrs1['static']]
            obj_facts2 = [f'desc(2,{attr})' for attr in attrs2['static']]
            if len(attrs2['time'])==1:
                when_fact = f'when({attrs2["time"][0]}).'
                obj_facts2+= [when_fact]
            if len(attrs2['events'])==1:
                events= f'action({attrs2["events"][0]})'
                obj_facts2+=[events]
            obj_desc1 = '.'.join(obj_facts1)
            obj_desc2 = '.'.join(obj_facts2)
            if len(attrs2['orders'])==1:
                order= f'order({attrs2["orders"][0]})'
            else:
                order=None
            full_string = '.'.join(filter(None,[query_fact,obj_desc1,obj_desc2,order])) + '.'
            return full_string
    if q_subtype=='what':
        if attrs1['collide']:
            #breakpoint()
            query_fact = f'query(what,{attrs1["attr_type"][0]})'
            obj_facts1= [f'desc(2,{attr})' for attr in attrs1['static']]
            obj_facts2 = ''
            if len(attrs1['time'])==1:
                when_fact = f'when({attrs1["time"][0]})'
                obj_facts1+= [when_fact]
            if len(attrs1['events'])==1:
                events= f'action({attrs1["events"][0]})'
                obj_facts1+=[events]
            if len(attrs1['orders'])==1:
                order= f'order({attrs1["orders"][0]})'
                obj_facts1+=[order]
            obj_desc1 = '.'.join(obj_facts1)
            obj_desc2 = '.'.join(obj_facts2)
            full_string = '.'.join([query_fact,obj_desc1]) + '.'
            return full_string
        elif len(attrs1['attr_type'])>0:
            #breakpoint()
            query_fact = f'query(what,{attrs1["attr_type"][0]})'
            obj_facts1= [f'desc(1,{attr})' for attr in attrs1['static']]
            obj_facts2 = [f'desc(2,{attr})' for attr in attrs2['static']]
            if len(attrs1['time'])==1:
                when_fact = f'when({attrs1["time"][0]})'
                obj_facts1+= [when_fact]
            if len(attrs2['time'])==1:
                when_fact = f'when({attrs2["time"][0]})'
                obj_facts1+= [when_fact]
            
            if len(attrs1['events'])==1:
                events= f'action({attrs1["events"][0]})'
                obj_facts1+=[events]
            if len(attrs1['orders'])==1:
                order= f'order({attrs1["orders"][0]})'
                obj_facts1+=[order]
            if len(attrs1['moving'])==1:
                obj_facts1+=[f'is({attrs1["moving"][0]})']
            
            if len(attrs2['events'])==1:
                obj_facts2+=[f'when({attrs2["events"][0]})']
            obj_desc1 = '.'.join(obj_facts1)
            obj_desc2 = '.'.join(obj_facts2)
            full_string = '.'.join([query_fact,obj_desc1,obj_desc2])
            if full_string[-1]!='.':
                full_string+='.'
            return full_string
        
        breakpoint()
    
def process_question(question):
    

    
    #breakpoint()
    # =============================================================================
    # Descriptive Questions
    # =============================================================================
    attrs1,attrs2 = get_attrs(question)
    
    # =============================================================================
    # are there
    # =============================================================================
    if 'Are there' in question:
        
        if 'exit' in question or 'enter' in question:
            if any(s in question for s in ['when','after','before']):
                if 'when' in question:
                    #breakpoint()
                    return attrs_to_string('any',attrs1,attrs2,question)
                elif 'collision' not in question:
                    #breakpoint()
                    return attrs_to_string('any',attrs1,attrs2,question)
                else:
                    return attrs_to_string('any',attrs1,attrs2,question)
                    breakpoint()
            else:
                #breakpoint()
                return attrs_to_string('any',attrs1,attrs2,question)
        elif 'begin' in question or 'end' in question:
            #breakpoint()
            return attrs_to_string('any',attrs1,attrs2,question)
            return f'query(any,{attrs1["moving"][0]}), desc(1,green), when(ends).'
        elif 'moving' in question or 'stationary' in question:
            #breakpoint()
            return attrs_to_string('any',attrs1,attrs2,question)
        elif 'collisions' in question:
            #breakpoint()
            return attrs_to_string('any',attrs1,attrs2,question)
            
        else:
            raise ValueError('Pattern not recognized.')
    
 
    # =============================================================================
    # how many
    # =============================================================================
    
    elif 'How many' in question:
        if 'exit' in question or 'enter' in question:
            if any(s in question for s in ['when','after','before']):
                if 'when' in question:
                    if 'there' not in question:
                        #breakpoint()
                        return attrs_to_string('howMany',attrs1,attrs2,question)
                        return 'query(howMany, stationary), desc(2,yellow), when(enters).'
                    else:
                        #breakpoint()
                        return attrs_to_string('howMany',attrs1,attrs2,question)
                elif 'collision' not in question:
                    #breakpoint()
                    return attrs_to_string('howMany',attrs1,attrs2,question)
                else:
                    #breakpoint() ###
                    return attrs_to_string('howMany',attrs1,attrs2,question)
            else:
                #breakpoint()
                return attrs_to_string('howMany',attrs1,attrs2,question)
        elif 'begin' in question or 'end' in question:
            if 'there' not in question:
                #breakpoint()
                return attrs_to_string('howMany',attrs1,attrs2,question)
            else:
                return attrs_to_string('howMany',attrs1,attrs2,question)
                return 'query(howMany, moving), when(ends).'
        elif 'moving' in question or 'stationary' in question:
            if 'there' not in question:
                #breakpoint()
                return attrs_to_string('howMany',attrs1,attrs2,question)
            else:
                #breakpoint()
                return attrs_to_string('howMany',attrs1,attrs2,question)
        elif 'collisions happen' in question:
            return attrs_to_string('howMany',attrs1,attrs2,question)
            breakpoint()
        else:
            raise ValueError('Pattern not recognized.')

    
    # =============================================================================
    # what
    # =============================================================================

    elif 'What' in question:
        if 'What is' in question:
            if 'collide' in question: 
                return attrs_to_string('what',attrs1,attrs2,question) #same 1 
                breakpoint()
            elif 'when' in question:
                if 'video' in question:
                    #breakpoint()
                    return attrs_to_string('what',attrs1,attrs2,question)
                else:
                    if 'that' in question:
                        #breakpoint()
                        return attrs_to_string('what',attrs1,attrs2,question)
                    else:
                        #breakpoint()
                        return attrs_to_string('what',attrs1,attrs2,question)
            else:
                if 'scene' in question:
                    #breakpoint()
                    return attrs_to_string('what',attrs1,attrs2,question)
                else:
                    if 'that' in question:
                        #breakpoint()
                        return attrs_to_string('what',attrs1,attrs2,question)
                    else:
                        #breakpoint()
                        return attrs_to_string('what',attrs1,attrs2,question)
        elif 'What' in question:
            if 'collide' in question:
                #breakpoint()
                return attrs_to_string('what',attrs1,attrs2,question) #same 2 
            elif 'when' in question:
                if 'video' in question:
                    #breakpoint()
                    return attrs_to_string('what',attrs1,attrs2,question)
                else:
                    if 'that' in question:
                        #breakpoint() ##
                        return attrs_to_string('what',attrs1,attrs2,question)
                    else:
                        #breakpoint()
                        return attrs_to_string('what',attrs1,attrs2,question)
            else:
                if 'scene' in question:
                    #breakpoint()
                    return attrs_to_string('what',attrs1,attrs2,question)
                else:
                    if 'that' in question:
                        #breakpoint()
                        return attrs_to_string('what',attrs1,attrs2,question)
                    else:
                        #breakpoint()
                        return attrs_to_string('what',attrs1,attrs2,question)
        else:
            raise ValueError('Pattern not recognized.')
    
    else:
        raise ValueError('Pattern not recognized.')







def filter_moving(sim, objs, frame):
    """
    Filter all moving objects in the input list
    - args: sim(simulation object), objects(list), frame(int)
    - return: objects(list)
    """
    if type(objs) is not list:
        return 'error'
    if type(frame) is not int and frame != 'null':
        return 'error'
    if frame == 'null':
        frame = None
    output_objs = []
    for o in objs:
        if sim.is_visible(o, frame_idx=frame) and \
           sim.is_moving(o, frame_idx=frame):
            output_objs.append(o)
    return output_objs

def filter_stationary(sim, objs, frame):
    """
    Filter all moving objects in the input list
    - args: sim(simulation object), objects(list), frame(int)
    - return: objects(list)
    """
    if type(objs) is not list:
        return 'error'
    if type(frame) is not int and frame != 'null':
        return 'error'
    if frame == 'null':
        frame = None
    output_objs = []
    for o in objs:
        if sim.is_visible(o, frame_idx=frame) and \
           not sim.is_moving(o, frame_idx=frame):
            output_objs.append(o)
    return output_objs

def _events(sim):
    """
    Return full event list sorted in time order
    - args: sim(simulation object)
    - return: events(list)
    """
    events = _get_events(sim)[:]
    events = sorted(events, key=lambda k: k['frame'])
    return events


def _convert_event_idx_cf2gt(sim, event, drop_idx):
    event_objs_converted = []
    for o in event['object']:
        if o >= drop_idx:
            event_objs_converted.append(o+1)
        else:
            event_objs_converted.append(o)
    event['object'] = event_objs_converted
    return event

def _get_events(sim, drop_idx=None):
    events = [
        {
            'type': 'start',
            'frame': 0,
        },
        {
            'type': 'end',
            'frame': 125,
        },
    ]
    for io in sim.in_out:
        if io['frame'] < sim.n_vis_frames:
            io_event = {
                'type': io['type'],
                'object': io['object'],
                'frame': io['frame'],
            }
            if drop_idx is not None:
                io_event = _convert_event_idx_cf2gt(io_event, drop_idx)
            events.append(io_event)
    for c in sim.collisions:
        if c['frame'] < sim.n_vis_frames:
            col_event = {
                'type': 'collision',
                'object': c['object'],
                'frame': c['frame']
            }
            if drop_idx is not None:
                col_event = _convert_event_idx_cf2gt(col_event, drop_idx)
            events.append(col_event)
    return events




def _get_unseen_events(sim):
    """Return a list of events (time_indicators) of events that are 
    going to happen
    """
    unseen_events = []
    for io in sim.in_out:
        if io['frame'] >= sim.n_vis_frames:
            io_event = {
                'type': io['type'],
                'object': [io['object']],
                'frame': io['frame'],
            }
            unseen_events.append(io_event)
    for c in sim.collisions:
        if c['frame'] >= sim.n_vis_frames:
            col_event = {
                'type': 'collision',
                'object': c['object'],
                'frame': c['frame'],
            }
            unseen_events.append(col_event)
    return unseen_events

def write_n_run(sim, question, args):
    """
    Return answer set facts corresponding to answer/2 and sim/2
    - args:
    - return: answer_facts(dict), sims(dict)
    """
    if 'Are there any stationary objects?' in question:
        pass#breakpoint()
    query_string = process_question(question)
    obj_attributes,moving,stationary,events,unseen_events=get_base_facts(sim,args)
    ASP_facts=get_base_ASP(obj_attributes,moving,stationary,events,unseen_events,args)
    
    partial_ASP_program=create_ASP_query(question)
    default_program=ASP_facts + partial_ASP_program + query_string
    
    temp_ASP=open('temp_ASP.lp','w')
    temp_ASP.write(default_program)
    temp_ASP.close()
    clingo_solved=solve('temp_ASP.lp', options='--warn none')
    
    all_lines=[]
    for line in clingo_solved:
        all_lines.append(line)

    answer_facts=[fact for fact in list(all_lines[0]) if 'answer' in fact]
    if len(answer_facts)!=0:
        return answer_facts[0][1][0], query_string
    else:
        return 'error', query_string

def get_question_string(q):
    """
    Return facts for ASP program
    - args: q(string)
    - return: obj1_string(string), negate_string(string)
    """
    split_words=tokenize(q)
    negate='not' in split_words
    negate_string='no' if negate else 'yes'
    objq_string=''
    #breakpoint()
    for word in split_words:
        if word in colors:
            string='question({0},{1}).'.format(negate_string,word)
        elif word in shapes:
            string='question({0},{1}).'.format(negate_string,word)
        elif word in materials:
            string='question({0},{1}).'.format(negate_string,word)
        else:
            continue
        objq_string+=string 
    objq_string+='\n'
    return objq_string,negate_string


def get_choice_strings(c,choice_num):
    """
    Return facts for ASP program
    - args: c(string), choice_num(int)
    - return: choice string for ASP program
    """
    if 'with' in c:
        split1,split2=c.split('with')
    elif 'and' in c:
        split1,split2=c.split('and')

    split1_words=tokenize(split1)
    split2_words=tokenize(split2)

    obj1_string=''
    for word in split1_words:
        if word in colors:
            string='choice({0}, 1, {1}).'.format(choice_num,word)
        elif word in shapes:
            string='choice({0}, 1, {1}).'.format(choice_num,word)
        elif word in materials:
            string='choice({0}, 1, {1}).'.format(choice_num,word)
        else:
            continue
        obj1_string+=string

    obj2_string=''
    for word in split2_words:
        if word in colors:
            string='choice({0}, 2, {1}).'.format(choice_num,word)
        elif word in shapes:
            string='choice({0}, 2, {1}).'.format(choice_num,word)
        elif word in materials:
            string='choice({0}, 2, {1}).'.format(choice_num,word)
        else:
            continue
        obj2_string+=string


    return obj1_string+'\n'+ obj2_string


def create_ASP_query(question):

    """
    Return facts for ASP program
    - args: question(str), program(str)
    - return: complete ASP program
    """

    question_string,negate_string=get_question_string(question)
    
    initial_lp_partial=question_string
    causal_lp = ASP_PE + '#show answer/1. ' + '\n' 
    return initial_lp_partial + causal_lp


def get_base_ASP(obj_attributes,moving,stationary,events,unseen_events, args):
    """
    Returns ASP facts
    - args: obj_attributes,moving(list),stationary(list),events(list),unseen_events(list)
    - return: partial input.lp string
    """
    # =============================================================================
    # Object Attributes
    # =============================================================================
    #frame_diff = 5 if not args.IOD else 1 
    frame_diff = 5 #if not args.IOD else 1 
    attributes_string=''
    for obj_idx,obj in enumerate(obj_attributes):

        attrs=[]
        for key in obj:
            attrs.append(obj[key])
        attributes_string+='color({0},{1}). material({0},{2}). shape({0},{3}).\n'.format(obj_idx,*attrs)


    # =============================================================================
    # Moving
    # =============================================================================
    moving_string=''
    for frame_idx,move in enumerate(moving):
        line=''
        for obj in move:
            line+='moving({0},{1}).'.format(obj,frame_idx*frame_diff)
        if line:
            moving_string+=line +'\n'


    # =============================================================================
    # Stationary
    # =============================================================================

    stationary_string=''

    for frame_idx,move in enumerate(stationary):
        line=''
        for obj in move:
            line+='stationary({0},{1}).'.format(obj,frame_idx*frame_diff)
        if line:
            stationary_string+=line+'\n'

    # =============================================================================
    #     Events
    # =============================================================================

    events_string=''

    for event in events:
        if event['type']=='in':
            pass
            events_string+='enter({0},{1}). \n'.format(event['object'][0],event['frame'])
        elif event['type']=='out':
            events_string+='exit({0},{1}). \n'.format(event['object'][0],event['frame'])
        elif event['type']=='collision':
            events_string+='collision({0},{1},{2}). \n'.format(event['object'][0],event['object'][1],event['frame'])


# =============================================================================
#     Unseen Events
# =============================================================================

    unseen_events_string=''
    for event in unseen_events:
        if event['type']=='in':
            pass
            #unseen_events_string+='enter({0},{1}). \n'.format(event['object'][0],event['frame'])
        elif event['type']=='collision':
            pass # don't include post-video events 
            #unseen_events_string+='collision({0},{1},{2}). \n'.format(event['object'][0],event['object'][1],event['frame'])



    final_string=attributes_string +  '\n\n' + stationary_string + moving_string +events_string+ '\n' + unseen_events_string + '\n\n'

    return final_string



def get_base_facts(sim,args):
    """
    Return base facts of the scene
    - args: sim(simulation object), args
    - return: base facts from scene
    """
    num_of_objects=len(sim.get_visible_objs())
    obj_attributes=[]
    for i in range(num_of_objects):
        obj_attributes.append(sim.get_static_attrs(i))

    #frame_range=range(0,128) if args.IOD else range(0,125+5,5)
    frame_range=range(0,125+5,5)
    moving=[];stationary=[]
    for frame_num in frame_range:
        moving.append(filter_moving(sim, [i for i in range(num_of_objects)],frame_num))
        stationary.append(filter_stationary(sim, [i for i in range(num_of_objects)],frame_num))
    events=_events(sim)
    unseen_events=_get_unseen_events(sim)

    return obj_attributes, moving,stationary,events,unseen_events

