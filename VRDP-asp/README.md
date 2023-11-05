# Steps to re-produce VRDP related experiments

## Optional Installation:
For visualization, install taichi
```
pip install taichi
```

## How to run
The validation set has 5,000 videos and every command below will show the progress bar on these videos.

- Descriptive:
In the descriptive directory, run:
'python run_descriptive.py'
Enhancements: --IOD --ASP_PE

- Explanatory:
In the explanatory directory, run:
'python run_explanatory.py'
Enhancements: --IOD, --ASP_PE

- Predictive:
In the predictive directory, run:
'python run_predictive.py'
Enhancements: --IOD --SPS --ASP_PE

- Counterfactual:
(Optional) To generate the CRCG simulation results (Algorithm 1 in the paper), run 1 and 2 (this takes 1-2 days). This is not necessary since we provide the generated files. Otherwise you can skip to 3.
1. In the counterfactual directory, run :
'python get_sim_facts.py'
2. In the VRDP-asp directory, run:
'python run_ASP_SIM.py'
3. In the counterfactual directory, run:
'python run_counterfactual.py'
To run the best model, use the  --ALL flag, otherwise use either: --ASP_CRCG --ASP_CRCG_approx --ASP_PE or --IOD.
