

prompt = '''Instructions: A description of a scene of moving objects and their physical dynamics is presented. A question is then asked about hypothetical changes in the scene and their outcomes.

Description: ''' 

prompt2 = '''Instructions: A description of a scene of moving objects and their physical dynamics is presented. A question is then asked about the scene description.

Description: ''' 


prompt_additional_first_try = '''If the removed object in the question does not affect the focus object, then what happens to the focus object in the scene description will also happen in the hypothetical question. 
In this case, the removed object does not affect the focus object: '''

prompt_additional_second_try = '''If the removed object in the question does not affect the other, then the collision in the following question will happen only if it happened in the scene description. 
In this case, the removed object does not affect the focus object: '''

prompt_additional = '''If the removed object in the question does not affect the other, then the collision in the following question will happen only if it happened in the scene description. 
In this case, the removed object does not affect the other object: '''


prompt_additional2 = '''The collision/hit in the following question will happen only if it happened in the scene description: '''


