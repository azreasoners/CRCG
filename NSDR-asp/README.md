# Steps to re-produce NSDR related experiments

## To run descriptive, explanatory, predictive, and counterfactual queries for validation set, run the following from their respective directories.
You can also pass arguments for descriptive (--IOD, --ASP_PE), explanatory (--IOD, --ASP_PE), predictive (--IOD, --ASP_PE, --SPS), and counterfactual (--ASP_CRCG, --ASP_PE, --IOD, --SPS) queries to turn on and off certain enhancements. ASP_CRCG is to use CRCG, ASP_PE is to use the ASP symbolic executor, IOD is to use improved object detection, and SPS is to use the simple physics simulator module. --ALL will run with all enhancements. The validation set has 5,000 videos and every command below will show the progress bar on these videos.

'python run_descriptive.py'

'python run_explanatory.py --ALL'

'python run_predictive.py --ALL'

'python run_counterfactual.py --ALL'

## To run descriptive, explanatory, predictive, and counterfactual queries for test set to submit the result, run the following from their respective directories and merge the results:

'python test_descriptive.py'

'python test_explanatory.py'

'python test_predictive.py'

'python test_counterfactual.py'

'python merge.py'
