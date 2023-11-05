# ASP-CR with CRAFT

## Requirements
toolz - install with `pip install toolz`.  
openai - install with `pip install openai` (tested on version 0.20.0).  

We have provided a file which includes all GPT prompts that are used in this code. If you would like to prompt GPT yourself, then it is required that (1) the prompt cache files be deleted and (2) in `keys.py`, to put in the API and organization key from an OpenAi account. To do the experiments with GPT-4, API access is required on your OpenAi account.

## Run

To do evaluation, from this directory run:
* `python run_CRAFT.py` for only cases where CRCG determines the answer
* `python run_CRAFT_ALL.py` for all cases

Use the following flags:  
`--GPT_model` to specify the model to use (`GPT-3.5` and `GPT-4` are available).
`--ASP_CRCG` to use CRCG.  
`--ASP_CRCG_GPT` to use CRCG with GPT prompts.  
`--hard` to use the "hard split".  

Without any flags, the default is baseline GPT and the "easy" split.
