ASP_consolidated_3 = '''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Atoms that are assumed to be given
%   * atoms to represent the video
%   * atoms to represent the query
%     EX.
%       counterfact(remove, qobj(I))
%       counterfact(remove, any)
%       option(OptionIdx, qobj(I1), Event, qobj(I2)) where Event is in {collide, enter}
%       query(counting, Event, qobj(I2))
%       query(negated) -- whether the query is asking about something not happening
%       feature(qobj(I), Feature)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

option(1, qobj(I1), collide, qobj(I2)) :- query(collide(qobj(I1), qobj(I2))).
option(1, qobj(I1), enter, qobj(I2)) :- query(enter(qobj(I1), qobj(I2))).

answer(Ans) :- answer(_,Ans).

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

% Each object in query should be the same as an object in video

same(qobj(I), O) :- feature(O,_,_), feature(qobj(I),_), feature(O,_,F): feature(qobj(I),F).

% Define removed object(s)

removed(O) :- counterfact(remove, qobj(I)), same(qobj(I), O).

% Find all timestamps to be considered in the causal graph

timestamp(T) :- collision(_,_,T).
timestamp(T) :- enter(_,_,T).

% Collision is symmetric

collision(O1,O2,T) :- collision(O2,O1,T).

% ancestor

ancestor(O,T1,O,T2) :- feature(O,_,_), timestamp(T1), timestamp(T2), T1<T2, not immovable(O).
ancestor(O1,T,O2,T) :- collision(O1,O2,T), not immovable(O1), not immovable(O2).
ancestor(O1,T1,O2,T2) :- ancestor(O1,T1,O3,T3), ancestor(O3,T3,O2,T2), (O1,T1)!=(O2,T2).

% affected

affected(O,T) :- removed(O), collision(_,_,T).
affected(O,T) :- removed(O'), ancestor(O',T',O,T).
% If we can remove "anything", every node that has an ancestor is affected
affected(O,T) :- counterfact(remove, any), ancestor(O',_,O,T), O!=O'.
% sim node

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


#show sim/2.
#show answer/1.'''