


ASP_PE = '''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Rules as interface to turn the above atoms into more general forms
%   * New atoms:
%      option(OptionIdx, qobj(I1), Event, qobj(I2))
%      feature(qobj(I), Feature)
%      query(negated)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

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

#defined question/2.
#defined query/2.
#defined when/1.
#defined desc/2.
#defined moving/2.
#defined stationary/2.
#defined action/1.
#defined enter/2.
#defined order/1.
#defined exit/2.
#defined enter/2.
#defined ancestor/3.
#defined is/1.

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


% Collision is symmetric

collision(O2,O1,FRAME) :- collision(O1,O2,FRAME).

#const begin = 0. 
#const end = 125. 

pos_result(yes; no).

% Each object in query should be the same as an object in video
same(qobj(I), O) :- feature(O,_,_), feature(qobj(I),_), feature(O,_,F): feature(qobj(I),F).

% Queries
%*
%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% DESCRIPTIVE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% =============================================================================
% are there/are there any
% =============================================================================

% Any objects stationary/moving when video ends 


answer(yes):- stationary(O,FRAME), FRAME =T, query(any, stationary), when(T), feature(O,_,F): desc(1,F).
answer(no) :- not answer(yes), query(any, stationary), when(_).

answer(yes):- moving(O,FRAME), FRAME =T, query(any, moving),when(T), feature(O,_,F): desc(1,F).
answer(no) :- not answer(yes), query(any, moving), when(_).

% any stationary/moving objs when obj2 enters/exits
answer(yes):- stationary(O,FRAME), FRAME =T, query(any, stationary), action(enter), enter(O2,T), feature(O,_,F): desc(1,F); feature(O2,_,F): desc(2,F).
answer(no) :- not answer(yes), query(any, stationary), action(enter).

answer(yes):- moving(O,FRAME), FRAME =T, query(any, moving), action(enter), enter(O2,T), feature(O,_,F): desc(1,F); feature(O2,_,F): desc(2,F).
answer(no) :- not answer(yes), query(any, moving), action(enter).

answer(yes):- stationary(O,FRAME), FRAME =T, query(any, stationary), action(exit), exit(O2,T), feature(O,_,F): desc(1,F); feature(O2,_,F): desc(2,F).
answer(no) :- not answer(yes), query(any, stationary), action(exit).

answer(yes):- moving(O,FRAME), FRAME =T, query(any, moving), action(exit), exit(O2,T), feature(O,_,F): desc(1,F); feature(O2,_,F): desc(2,F).
answer(no) :- not answer(yes), query(any, moving), action(exit).


% any objs that enter before/after obj 2 enters/exits
answer(yes):- query(any, enter), action(enter), enter(O1,T1), enter(O2,T2), T1>T2, order(after), feature(O1,_,F3): desc(1,F3); feature(O2,_,F4): desc(2,F4).
answer(no) :- not answer(yes), query(any, enter), action(enter), order(after).

answer(yes):- query(any, enter), action(enter), enter(O1,T1), enter(O2,T2), T1<T2, order(before), feature(O1,_,F3): desc(1,F3); feature(O2,_,F4): desc(2,F4).
answer(no) :- not answer(yes), query(any, enter), action(enter), order(before).

answer(yes):- query(any, enter), action(exit), enter(O1,T1), exit(O2,T2), T1>T2, order(after), feature(O1,_,F3): desc(1,F3); feature(O2,_,F4): desc(2,F4).
answer(no) :- not answer(yes), query(any, enter), action(exit), order(after).

answer(yes):- query(any, enter), action(exit), enter(O1,T1), exit(O2,T2), T1<T2, order(before), feature(O1,_,F3): desc(1,F3); feature(O2,_,F4): desc(2,F4).
answer(no) :- not answer(yes), query(any, enter), action(exit), order(before).


answer(yes):- query(any, exit), action(enter), exit(O1,T1), enter(O2,T2), T1>T2, order(after), feature(O1,_,F3): desc(1,F3); feature(O2,_,F4): desc(2,F4).
answer(no) :- not answer(yes), query(any, exit), action(enter), order(after).

answer(yes):- query(any, exit), action(enter), exit(O1,T1), enter(O2,T2), T1<T2, order(before), feature(O1,_,F3): desc(1,F3); feature(O2,_,F4): desc(2,F4).
answer(no) :- not answer(yes), query(any, exit), action(enter), order(before).

answer(yes):- query(any, exit), action(exit), exit(O1,T1), exit(O2,T2), T1>T2, order(after), feature(O1,_,F3): desc(1,F3); feature(O2,_,F4): desc(2,F4).
answer(no) :- not answer(yes), query(any, exit), action(exit), order(after).

answer(yes):- query(any, exit), action(exit), exit(O1,T1), exit(O2,T2), T1<T2, order(before), feature(O1,_,F3): desc(1,F3); feature(O2,_,F4): desc(2,F4).
answer(no) :- not answer(yes), query(any, exit), action(exit), order(before).

% any objects that enter scene
answer(yes) :- query(any,enter), enter(O,T), not order(_), feature(O,_,F): desc(1,F).
answer(no) :- query(any,enter), not order(_), not answer(yes).

answer(yes) :- query(any,exit), exit(O,T), feature(O,_,F): desc(1,F).
answer(no) :- query(any,exit), not answer(yes).

% any objects moving/stationary

answer(yes) :- query(any,moving), moving(O,T), not when(_), not action(_), feature(O,_,F): desc(1,F).
answer(no) :- query(any,moving), not when(_), not action(_), not answer(yes).

answer(yes) :- query(any,stationary), stationary(O,_), not moving(O,_), not when(_), not action(_), feature(O,_,F): desc(1,F).
answer(no) :- query(any,stationary), not when(_), not action(_), not answer(yes).

% any collisions
answer(yes) :- collision(_,_,_), query(any,collision), not action(_), not order(_), not when(_).
answer(no) :- not answer(yes), query(any,collision), not action(_), not order(_), not when(_).


% any collisions before/after obj enters/exits

answer(yes):- collision(O1,O3,FRAME), FRAME <T, query(any, collision), action(collision), action(enter), enter(O2,T), order(before), feature(O2,_,F): desc(2,F).
answer(yes):- collision(O1,O3,FRAME), FRAME >T, query(any, collision), action(collision), action(enter), enter(O2,T), order(after), feature(O2,_,F): desc(2,F).
answer(yes):- collision(O1,O3,FRAME), FRAME <T, query(any, collision), action(collision), action(exit), exit(O2,T), order(before), feature(O2,_,F): desc(2,F).
answer(yes):- collision(O1,O3,FRAME), FRAME >T, query(any, collision), action(collision), action(exit), exit(O2,T), order(after), feature(O2,_,F): desc(2,F).

answer(no) :- not answer(yes), query(any, collision), action(_).

% =============================================================================
% how many
% =============================================================================


% how many moving when video ends 


objs(O2):- query(howMany, moving), feature(O2,_,_), when(_), feature(O2,_,F2): desc(1,F2).
objs(O2):- query(howMany, stationary), feature(O2,_,_), when(_), feature(O2,_,F2): desc(1,F2).

answer(N) :- N= #count{O2: objs(O2), moving(O2,end)}, query(howMany, moving), when(end).
answer(N):- N = #count{O2: objs(O2), stationary(O2, end)}, query(howMany, stationary), when(end).

answer(N):- N = #count{O2: objs(O2), moving(O2, begin)}, query(howMany, moving), when(begin).
answer(N):- N = #count{O2: objs(O2), stationary(O2, begin)}, query(howMany, stationary), when(begin).


% how many objs moving when obj2 enters
objs(O2):- query(howMany, moving), feature(O2,_,_), action(_), feature(O2,_,F2): desc(1,F2).
answer(N) :- N= #count{O3: objs(O3), moving(O3,T)}, query(howMany, moving), enter(O2,T), action(enter), feature(O2,_,F2): desc(2,F2).

objs(O2):- query(howMany, stationary), feature(O2,_,_), action(_), feature(O2,_,F2): desc(1,F2).
answer(N) :- N= #count{O3: objs(O3), stationary(O3,T)}, query(howMany, stationary), enter(O2,T), action(enter), feature(O2,_,F2): desc(2,F2).

objs(O2):- query(howMany, moving), feature(O2,_,_), action(_), feature(O2,_,F2): desc(1,F2).
answer(N) :- N= #count{O3: objs(O3), moving(O3,T)}, query(howMany, moving), exit(O2,T), action(exit), feature(O2,_,F2): desc(2,F2).

objs(O2):- query(howMany, stationary), feature(O2,_,_), action(_), feature(O2,_,F2): desc(1,F2).
answer(N) :- N= #count{O3: objs(O3), stationary(O3,T)}, query(howMany, stationary), exit(O2,T), action(exit), feature(O2,_,F2): desc(2,F2).


% how many objects enter/exit
objs(O2):- query(howMany, enter), feature(O2,_,_), not order(_), feature(O2,_,F2): desc(1,F2).
answer(N) :- N=#count{O2: objs(O2), enter(O2,_)}, not order(_), query(howMany, enter).


objs(O2):- query(howMany, exit), feature(O2,_,_), not order(_), feature(O2,_,F2): desc(1,F2).
answer(N) :- N=#count{O2: objs(O2), exit(O2,_)}, not order(_), query(howMany, exit).

% how many objs enter scene before obj 2 enters/exits

objs(O2):- query(howMany, enter), feature(O2,_,_), action(_), order(_), feature(O2,_,F2): desc(1,F2).
objs(O2):- query(howMany, exit), feature(O2,_,_), action(_), order(_), feature(O2,_,F2): desc(1,F2).

answer(N) :- N=#count{O3: objs(O3), enter(O3,F), F<F3}, order(before), action(enter), query(howMany, enter), enter(O2, F3), feature(O2,_,F2): desc(2,F2).

answer(N) :- N=#count{O3: objs(O3), enter(O3,F), F<F3}, order(before), action(exit),  query(howMany, enter), exit(O2, F3), feature(O2,_,F2): desc(2,F2).

answer(N) :- N=#count{O3: objs(O3), exit(O3,F), F<F3}, order(before), action(enter), query(howMany, exit), enter(O2, F3), feature(O2,_,F2): desc(2,F2).

answer(N) :- N=#count{O3: objs(O3), exit(O3,F), F<F3}, order(before), action(exit), query(howMany, exit), exit(O2, F3), feature(O2,_,F2): desc(2,F2).

answer(N) :- N=#count{O3: objs(O3), enter(O3,F), F>F3}, order(after), action(enter), query(howMany, enter), enter(O2, F3), feature(O2,_,F2): desc(2,F2).

answer(N) :- N=#count{O3: objs(O3), enter(O3,F), F>F3}, order(after), action(exit),  query(howMany, enter), exit(O2, F3), feature(O2,_,F2): desc(2,F2).

answer(N) :- N=#count{O3: objs(O3), exit(O3,F), F>F3}, order(after), action(enter), query(howMany, exit), enter(O2, F3), feature(O2,_,F2): desc(2,F2).

answer(N) :- N=#count{O3: objs(O3), exit(O3,F), F>F3}, order(after), action(exit), query(howMany, exit), exit(O2, F3), feature(O2,_,F2): desc(2,F2).





% how many collisions
answer(N/2) :- N=#count{(O1,O2,F): collision(O1,O2,F)}, query(howMany, collision), not action(_), not order(_).

%how many collisions happen after obj enters/exits

answer(N/2) :- N=#count{(O1,O3,F): collision(O1,O3,F), F<F3}, query(howMany, collision), action(enter), enter(O2,F3), order(before), feature(O2,_,F2): desc(2,F2).

answer(N/2) :- N=#count{(O1,O3,F): collision(O1,O3,F), F>F3}, query(howMany, collision), action(enter), enter(O2,F3), order(after), feature(O2,_,F2): desc(2,F2).

answer(N/2) :- N=#count{(O1,O3,F): collision(O1,O3,F), F<F3}, query(howMany, collision), action(exit), exit(O2,F3), order(before), feature(O2,_,F2): desc(2,F2).

answer(N/2) :- N=#count{(O1,O3,F): collision(O1,O3,F), F>F3}, query(howMany, collision), action(exit), exit(O2,F3), order(after), feature(O2,_,F2): desc(2,F2).


% how many moving/stationary objs
objs(O2):- query(howMany, stationary), feature(O2,_,_), not when(_), not action(_), feature(O2,_,F2): desc(1,F2).
answer(N) :- N=#count{O2: objs(O2), not moving(O2,_)}, not when(_), not action(_), query(howMany, stationary).

objs(O2):- query(howMany, moving), feature(O2,_,_), not when(_), not action(_), feature(O2,_,F2): desc(1,F2).
answer(N) :- N=#count{O2: objs(O2), moving(O2,_)}, not when(_), not action(_), query(howMany, moving).


% =============================================================================
% what
% =============================================================================

% what feature is the first object to enter/exit

answer(M):- feature(O,Attr, M), query(what, Attr), order(first),action(enter), enter(O,F), F<=F2: enter(_,F2).
answer(M):- feature(O,Attr, M), query(what, Attr), order(first),action(exit), exit(O,F), F<=F2: exit(_,F2).

% what feature is the last object to enter/exit

answer(M):- feature(O,Attr, M), query(what, Attr), order(last),action(enter), enter(O,F), F2<=F: enter(_,F2).
answer(M):- feature(O,Attr, M), query(what, Attr), order(last),action(exit), exit(O,F), F2<=F: exit(_,F2).

% what feature is the second object to enter/exit
answer(M):- feature(O2,Attr, M), query(what, Attr), order(second), action(enter), enter(O1,F1), enter(O2,F2), F1<F2,  F1<=F3: enter(_,F3); F2<=F3:enter(_,F3),F3!=F1.
answer(M):- feature(O2,Attr, M), query(what, Attr), order(second), action(exit), exit(O1,F1), exit(O2,F2), F1<F2,  F1<=F3: exit(_,F3); F2<=F3:exit(_,F3),F3!=F1.

% what is shape of object that is stationary when video begins

answer(S) :- feature(O,shape,S), stationary(O,0), query(shape,stationary,begin).

% feature of object to collide with another

answer(F2) :- query(what,Attr), feature(O2,Attr,F2), collision(O,O2,_),action(collide), not when(_), not order(_), feature(O,_,F): desc(2,F).

% feature of first object to collide with another
answer(F2) :- query(what,Attr), feature(O2,Attr,F2), collision(O,O2,T),action(collide), order(first), not when(_), T<=T2:collision(_,O,T2); feature(O,_,F): desc(2,F).

% feature of second object to collide with another
answer(F3) :- query(what,Attr), feature(O3,Attr,F3), collision(O1,O2,T1), collision(O3,O2,T2), action(collide), T1<T2, not when(_), order(second), feature(O2,_,F): desc(2,F);T1<=T: collision(_,_,T) ; T2<=T: collision(_,_,T), T!=T1.

% feature of last object to collide with another
answer(F2) :- query(what,Attr), feature(O2,Attr,F2), collision(O,O2,T),action(collide), order(last), not when(_), T>=T2:collision(_,O,T2); feature(O,_,F): desc(2,F).


% what is feature of object that is stationary/moving, when video begins/ends
answer(F2) :- query(what,Attr), feature(O2,Attr,F2), stationary(O2,T), is(stationary), when(T), feature(O2,_,F3): desc(1,F3).
answer(F2) :- query(what,Attr), feature(O2,Attr,F2), moving(O2,T), is(moving),  when(T), feature(O2,_,F3): desc(1,F3).

% what is shape of stationary/moving object when object 2 enters
answer(F3) :- query(what,Attr), is(stationary), stationary(O,T), feature(O,Attr,F3), enter(O2,T),  when(enter), feature(O,_,F): desc(1,F); feature(O2,_,F2): desc(2,F2).
answer(F3) :- query(what,Attr), is(stationary), stationary(O,T), feature(O,Attr,F3), exit(O2,T),  when(exit), feature(O,_,F): desc(1,F); feature(O2,_,F2): desc(2,F2).

answer(F3) :- query(what,Attr), is(moving), moving(O,T), feature(O,Attr,F3), enter(O2,T),  when(enter), feature(O,_,F): desc(1,F); feature(O2,_,F2): desc(2,F2).
answer(F3) :- query(what,Attr), is(moving), moving(O,T), feature(O,Attr,F3), exit(O2,T),  when(exit), feature(O,_,F): desc(1,F); feature(O2,_,F2): desc(2,F2).


% what is feature of object that is stationary/moving
answer(F2) :- query(what,Attr), feature(O2,Attr,F2), stationary(O2,T), is(stationary), not when(_), not action(_), desc(1,_), feature(O2,_,F3): desc(1,F3).
answer(F2) :- query(what,Attr), feature(O2,Attr,F2), not moving(O2,_), is(stationary), not when(_), not action(_), not desc(_,_).
answer(F2) :- query(what,Attr), feature(O2,Attr,F2), moving(O2,T), is(moving), not when(_), not action(_), desc(1,_), feature(O2,_,F3): desc(1,F3).
answer(F2) :- query(what,Attr), feature(O2,Attr,F2), not stationary(O2,_), is(moving), not when(_), not action(_), not desc(_,_).

%what feature is object that enters scene
answer(M):- feature(O,Attr, M), query(what, Attr), enter(O,F), action(enter), not when(_), not order(_).

%what feature is object that exits scene
answer(M):- feature(O,Attr, M), query(what, Attr), exit(O,F), action(exit), not when(_), not order(_).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% EXPLANATORY
%%%%%%%%%%%%%%%%%%%%%%%%%%%%

ancestor(O1,O2,(A,B)) :- collision(O1,O2,A), collision(O2,_,B), A<=B, O1!=O2.
ancestor(O1,O3,(A,C)) :- ancestor(O1,O2,(A,B)), ancestor(O2,O3,(B,C)), O1!=O3.

% we find  2 target objects to collide in choice Idx, for choices with 2 objects

target(Idx, (O1,O2)) :- choice(Idx, 2, _),
						feature(O1, _), feature(O1, F) : choice(Idx, 1, F);
						feature(O2, _), feature(O2, F) : choice(Idx, 2, F).

% we find the 1 target object to collide in choice Idx, for choices with 1 object
target(Idx, (O1)) :- choice(Idx,1,  _), not choice(Idx,2,_), feature(O1, _), feature(O1, F) : choice(Idx, 1, F).



% we find either 1 or 2 question objects, depending on the number of objects in the question
question_objects(Ans, (O1,O2)) :- question(Ans, 2, _), feature(O1, _), feature(O1, F) : question(Ans, 1, F); feature(O2, _), feature(O2, F): question(Ans, 2, F).

question_objects(Ans, (O1)) :- question(Ans, _, _), not question(Ans,2,_), feature(O1, _), feature(O1, F) : question(Ans, 1, F).

neg(yes, no; no, yes).

% Question:obj - Choice:obj
responsible(Idx):- 
   target(Idx,O1),
   question_objects(Ans,O3),
   ancestor(O1,O3,_).
% Question:obj - Choice:col
responsible(Idx):-
   target(Idx, (O1,O2)), collision(O1,O2,C),    
   question_objects(Ans,O3), 
   1{ancestor(O1,O3,(C,_)); ancestor(O2,O3,(C,_))}.
% Question:col - Choice:obj
responsible(Idx):-
   target(Idx,O1),
   question_objects(Ans,(O3,O4)), collision(O3,O4,C),
   1{ancestor(O1,O3,(_,C));ancestor(O1,O4,(_,C))}.
% Question:col - Choice:col
responsible(Idx):-
   target(Idx, (O1,O2)), collision(O1,O2,C1),
   question_objects(Ans,(O3,O4)), collision(O3,O4,C2),  
   1{ancestor(O1,O3,(C1,C2)); ancestor(O1,O4,(C1,C2));
     ancestor(O2,O3,(C1,C2)); ancestor(O2,O4,(C1,C2))}.

answer(Idx, Ans):- question(Ans,_,_), responsible(Idx).
answer(Idx, Ans2):- question(Ans,_,_), not responsible(Idx),choice(Idx,_,_), neg(Ans,Ans2).



*%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% PREDICTIVE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% if the option collision matches with any of the cfSim/2 facts such that the collision is in the set generated by the simulator, then the answer is yes (or no if the question contains a negation).
answer(Idx, Ans) :- collision(O1,O2,F), F>125, option(Idx,qobj(I1), collide, qobj(I2)), same(qobj(I1), O1),same(qobj(I2), O2), pos_result(Ans), Ans=yes:not query(negated); Ans=no: query(negated).
answer(Idx, Ans):- not answer(Idx, Ans2), option(Idx,_,_,_), pos_result(Ans), pos_result(Ans2), Ans!=Ans2, Ans=no : not query(negated); Ans=yes: query(negated).

%*
%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% COUNTERFACTUAL
%%%%%%%%%%%%%%%%%%%%%%%%%%%%

counterfact(remove, qobj(0)).

% Define removed object(s)

removed(O) :- counterfact(remove, qobj(I)), same(qobj(I), O).

cfSim(O,collision(O2,O1,F)) :- cfSim(O,collision(O1,O2,F)).

removed(O) :- counterfact(remove, qobj(I)), same(qobj(I), O).
cfSim(O,collision(O2,O1,F)) :- cfSim(O,collision(O1,O2,F)).

% if the option collision matches with any of the cfSim/2 facts such that the collision is in the set generated by the simulator, then the answer is yes (or no if the question contains a negation). 
answer(Idx, Ans) :- removed(O), cfSim(O,collision(O1,O2,F)), option(Idx,qobj(I1), collide, qobj(I2)), same(qobj(I1), O1),same(qobj(I2), O2), pos_result(Ans), Ans=yes:not query(negated); Ans=no: query(negated).
answer(Idx, Ans):- not answer(Idx, Ans2), option(Idx,_,_,_), pos_result(Ans), pos_result(Ans2), Ans!=Ans2, Ans=no : not query(negated); Ans=yes: query(negated).
*%
'''