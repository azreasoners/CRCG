# Question Parser

A text-to-program semantic parser using Tensor2Tensor library   

## Environment

We used Python 3.7.9, and following libraries:

```
tensor2tensor==1.15.7
tensorflow-datasets==3.2.1
tensorflow==1.15.5
```

## Training and evaluating a model

First follow instructions in `data/` directory.

In order to train and evaluate a model, run the following:

```shell
bash run_experiment.sh
```

This will run preprocessing on the dataset and train a transformer model on the train split of the CLEVRER dataset, after which it will directly be evaluated.

Finally it generates `test_inferred.json` on current directory. We placed our sample result file on `data/questions/`.
