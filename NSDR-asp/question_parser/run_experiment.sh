#!/bin/bash -eu
# ================= Input parameters ================

# Available models: lstm_seq2seq_attention, transformer, universal_transformer.
model="transformer"

# Custom hyperparameters are defined in clevrer/clevrer.py.
hparams_set="clevrer_transformer"

# Train steps.
train_steps="35000"

# Local path to the dataset (after it has been downloaded).
dataset_local_path="../data/questions"

# Evaluation results will be written to this path.
eval_results_path="evaluation.txt"

# Tensor2tensor results will be written to this path. This includes encode/
# decode files, the vocabulary, and the trained models.
save_path="t2t_data"

# The tensor2tensor problem to use. The clevrer problem is defined in clevrer/clevrer.py.
problem="clevrer"

# Other path-related variables.
tmp_path="/tmp/clevrer_tmp"
work_dir="$(pwd)"
output_dir="${save_path}/output"
checkpoint_path="${save_path}/output/model.ckpt-${train_steps}"

# Evaluate the trained model on the validation split of the dataset.
eval_encode_path="${save_path}/validation/validation_encode.txt"
eval_decode_path="${save_path}/validation/validation_decode.txt"
eval_decode_inferred_path="${save_path}/validation/validation_decode_inferred.txt"
eval_input="${dataset_local_path}/validation.json"
eval_output="${save_path}/validation/validation_inferred.json"

# Do predictions on the test split of the dataset
test_encode_path="${save_path}/test/test_encode.txt"
test_decode_inferred_path="${save_path}/test/test_inferred.txt"
test_input="${dataset_local_path}/test.json"
test_output="${save_path}/test/test_inferred.json"

# ================= Pipeline ================
python3 -m preprocess_main --dataset_path="${dataset_local_path}" \
  --save_path="${save_path}"

t2t-datagen --t2t_usr_dir="${work_dir}/clevrer/" --data_dir="${save_path}" \
  --problem="${problem}" --tmp_dir="${tmp_path}"

t2t-trainer --t2t_usr_dir="${work_dir}/clevrer/" --data_dir="${save_path}" \
  --problem="${problem}" --model="${model}" --hparams_set="${hparams_set}" \
  --output_dir="${output_dir}" --train_steps="${train_steps}"


t2t-decoder --t2t_usr_dir="${work_dir}/clevrer/" --data_dir="${save_path}" \
  --problem="${problem}" --model="${model}" --hparams_set="${hparams_set}" \
  --output_dir="${output_dir}" \
  --checkpoint_path="${checkpoint_path}" \
  --decode_from_file="${eval_encode_path}" \
  --decode_to_file="${eval_decode_inferred_path}"

python3 -m evaluate_main --questions_path="${eval_encode_path}" \
  --golden_answers_path="${eval_decode_path}" \
  --inferred_answers_path="${eval_decode_inferred_path}" \
  --output_path="${eval_results_path}"

python3 -m postprocess \
  --inferred_path="${eval_decode_inferred_path}" \
  --input_path="${test_input}" \
  --output_path="${eval_output}"


t2t-decoder --t2t_usr_dir="${work_dir}/clevrer/" --data_dir="${save_path}" \
  --problem="${problem}" --model="${model}" --hparams_set="${hparams_set}" \
  --output_dir="${output_dir}" \
  --checkpoint_path="${checkpoint_path}" \
  --decode_from_file="${test_encode_path}" \
  --decode_to_file="${test_decode_inferred_path}"

python3 -m postprocess \
  --inferred_path="${test_decode_inferred_path}" \
  --input_path="${test_input}" \
  --output_path="${test_output}"


python3 -m validation_inferred2oe_mc \
  --inferred_output_path="${eval_output}" \
  --golden_answers_path="${eval_input}"

python3 -m test_inferred2oe_mc \
  --inferred_output_path="${test_output}" \
