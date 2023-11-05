import os
import time
import json



all_sims_dict = json.load(open('counterfactual/all_sims_dict.json'))

for i in range(10000,15000):
    os.system("python physics_simulation_store.py {0}".format(i))

    sim_dicts = all_sims_dict[f'sim_{i:05d}.json']
    for idx,j in enumerate(sim_dicts):
        os.system("python ASP_SIM_test.py {0} {1}".format(i, idx))
    if i%50==0:
        print(f'{i}/15000')
