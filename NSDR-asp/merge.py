import json
from tqdm import tqdm

descriptive_path = './descriptive/descriptive.json'
explanatory_path = './explanatory/explanatory.json'
predictive_path = './predictive/predictive.json'
counterfactual_path = './counterfactual/counterfactual.json'

with open(descriptive_path) as f:
    descriptive = json.load(f)
with open(explanatory_path) as f:
    explanatory = json.load(f)
with open(predictive_path) as f:
    predictive = json.load(f)
with open(counterfactual_path) as f:
    counterfactual = json.load(f)

result = []
for scene_index in tqdm(range(0, 5000)):
    merge = {
        'scene_index': 15000 + scene_index,
        'questions': [],
    }

    for query_type in (descriptive, explanatory, predictive, counterfactual):
        merge['questions'].extend(query_type[scene_index]['questions'])

    result.append(merge)

output_path = 'best.json'
with open(output_path, 'w') as f:
    json.dump(result, f)
