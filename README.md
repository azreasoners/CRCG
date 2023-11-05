# CRCG
This is the repository to reproduce the results in the paper "Think before You Simulate: Orchestrating Symbolic Reasoning, Perception, and Simulation for Counterfactual Question Answering".

## Installation
We tested this repository on Python 3.6 in a conda environment for our experiments. Please follow the steps below to create a conda environment and install necessary packages.
```
conda create --name asp-CRCG python=3.6
conda activate asp-CRCG
conda install -c potassco clingo==5.3.0
conda install -c anaconda ipython nltk numpy
conda install -c conda-forge clyngor tqdm ipdb matplotlib
conda install pytorch
```
For the question parser to work, one also needs to download the NLTK punctuation package. Open a python shell with
```
python
```
and run the following 2 lines of code in the python shell.
```
import nltk
nltk.download('punkt')
```

## Data Preparation
Please follow the steps below to prepare data for the experiments with three baselines.
* NSDR-asp: baseline is NS-DR on CLEVRER dataset
* VRDP-asp: baseline is VRDP on CLEVRER dataset
* CRAFT-asp: baseline is GPT-3 on CRAFT dataset

### For both NSDR-asp and VRDP-asp
From https://github.com/chuangg/CLEVRER/tree/master/executor/data,
* download `train.json`, `validation.json`, and `test.json` and put them into `NSDR-asp/data/questions/` folder.


### For NSDR-asp only
From https://github.com/chuangg/CLEVRER, look for the links in the following keywords.
* "The dynamic predictions can be found here"
* "The results of video frame parser (visual masks) can be found here."

Download the files, unzip them, and place them (i.e., `propnet_preds` and `processed_proposals` folders) under `NSDR-asp/data/` folder. One may also use the following commands to download all files.
```
pip install gdown
cd NSDR-asp/data
gdown --id 1u2OdG59Zl1PqNAnXZjDVMmhXSy3czR44
gdown --id 1BJ8n1z0M7a-8yhDRX_P_50GakKXRf8uR
tar -xzf propnet_preds.tar.gz
tar -xzf processed_proposals.tar.gz
```

To run the experiments, the `NSDR-asp` directory format should match the following:
```
NSDR-asp/  
├─ data/    
│  ├─ convert.py  
│  ├─ converted/ (will be generated later)
│  ├─ processed_proposals/
│  ├─ propnet_preds/  
│  │  ├─ with_edge_supervision_old/
│  │  ├─ without_edge_supervision/
│  ├─ questions/  
│  │  ├─ train.json  
│  │  ├─ validation.json  
│  │  ├─ test.json
├─ descriptive/  
├─ explanatory/  
├─ predictive/  
├─ counterfactual/
├─ question_parser/
├─ merge.py
```

### For VRDP-asp only
From https://github.com/dingmyu/VRDP,
* download `object_dicts_with_physics.zip`, `object_simulated.zip`, and `object_updated_results.zip` files, unzip them, and place the 3 folders in the `VRDP-asp/data/` folder. One may also use the following commands to download all files.
```
cd VRDP-asp/data
gdown --id 1H41hTi_2_BOs4Vj6A5wu4eIzogfHh0C1
gdown --id 12BR4dfg3qo8F9N8rjfwP6Z4n0b4v6cQB
gdown --id 1kVEVtxMZIpaodb6R1oWw2FLyHCxH-vsr
unzip object_dicts_with_physics.zip
unzip object_simulated.zip
unzip object_updated_results.zip
```

### Format mask r-cnn results:
This will create the converted folder and populate it with IOD results.
```
cd NSDR-asp/data
python convert.py
```

### For CRAFT-asp only
From https://zenodo.org/record/4904783, download the dataset files `CRAFT.zip` and `CRAFT_Annotations.zip`, unzip them, and put `dataset_minimal.json`, `split_info_hard.json`, and `split_info_random.json` (from `CRAFT.zip`) as well as `annotations.json` (from `CRAFT_Annotations.zip`) into the `CRAFT-asp/` folder. One may also use the following commands to download all files.
```
cd CRAFT-asp
wget https://zenodo.org/record/4904783/files/CRAFT.zip
wget https://zenodo.org/record/4904783/files/CRAFT_Annotations.zip
unzip CRAFT.zip
unzip CRAFT_Annotations.zip
```
Optionally, one may remove the big files not needed for our experiments with the following commands.
```
rm -r videos
rm -r *.zip
```

## How to run the experiments
The codes and data for all experiments are available in the "NSDR-asp", "VRDP-asp", "CRAFT-asp" folders respectively. More detailed instructions are provided in the README.md file in each folder.
