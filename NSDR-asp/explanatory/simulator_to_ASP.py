from clyngor import ASP, solve
from nltk import word_tokenize as tokenize
from ASP_PE import ASP_PE

colors={'gray', 'red', 'blue', 'green', 'brown', 'cyan', 'purple', 'yellow'}
shapes={'cube', 'sphere', 'cylinder'}
materials={'metal', 'rubber'}


def filter_moving(sim, objs, frame):
    """
    Filter all moving objects in the input list
    - args: objects(list), frame(int)
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
    - args: objects(list), frame(int)
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
    - args:
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


def get_question_string(q):

    split_words=tokenize(q)
    negate='not' in split_words
    negate_string='no' if negate else 'yes'
    
    single_object=False
    if 'with' in q:
        split1,split2=q.split('with')
    elif 'and' in q:
        split1,split2=q.split('and')
    else:
        single_object=True
        split1=q

    split1_words=tokenize(split1)
    if not single_object:
        split2_words=tokenize(split2)

    obj1_string=''
    for word in split1_words:
        if word in colors:
            string='question({0}, 1, {1}).'.format(negate_string,word)
        elif word in shapes:
            string='question({0}, 1, {1}).'.format(negate_string,word)
        elif word in materials:
            string='question({0}, 1, {1}).'.format(negate_string,word)
        else:
            continue
        obj1_string+=string

    if single_object:
        return obj1_string

    obj2_string=''
    for word in split2_words:
        if word in colors:
            string='question({0}, 2, {1}).'.format(negate_string,word)
        elif word in shapes:
            string='question({0}, 2, {1}).'.format(negate_string,word)
        elif word in materials:
            string='question({0}, 2, {1}).'.format(negate_string,word)
        else:
            continue
        obj2_string+=string

    return obj1_string+'\n'+ obj2_string

def get_choice_strings(c,choice_num):

    single_object=False
    if 'with' in c:
        split1,split2=c.split('with')
    elif 'and' in c:
        split1,split2=c.split('and')
    else:
        single_object=True
        split1=c

    split1_words=tokenize(split1)
    if not single_object:
        split2_words=tokenize(split2)

    obj1_string=''
    for word in split1_words:
        if word in colors:
            string='choice(choice{0}, 1, {1}).'.format(choice_num,word)
        elif word in shapes:
            string='choice(choice{0}, 1, {1}).'.format(choice_num,word)
        elif word in materials:
            string='choice(choice{0}, 1, {1}).'.format(choice_num,word)
        else:
            continue
        obj1_string+=string

    if single_object:
        return obj1_string

    obj2_string=''
    for word in split2_words:
        if word in colors:
            string='choice(choice{0}, 2, {1}).'.format(choice_num,word)
        elif word in shapes:
            string='choice(choice{0}, 2, {1}).'.format(choice_num,word)
        elif word in materials:
            string='choice(choice{0}, 2, {1}).'.format(choice_num,word)
        else:
            continue
        obj2_string+=string


    return obj1_string+'\n'+ obj2_string

def create_question_choice_facts(question,choices):
    
    question_string=get_question_string(question)
    choices_string=''
    for c_idx, choice in enumerate(choices):
        choice_string=get_choice_strings(choice,c_idx)    
        choices_string+=choice_string+'\n\n'
    
    return  question_string + '\n' + choices_string

def get_base_facts(sim,args):
    #breakpoint()
    num_of_objects=len(sim.get_visible_objs())
    obj_attributes=[]
    for i in range(num_of_objects):
        obj_attributes.append(sim.get_static_attrs(i))

    frame_range=range(0,128) if args.IOD else range(0,125,5)

    moving=[];stationary=[]
    for frame_num in frame_range:
        moving.append(filter_moving(sim, [i for i in range(num_of_objects)],frame_num))
        stationary.append(filter_stationary(sim, [i for i in range(num_of_objects)],frame_num))
    events=_events(sim)
    unseen_events=_get_unseen_events(sim)

    return obj_attributes, moving,stationary,events,unseen_events

def base_facts_to_ASP(sim,args):
    # =============================================================================
    # Object Attributes
    # =============================================================================

    obj_attributes,moving,stationary,events,unseen_events=get_base_facts(sim,args)
    attributes_string=''
    for obj_idx,obj in enumerate(obj_attributes):

        attrs=[]
        for key in obj:
            attrs.append(obj[key])
        #breakpoint()
        attributes_string+='color({0},{1}). material({0},{2}). shape({0},{3}).\n'.format(obj_idx,*attrs)

    # =============================================================================
    # Moving
    # =============================================================================
    moving_string=''

    for frame_idx,move in enumerate(moving):
        line=''
        for obj in move:
            line+='moving({0},{1}).'.format(obj,frame_idx*1)
        if line:
            moving_string+=line +'\n'

    # =============================================================================
    # Stationary
    # =============================================================================

    stationary_string=''

    for frame_idx,move in enumerate(stationary):
        line=''
        for obj in move:
            line+='stationary({0},{1}).'.format(obj,frame_idx*1)
        if line:
            stationary_string+=line+'\n'

    # =============================================================================
    #     Events
    # =============================================================================

    events_string=''

    for event in events:
        if event['type']=='in':
            pass#events_string+='enter({0},{1}). \n'.format(event['object'][0],event['frame'])
        elif event['type']=='collision':
            events_string+='collision({0},{1},{2}). \n'.format(event['object'][0],event['object'][1],event['frame'])

# =============================================================================
#     Unseen Events
# =============================================================================
    unseen_events_string=''
    for event in unseen_events:
        if event['type']=='in':
            pass
        elif event['type']=='collision':
            unseen_events_string+='collision({0},{1},{2}). \n'.format(event['object'][0],event['object'][1],event['frame'])
    
    return attributes_string,events_string,unseen_events_string

def get_program(sim,question,choice,q_str,c_str,choices,args):

    attributes_string,events_string,unseen_events_string=base_facts_to_ASP(sim,args)
    question_choice_facts=create_question_choice_facts(q_str,choices)
    final_string=question_choice_facts+ '\n' + attributes_string +  '\n\n' +events_string+ '\n' + unseen_events_string + '\n'+ ASP_PE + '\n' + '#show answer/2.'
    return final_string

def write_n_run(sim,question,choice,q_str,c_str,choices,args):
    """
    Return answer set 
    - args: sim(simulation object),question(str),choice(str),q_str(str),c_str(str),choices(list),args
    - return: answer set (list)
    """
    ASP_program=get_program(sim,question,choice,q_str,c_str,choices,args)
    temp_ASP=open('temp_ASP.lp','w')
    temp_ASP.write(ASP_program)
    temp_ASP.close()
    clingo_solved=solve('temp_ASP.lp', options = '--warn none')
    all_lines=[]
    for line in clingo_solved:
        all_lines.append(line)
    
    return all_lines
