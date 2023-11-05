from nltk import word_tokenize as tokenize
from clyngor import solve

colors={'gray', 'red', 'blue', 'green', 'brown', 'cyan', 'purple', 'yellow'}
shapes={'cube', 'sphere', 'cylinder'}
materials={'metal', 'rubber'}

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

def write_n_run(sim, question,choices, args):
    """
    Return answer set facts corresponding to answer/2 and sim/2
    - args: sim(simulation object), question(str), choices(list), args
    - return: answer_facts(dict), sims(dict)
    """
    obj_attributes,moving,stationary,events,unseen_events=get_base_facts(sim,args)
    ASP_facts=get_base_ASP(obj_attributes,moving,stationary,events,unseen_events)
    
    partial_ASP_program=create_ASP_query(question,choices)
    default_program=ASP_facts + partial_ASP_program
    temp_ASP=open('temp_ASP.lp','w')
    temp_ASP.write(default_program)
    temp_ASP.close()
    clingo_solved=solve('temp_ASP.lp')
    all_lines=[]
    for line in clingo_solved:
        all_lines.append(line)

    answer_facts=[fact for fact in list(all_lines[0]) if 'answer' in fact]
    answer_facts=[(int(str(ans[1][0])[-1]),ans[1][1]) for ans in answer_facts]
    answer_facts={item[0]:item[1] for item in answer_facts}
    
    
    sims=[fact for fact in list(all_lines[0]) if 'sim' in fact]
    sims=[(sim[1][0],sim[1][1]) for sim in sims]
    sims={sim[0]:sim[1] for sim in sims}


    return answer_facts,sims


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


def create_ASP_query(question,choices):
    """
    Return facts for ASP program
    - args: question(str), program(str)
    - return: complete ASP program
    """

    part3='''
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Rules as interface to turn the above atoms into more general forms
%   * New atoms:
%      counterfact(remove, qobj(I))
%      option(OptionIdx, qobj(I1), Event, qobj(I2))
%      feature(qobj(I), Feature)
%      query(negated)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

counterfact(remove, qobj(0)).

option(C, qobj(C*10 + 1), collide, qobj(C*10 + 2)) :- choice(C,_,_).

feature(qobj(0), Feature) :- question(_,Feature).
feature(qobj(C*10 + I), Feature) :- choice(C, I, Feature).

query(negated) :- question(no,_).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Supress warnings of "atom does not occur in any rule head"
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#defined size/2.
#defined enter/3.
#defined query/3.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Helper atoms
%   * turn size/2, color/2, shape/2 into feature/3 and feature/2
%   * immovable/1 denotes "background" objects that will never move
%   * event/4 denotes the events in {collide, enter}
%   * pos_result/1 denotes the possible result in {yes, no}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

feature(O, size, V) :- size(O, V).
feature(O, color, V) :- color(O, V).
feature(O, shape, V) :- shape(O, V).
feature(O, material, V) :- material(O, V).

feature(O, V) :- feature(O, _, V).

immovable(O) :- feature(O, shape, basket).
immovable(O) :- feature(O, shape, ground).

event(O1, collide, O2, Frame) :- collision(O1, O2, Frame).
event(O1, enter, O2, Frame) :- enter(O1, O2, Frame).

pos_result(yes; no).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Rules for ancestor and simulation
%   * ancestor/4 determines the ancestor relationships between 2 collisions
%   * same/2 identify the objects in query with the objects in video
%   * removed/1 denotes the removed object(s)
%   * sim/2 denotes which frame to start simulation for an object
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%




% Find all timestamps to be considered in the causal graph
timestamp(T) :- collision(_,_,T).
timestamp(T) :- enter(_,_,T).



% Collision is symmetric

collision(O2,O1,FRAME) :- collision(O1,O2,FRAME).

% the collision of O1 at frame F1 is the ancestor of the collision of O2 at frame F2
% - if movable objects O1 and O2 collide at frame F1, and later, O2 collide at frame F2, or
% - if the collision of O1 at F1 is the ancestor of the collision of O3 at F3, which is further the ancestor of the collision of O2 at F2.

%ancestor(O1,F1,O2,F2) :- collision(O1,O2,F1), collision(O2,_,F2), F1<=F2, O1!=O2,
%    not immovable(O1), not immovable(O2).

%ancestor(O1,F1,O2,F2) :- ancestor(O1,F1,O3,F3), ancestor(O3,F3,O2,F2), O1!=O2.


% ancestor
ancestor(O,T1,O,T2) :- feature(O,_,_), timestamp(T1), timestamp(T2), T1<T2, not immovable(O).
ancestor(O1,T,O2,T) :- collision(O1,O2,T), not immovable(O1), not immovable(O2).
ancestor(O1,T1,O2,T2) :- ancestor(O1,T1,O3,T3), ancestor(O3,T3,O2,T2), (O1,T1)!=(O2,T2).


% Each object in query should be the same as an object in video

same(qobj(I), O) :- feature(O,_,_), feature(qobj(I),_), feature(O,_,F): feature(qobj(I),F).

% Define removed object(s)

removed(O) :- counterfact(remove, qobj(I)), same(qobj(I), O).


affected(O,T) :- removed(O), collision(_,_,T).
affected(O,T) :- removed(O'), ancestor(O',T',O,T).
affected(O,T) :- counterfact(remove, any), ancestor(_,_,O,T).                 
                         
sim(O,T) :- not removed(O), affected(O,T), T<=T': affected(O,T').

% condition 2: collision happens before simulation is needed for the 2 objects
determined(Q, yes) :- option(Q, qobj(I1), Event, qobj(I2)), 
    same(qobj(I1), O1), same(qobj(I2),O2),
    event(O1, Event, O2, F),
    not affected(O1,F), not affected(O2,F).

% condition 1: object in question is removed
determined(Q, no) :- option(Q, qobj(I1), Event, qobj(I2)), 
    same(qobj(I1), O1), same(qobj(I2),O2),
    removed(O1): not removed(O2).

% condition 3: collision not happen and no similation is needed for the 2 objects
determined(Q, no) :- option(Q, qobj(I1), Event, qobj(I2)), 
    same(qobj(I1), O1), same(qobj(I2),O2),
    not event(O1, Event, O2, _),
    not affected(O1,_), not affected(O2,_).


% we answer negated result if the query is asking about an event not happening

answer(Idx, Ans) :- determined(Idx, Res), 
    pos_result(Res), pos_result(Ans),
    Res = Ans: not query(negated);
    Res != Ans: query(negated).

% we answer the count if the query is about counting events

answer(N) :- query(counting, Event, qobj(I)), 
    same(qobj(I), O),
    N = #count{Ox: event(Ox,Event,O,_), not removed(Ox)},
    not sim(Ox,_): feature(Ox,_,_).

% we answer tbd if no result is predicted

{answer(Idx, tbd)} :- option(Idx,_,_,_).
:- option(Idx,_,_,_), #count{Res: answer(Idx, Res)} = 0.
:- option(Idx,_,_,_), answer(Idx, tbd), #count{Res: answer(Idx, Res)} > 1.

#show answer/2.
#show sim/2.
#show removed/1.'''

    question_string,negate_string=get_question_string(question)
    choices_string=''
    for c_idx, choice in enumerate(choices):
        choice_string=get_choice_strings(choice,c_idx)    
        choices_string+=choice_string+'\n\n'
    
    initial_lp_partial=question_string + '\n' + choices_string
    causal_lp = part3 + '\n' 
    return initial_lp_partial + causal_lp


def get_base_ASP(obj_attributes,moving,stationary,events,unseen_events):
    """
    Returns ASP facts
    - args: obj_attributes,moving(list),stationary(list),events(list),unseen_events(list)
    - return: partial input.lp string
    """
    # =============================================================================
    # Object Attributes
    # =============================================================================

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
            pass
            #events_string+='enter({0},{1}). \n'.format(event['object'][0],event['frame'])
        elif event['type']=='collision':
            events_string+='collision({0},{1},{2}). \n'.format(event['object'][0],event['object'][1],event['frame'])


# =============================================================================
#     Unseen Events
# =============================================================================

    unseen_events_string=''
    for event in unseen_events:
        if event['type']=='in':
            unseen_events_string+='enter({0},{1}). \n'.format(event['object'][0],event['frame'])
        elif event['type']=='collision':
            unseen_events_string+='collision({0},{1},{2}). \n'.format(event['object'][0],event['object'][1],event['frame'])



    final_string=attributes_string +  '\n\n' +events_string+ '\n' + unseen_events_string + '\n\n'

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

    frame_range=range(0,128) if args.IOD else range(0,125,5)

    moving=[];stationary=[]
    for frame_num in frame_range:
        moving.append(filter_moving(sim, [i for i in range(num_of_objects)],frame_num))
        stationary.append(filter_stationary(sim, [i for i in range(num_of_objects)],frame_num))
    events=_events(sim)
    unseen_events=_get_unseen_events(sim)

    return obj_attributes, moving,stationary,events,unseen_events

